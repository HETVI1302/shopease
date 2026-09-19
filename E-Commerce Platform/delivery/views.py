from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import delivery_required
from orders.models import Order
from django.utils import timezone

@delivery_required
def dashboard(request):
    # Active deliveries assigned to this partner (not delivered or cancelled)
    active_deliveries_raw = Order.objects.filter(
        delivery_partner=request.user,
        status__in=['Assigned', 'Picked Up', 'Out for Delivery']
    ).order_by('created')
    
    # Add mock scheduled time (created + 2 days, 5:00 PM)
    active_deliveries = []
    for order in active_deliveries_raw:
        scheduled = order.created + timezone.timedelta(days=2)
        scheduled = scheduled.replace(hour=17, minute=0, second=0)
        order.scheduled_time = scheduled
        active_deliveries.append(order)
    
    # Completed deliveries
    completed_deliveries = Order.objects.filter(
        delivery_partner=request.user,
        status__in=['Delivered', 'Refunded']
    ).order_by('-updated')[:20] # Show last 20

    # Return Pickups
    from orders.models import ReturnRequest
    return_pickups = ReturnRequest.objects.filter(
        assigned_rider=request.user,
        status='PICKUP_ASSIGNED'
    ).order_by('created_at')
    
    completed_pickups = ReturnRequest.objects.filter(
        assigned_rider=request.user,
        status__in=['PICKED_UP', 'REFUNDED', 'REJECTED']
    ).order_by('-updated_at')[:20]

    return render(request, 'delivery/dashboard.html', {
        'active_deliveries': active_deliveries,
        'completed_deliveries': completed_deliveries,
        'return_pickups': return_pickups,
        'completed_pickups': completed_pickups
    })

@delivery_required
def update_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, delivery_partner=request.user)
        new_status = request.POST.get('status')
        
        valid_statuses = ['Picked Up', 'Out for Delivery', 'Delivered']
        if new_status in valid_statuses:
            order.status = new_status
            if new_status == 'Delivered' and order.payment_method == 'COD':
                order.paid = True # Mark as paid when delivered for COD
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}")
        else:
            messages.error(request, "Invalid status update.")
            
    return redirect('delivery:dashboard')

@delivery_required
def confirm_pickup(request, return_id):
    if request.method == 'POST':
        from orders.models import ReturnRequest
        return_req = get_object_or_404(ReturnRequest, id=return_id, assigned_rider=request.user)
        
        if return_req.status == 'PICKUP_ASSIGNED':
            return_req.status = 'PICKED_UP'
            
            # Optionally update order status
            order = return_req.order
            order.status = 'PICKED_UP'
            
            if return_req.refund_method == 'STORE_WALLET':
                from accounts.models import UserWallet, WalletTransaction
                from django.utils import timezone
                from datetime import timedelta
                from decimal import Decimal

                wallet, _ = UserWallet.objects.get_or_create(user=return_req.user)
                refund_amt = return_req.refund_amount if return_req.refund_amount > 0 else return_req.order.get_total_cost()
                refund_dec = Decimal(str(refund_amt))
                
                already_credited = WalletTransaction.objects.filter(
                    wallet=wallet,
                    order=return_req.order,
                    transaction_type='CREDIT'
                ).exists()

                if not already_credited:
                    current_bal = Decimal(str(wallet.balance or '0.00'))
                    wallet.balance = current_bal + refund_dec
                    wallet.save()

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_dec,
                        transaction_type='CREDIT',
                        description=f"Refund for Return of Order #{return_req.order.id}",
                        order=return_req.order,
                        expires_at=timezone.now() + timedelta(days=365)
                    )
                return_req.status = 'REFUNDED'
                order.status = 'REFUNDED'
            
            return_req.save()
            order.save()
            
            messages.success(request, f"Pickup confirmed for Return #{return_req.id}")
            
    return redirect('delivery:dashboard')
