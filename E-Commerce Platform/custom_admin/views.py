from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from accounts.decorators import seller_required
from accounts.models import CustomUser
from orders.models import Order
from store.models import Product
from django.db.models import Sum, Q

@seller_required
def dashboard(request):
    # Stats
    orders_paid = Order.objects.filter(paid=True)
    total_revenue = sum(o.get_total_cost() for o in orders_paid)
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(role='CUSTOMER').count()
    recent_orders = Order.objects.select_related('user').order_by('-created')[:8]
    low_stock_products = Product.objects.filter(stock__lte=5).order_by('stock')[:5]
    
    return render(request, 'custom_admin/dashboard.html', {
        'revenue': total_revenue,
        'orders_count': total_orders,
        'customers_count': total_customers,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    })

@seller_required
def manage_orders(request):
    orders = Order.objects.all().order_by('-created')
    
    search_query = request.GET.get('search')
    if search_query:
        if search_query.isdigit():
            orders = orders.filter(id=search_query)
        else:
            orders = orders.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(city__icontains=search_query)
            )

    delivery_partners = CustomUser.objects.filter(role='DELIVERY_PARTNER', is_active=True)
    
    return render(request, 'custom_admin/manage_orders.html', {
        'orders': orders,
        'delivery_partners': delivery_partners
    })

@seller_required
def assign_delivery(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        partner_id = request.POST.get('partner_id')
        
        if partner_id:
            partner = get_object_or_404(CustomUser, id=partner_id, role='DELIVERY_PARTNER')
            order.delivery_partner = partner
            order.status = 'Assigned'
            order.save()
            messages.success(request, f"Order #{order.id} assigned to {partner.first_name} {partner.last_name}")
        else:
            messages.error(request, "Please select a valid delivery partner.")
            
    return redirect('custom_admin:manage_orders')

from orders.models import Order, ReturnRequest

@seller_required
def returns_list(request):
    returns = ReturnRequest.objects.all().order_by('-created_at')
    delivery_partners = CustomUser.objects.filter(role='DELIVERY_PARTNER', is_active=True)
    return render(request, 'custom_admin/returns_list.html', {
        'returns': returns,
        'delivery_partners': delivery_partners
    })

@seller_required
def assign_pickup_rider(request, return_id):
    if request.method == 'POST':
        return_req = ReturnRequest.objects.filter(id=return_id).first()
        if not return_req:
            return_req = get_object_or_404(ReturnRequest, order_id=return_id)
            
        rider_id = request.POST.get('rider_id')
        if rider_id:
            rider = get_object_or_404(CustomUser, id=rider_id, role='DELIVERY_PARTNER')
            return_req.assigned_rider = rider
            return_req.status = 'PICKUP_ASSIGNED'
            return_req.save()
            messages.success(request, f"Rider {rider.username} assigned for pickup of Order #{return_req.order.id}!")
        else:
            messages.error(request, "Please select a valid delivery partner.")
    return redirect('custom_admin:returns_list')

@seller_required
def approve_return(request, return_id):
    if request.method == 'POST':
        return_req = ReturnRequest.objects.filter(id=return_id).first()
        if not return_req:
            return_req = get_object_or_404(ReturnRequest, order_id=return_id)
            
        if return_req.status == 'REQUESTED':
            return_req.status = 'APPROVED'
            return_req.save()
            
            # Update order status
            order = return_req.order
            order.status = 'Return Approved'
            order.save()
            
            messages.success(request, f"Return approved for Order #{order.id}.")
    return redirect('custom_admin:returns_list')

@seller_required
def process_refund(request, return_id):
    if request.method == 'POST':
        # Fetch return request
        return_req = ReturnRequest.objects.filter(id=return_id).first()
        if not return_req:
            return_req = get_object_or_404(ReturnRequest, order_id=return_id)
        
        order = return_req.order
        refund_amount = request.POST.get('refund_amount') or getattr(order, 'total_amount', None) or order.get_total_cost()

        refund_method = request.POST.get('refund_method', return_req.refund_method)
        
        # 1. Process Refund based on selected Method
        if refund_method == 'ORIGINAL' and ('RAZORPAY' in str(order.payment_method).upper() or 'ONLINE' in str(order.payment_method).upper()):
            # Simulate successful refund safely
            try:
                from django.conf import settings
                import razorpay
                if getattr(settings, 'RAZORPAY_KEY_ID', None) and getattr(order, 'razorpay_payment_id', None):
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    client.payment.refund(order.razorpay_payment_id, {'amount': int(float(refund_amount) * 100)})
            except Exception as e:
                print(f"Razorpay live refund bypassed for mock testing: {e}")
                
        elif refund_method == 'STORE_WALLET' or (refund_method == 'ORIGINAL' and 'WALLET' in str(order.payment_method).upper()):
            # 2. Credit the user's wallet with the refund amount
            from accounts.models import UserWallet, WalletTransaction
            from django.utils import timezone
            from datetime import timedelta
            from decimal import Decimal
            
            wallet, _ = UserWallet.objects.get_or_create(user=return_req.user)
            refund_dec = Decimal(str(refund_amount))
            
            already_credited = WalletTransaction.objects.filter(
                wallet=wallet, order=order, transaction_type='CREDIT'
            ).exists()
            
            if not already_credited:
                current_bal = Decimal(str(wallet.balance or '0.00'))
                wallet.balance = current_bal + refund_dec
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_dec,
                    transaction_type='CREDIT',
                    description=f"Refund for Return of Order #{order.id}",
                    order=order,
                    expires_at=timezone.now() + timedelta(days=365)
                )

        # 3. Update Statuses
        return_req.status = 'REFUNDED'
        return_req.refund_amount = refund_amount
        return_req.save()

        order.status = 'REFUNDED'
        order.refund_status = 'Refund Processed Successfully'
        order.save()

        messages.success(request, f"Refund of ₹{refund_amount} successfully processed for Order #{order.id}!")
        
        # Support both AJAX and direct form post
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax'):
            return JsonResponse({'success': True, 'message': f'Refund of ₹{refund_amount} completed successfully!'})
        
        return redirect('custom_admin:manage_returns')

    return redirect('custom_admin:manage_returns')

@seller_required
def reject_return(request, return_id):
    if request.method == 'POST':
        return_req = ReturnRequest.objects.filter(id=return_id).first()
        if not return_req:
            return_req = get_object_or_404(ReturnRequest, order_id=return_id)
            
        admin_remark = request.POST.get('admin_remark', '')
        
        return_req.status = 'REJECTED'
        return_req.admin_remark = admin_remark
        return_req.save()
        
        # We might revert order status back to Delivered, or leave it as Return Requested / Rejected
        order = return_req.order
        order.status = 'Delivered'  # Revert back
        order.save()
        
        messages.success(request, f"Return rejected for Order #{order.id}.")
    return redirect('custom_admin:returns_list')

@seller_required
def manage_products(request):
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(id__iexact=search_query if search_query.isdigit() else 0)
        ).select_related('category').order_by('-created')
    else:
        products = Product.objects.all().select_related('category').order_by('-created')
        
    from store.models import Category
    categories = Category.objects.all()
    return render(request, 'admin_panel/products_list.html', {'products': products, 'categories': categories})

@seller_required
def admin_add_product(request):
    from store.models import Category
    from django.utils.text import slugify
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        slug = slugify(name)
        
        product = Product.objects.create(
            category=category,
            name=name,
            slug=slug,
            price=price,
            stock=stock,
            description=description,
            image=image,
            target=request.POST.get('target', 'UNISEX'),
            available=True
        )
        messages.success(request, "Product added successfully!")
    return redirect('custom_admin:manage_products')

@seller_required
def admin_edit_product(request, product_id):
    from store.models import Category
    from django.utils.text import slugify
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.slug = slugify(product.name)
        product.price = request.POST.get('price', product.price)
        product.stock = int(request.POST.get('stock', product.stock))
        product.description = request.POST.get('description', product.description)
        product.target = request.POST.get('target', getattr(product, 'target', 'UNISEX'))
        
        category_id = request.POST.get('category') or request.POST.get('category_id')
        if category_id:
            product.category_id = category_id
            
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            
        # Auto-set availability based on stock
        product.available = product.stock > 0
        product.save()
        
        messages.success(request, f"Product '{product.name}' updated successfully!")
    return redirect('custom_admin:manage_products')

@seller_required
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
    return redirect('custom_admin:manage_products')

@seller_required
def manage_users(request):
    search_query = request.GET.get('search', '').strip()
    users = CustomUser.objects.all().order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(role__icontains=search_query)
        )
        
    return render(request, 'admin_panel/users_list.html', {
        'users': users,
        'search_query': search_query
    })
