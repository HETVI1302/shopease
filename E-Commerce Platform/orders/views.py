from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .models import Cart, CartItem, Order, OrderItem, Coupon
from store.models import Product, ProductVariant
from .invoice_generator import render_to_pdf
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
import razorpay
import json

# Init Razorpay Client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def get_user_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge any session cart items into the user's DB cart
        session_cart_id = request.session.get('cart_id')
        if session_cart_id:
            session_cart = Cart.objects.filter(id=session_cart_id).first()
            if session_cart and session_cart != cart:
                for item in session_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
                del request.session['cart_id']
        return cart
    else:
        cart_id = request.session.get('cart_id')
        cart = Cart.objects.filter(id=cart_id).first() if cart_id else None
        if not cart:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
        return cart

def cart_add(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'login_required': True,
                'redirect_url': f'/accounts/login/?next={request.META.get("HTTP_REFERER", "/")}',
                'message': 'Please login or register to add products to your cart.'
            }, status=401)
        return redirect('accounts:login')

    product = get_object_or_404(Product, id=product_id)
    cart = get_user_cart(request)
    
    # Simple form reading for variants and quantity
    variant_id = request.POST.get('variant')
    quantity = int(request.POST.get('quantity', 1))
    
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        variant=variant,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_items_count': sum(i.quantity for i in cart.items.all())
        })
        
    action_type = request.POST.get('action_type', 'add')
    if action_type == 'buy_now':
        return redirect('orders:checkout')
        
    return redirect('orders:cart_detail')

def cart_remove(request, item_id):
    cart = get_user_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('orders:cart_detail')

@csrf_exempt
def update_cart_quantity(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            action = data.get('action') # 'increase' or 'decrease'
            
            cart = get_user_cart(request)
            item = get_object_or_404(CartItem, id=item_id, cart=cart)
            
            max_stock = item.variant.stock if item.variant else item.product.stock
            
            if action == 'increase':
                if item.quantity < max_stock:
                    item.quantity += 1
                    item.save()
            elif action == 'decrease':
                if item.quantity > 1:
                    item.quantity -= 1
                    item.save()
                else:
                    item.delete()
                    
            # Recalculate totals
            cart_subtotal = sum(i.get_cost() for i in cart.items.all())
            discount = 0
            if cart.coupon:
                discount = (cart.coupon.discount / 100) * cart_subtotal
            cart_total = cart_subtotal - discount
            
            cart_items_count = sum(i.quantity for i in cart.items.all())
            
            return JsonResponse({
                'success': True,
                'item_quantity': item.quantity if item.id else 0, # might be deleted
                'item_cost': str(item.get_cost()) if item.id else "0",
                'cart_subtotal': str(cart_subtotal),
                'discount': str(discount),
                'cart_total': str(cart_total),
                'cart_items_count': cart_items_count
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
        except:
            code = request.POST.get('code')
            
        if not code:
            return JsonResponse({'success': False, 'message': 'Coupon code is required.'})
            
        cart = get_user_cart(request)
        try:
            coupon = Coupon.objects.get(code__iexact=code, active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
            if cart.get_total_price >= coupon.min_order_amount:
                cart.coupon = coupon
                cart.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon applied successfully!',
                    'discount_amount': str(cart.get_discount),
                    'new_total': str(cart.get_total_price_after_discount),
                    'coupon_code': coupon.code
                })
            else:
                cart.coupon = None
                cart.save()
                return JsonResponse({
                    'success': False, 
                    'message': f"Minimum cart value of ₹{coupon.min_order_amount} required."
                })
        except Coupon.DoesNotExist:
            cart.coupon = None
            cart.save()
            return JsonResponse({
                'success': False, 
                'message': 'Invalid or expired coupon code. Please check and try again.'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@csrf_exempt
def remove_coupon(request):
    if request.method == 'POST':
        cart = get_user_cart(request)
        cart.coupon = None
        cart.save()
        return JsonResponse({
            'success': True,
            'subtotal': cart.get_total_price,
            'discount': 0,
            'total': cart.get_total_price_after_discount
        })
    return JsonResponse({'success': False}, status=400)

@login_required(login_url='accounts:login')
def cart_detail(request):
    cart = get_user_cart(request)
    active_coupons = Coupon.objects.filter(active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
    return render(request, 'cart.html', {
        'cart': cart,
        'active_coupons': active_coupons
    })

def get_active_cart_items(request):
    """
    Finds active cart items across all possible cart instances for the current user/session.
    """
    # 1. Direct query: Find any CartItems belonging to carts owned by this user
    if request.user.is_authenticated:
        items = CartItem.objects.filter(cart__user=request.user).select_related('product')
        if items.exists():
            return items

        # In case CartItem is directly linked to user (if user field exists on CartItem)
        if hasattr(CartItem, 'user'):
            items = CartItem.objects.filter(user=request.user).select_related('product')
            if items.exists():
                return items

        # Check all carts for this user from newest to oldest
        user_carts = Cart.objects.filter(user=request.user).order_by('-id')
        for c in user_carts:
            c_items = getattr(c, 'items', None) or getattr(c, 'cartitem_set', None)
            if c_items and c_items.exists():
                return c_items.all()

    # 2. Session Cart Check
    session_cart_id = request.session.get('cart_id')
    if session_cart_id:
        items = CartItem.objects.filter(cart_id=session_cart_id).select_related('product')
        if items.exists():
            return items

    if request.session.session_key:
        items = CartItem.objects.filter(cart__session_id=request.session.session_key).select_related('product')
        if items.exists():
            return items

    return CartItem.objects.none()

@login_required
def checkout(request):
    cart = get_user_cart(request)
    active_items = get_active_cart_items(request)
    
    # Consolidate all found active items into the main cart to prevent any mismatch
    if active_items and active_items.exists():
        for item in active_items:
            if item.cart_id != cart.id:
                existing = cart.items.filter(product=item.product, variant=item.variant).first()
                if existing and existing.id != item.id:
                    existing.quantity += item.quantity
                    existing.save()
                    item.delete()
                else:
                    item.cart = cart
                    item.save()
                    
    if request.method == 'POST':
        # Check if cart is empty to prevent empty orders
        if not cart.items.exists():
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'})
            
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        shipping_phone = request.POST.get('phone_number')
        address = request.POST.get('address')
        postal_code = request.POST.get('postal_code')
        city = request.POST.get('city')
        payment_method = request.POST.get('payment_method', 'Razorpay')
        apply_wallet = request.POST.get('apply_wallet') == 'true'
        
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    shipping_phone=shipping_phone,
                    address=address,
                    postal_code=postal_code,
                    city=city,
                    payment_method=payment_method,
                    coupon=cart.coupon,
                    discount_amount=cart.get_discount
                )
                
                # Move items
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        price=item.get_cost() / item.quantity,
                        quantity=item.quantity
                    )
                
                # Pre-calculate cart total before cart deletion
                cart_total = cart.get_total_price_after_discount
                
                # Handle Wallet Deduction
                if apply_wallet and hasattr(request.user, 'wallet') and request.user.wallet.balance > 0:
                    from decimal import Decimal
                    wallet = request.user.wallet
                    wallet_used = min(Decimal(str(cart_total)), wallet.balance)
                    
                    if wallet_used > 0:
                        wallet.balance -= wallet_used
                        wallet.save()
                        
                        order.wallet_discount = wallet_used
                        order.save()
                        
                        from accounts.models import WalletTransaction
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            amount=wallet_used,
                            transaction_type='DEBIT',
                            description=f"Payment for Order #{order.id}",
                            order=order
                        )

                # Empty cart now that calculations are done
                cart.delete()

                # Pre-calculate amount to pass to context/Razorpay
                amount = int(order.get_total_cost() * 100) # Razorpay expects paisa
                currency = 'INR'

                if amount == 0:
                    order.paid = True
                    order.payment_method = 'WALLET'
                    order.status = 'Placed'
                    order.save()
                    
                    # Deduct stock
                    for item in order.items.all():
                        if item.variant:
                            if item.variant.stock >= item.quantity:
                                item.variant.stock -= item.quantity
                                item.variant.save()
                        else:
                            if item.product.stock >= item.quantity:
                                item.product.stock -= item.quantity
                                item.product.save()
                                
                    return JsonResponse({
                        'success': True,
                        'is_free_order': True,
                        'order_id': order.id,
                        'redirect_url': f'/orders/detail/{order.id}/',
                        'message': 'Order placed successfully using Wallet!'
                    })

                # Handle Payment
                if payment_method == 'Razorpay':
                    if razorpay_client:
                        try:
                            razorpay_order = razorpay_client.order.create({
                                "amount": amount,
                                "currency": currency,
                                "payment_capture": "1"
                            })
                            order.razorpay_order_id = razorpay_order['id']
                            order.save()
                            
                            return JsonResponse({
                                'success': True,
                                'payment_method': 'Razorpay',
                                'razorpay_order_id': order.razorpay_order_id,
                                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                                'razorpay_amount': amount,
                                'currency': currency
                            })
                        except Exception as e:
                            # Fallback if razorpay creation fails
                            return JsonResponse({
                                'success': True,
                                'payment_method': 'Mock',
                                'order_id': order.id,
                                'amount': amount
                            })
                    else:
                        # Fallback if razorpay keys are missing
                        return JsonResponse({
                            'success': True,
                            'payment_method': 'Mock',
                            'order_id': order.id,
                            'amount': amount
                        })
                    
                elif payment_method == 'COD':
                    return JsonResponse({
                        'success': True,
                        'is_free_order': False,
                        'order_id': order.id,
                        'redirect_url': f'/orders/detail/{order.id}/',
                        'message': 'COD Order placed successfully!'
                    })
                    
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    if not cart.items.exists():
        return redirect('orders:cart_detail')
    return render(request, 'checkout.html', {'cart': cart})

@csrf_exempt
def payment_verify(request):
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        
        order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Deduct stock for all items
            for item in order.items.all():
                product = item.product
                variant = item.variant
                
                if variant:
                    if variant.stock >= item.quantity:
                        variant.stock -= item.quantity
                        variant.save()
                else:
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
            
            order.paid = True
            order.payment_method = 'Online (Razorpay)'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()
            
            return redirect('orders:order_success', order_id=order.id)
        except Exception as e:
            return HttpResponse(f"Payment Verification Failed: {e}", status=400)
            
    return HttpResponse("Invalid request", status=400)

@csrf_exempt
def mock_payment_verify(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        
        # Deduct stock for all items
        for item in order.items.all():
            product = item.product
            variant = item.variant
            
            if variant:
                if variant.stock >= item.quantity:
                    variant.stock -= item.quantity
                    variant.save()
            else:
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                    
        order.paid = True
        order.status = 'Placed'
        order.payment_method = 'Online (Mock Razorpay)'
        order.save()
        
        return redirect('orders:order_success', order_id=order.id)
    return HttpResponse("Invalid request", status=400)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})

@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render_to_pdf(order)

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'customer_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return_req = order.return_requests.last()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'return_req': return_req,
        'return_request': return_req
    })

from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import ReturnRequest

@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order is delivered and within 7 days
    is_delivered = order.status == 'Delivered'
    is_within_7_days = False
    if is_delivered and order.updated:
        # Assuming updated field reflects when status was set to Delivered
        is_within_7_days = timezone.now() <= order.updated + timedelta(days=7)

    if request.method == 'POST':
        if not (is_delivered and is_within_7_days):
            messages.error(request, "This order is not eligible for a return.")
            return redirect('orders:my_orders')

        if hasattr(order, 'return_requests') and order.return_requests.exists():
            messages.error(request, "A return request already exists for this order.")
            return redirect('orders:my_orders')

        reason = request.POST.get('reason')
        additional_notes = request.POST.get('additional_notes')
        refund_method = request.POST.get('refund_method', 'ORIGINAL')
        upi_id = request.POST.get('upi_id', '')

        ReturnRequest.objects.create(
            order=order,
            user=request.user,
            reason=reason,
            additional_notes=additional_notes,
            refund_method=refund_method,
            upi_id=upi_id,
            status='REQUESTED',
            refund_amount=order.get_total_cost() # Initial fallback, admin can adjust
        )

        order.status = 'Return Requested'
        order.save()
        
        messages.success(request, "Your return request has been submitted successfully.")
        return redirect('orders:my_orders')
        
    return render(request, 'orders/return_request.html', {
        'order': order,
        'is_eligible': is_delivered and is_within_7_days
    })
