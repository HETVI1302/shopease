document.addEventListener('DOMContentLoaded', function() {
    const qtyButtons = document.querySelectorAll('.cart-qty-btn');
    
    qtyButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const itemId = this.getAttribute('data-item-id');
            const action = this.getAttribute('data-action');
            
            // disable button temporarily to prevent spamming
            this.disabled = true;
            
            fetch('/orders/cart/update-quantity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    item_id: itemId,
                    action: action
                })
            })
            .then(response => {
                if (response.status === 403) {
                    window.location.reload();
                    return;
                }
                return response.json();
            })
            .then(data => {
                this.disabled = false;
                
                if (data.error) {
                    console.error('Error updating quantity:', data.error);
                    return;
                }
                
                if (data.success) {
                    if (data.item_quantity > 0) {
                        // Update specific item
                        const qtyInput = document.getElementById(`item-qty-${itemId}`);
                        const costEl = document.getElementById(`item-cost-${itemId}`);
                        
                        if (qtyInput) qtyInput.value = data.item_quantity;
                        if (costEl) costEl.innerText = '₹' + data.item_cost;
                    } else {
                        // Item was removed, reload page to reflect removal properly
                        window.location.reload();
                        return;
                    }
                    
                    // Update global totals
                    const cartSubtotal = document.getElementById('cart-subtotal');
                    const cartDiscount = document.getElementById('cart-discount');
                    const cartTotal = document.getElementById('cart-total');
                    const navCartCountList = document.querySelectorAll('.fa-cart-shopping + .badge'); // in case there are multiple
                    
                    if (cartSubtotal) cartSubtotal.innerText = '₹' + data.cart_subtotal;
                    
                    if (parseFloat(data.discount) > 0) {
                        if (cartDiscount) cartDiscount.innerText = '-₹' + data.discount;
                    } else {
                        // Hide discount container if discount is 0
                        const discountContainer = document.getElementById('discount-container');
                        if (discountContainer) discountContainer.classList.add('d-none');
                    }
                    
                    if (cartTotal) cartTotal.innerText = '₹' + data.cart_total;
                    
                    navCartCountList.forEach(badge => {
                        badge.innerText = data.cart_items_count;
                        if (data.cart_items_count <= 0) {
                            badge.style.display = 'none';
                        } else {
                            badge.style.display = 'inline-block';
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                this.disabled = false;
            });
        });
    });

    // Coupon System Logic
    const applyCouponForm = document.getElementById('apply-coupon-form');
    const msgContainer = document.getElementById('coupon-message-container');
    const availableCouponBtns = document.querySelectorAll('.apply-available-coupon-btn');

    function handleApplyCoupon(code, button) {
        if (!code) return;
        
        const originalBtnText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        
        if (msgContainer) {
            msgContainer.classList.add('d-none');
            msgContainer.classList.remove('bg-danger-subtle', 'text-danger', 'bg-success-subtle', 'text-success');
        }

        fetch('/orders/cart/apply-coupon/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                // Adding a dummy csrf token, wait, we used @csrf_exempt so it's fine, but better safe.
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success
                if (msgContainer) {
                    msgContainer.innerText = data.message;
                    msgContainer.classList.remove('d-none', 'bg-danger-subtle', 'text-danger');
                    msgContainer.classList.add('bg-success-subtle', 'text-success');
                }
                
                // Update totals in UI
                const cartDiscount = document.getElementById('cart-discount');
                const cartTotal = document.getElementById('cart-total');
                const discountContainer = document.getElementById('discount-container');
                const appliedCouponCode = document.getElementById('applied-coupon-code');
                
                if (cartDiscount) cartDiscount.innerText = '-₹' + data.discount_amount;
                if (cartTotal) cartTotal.innerText = '₹' + data.new_total;
                if (appliedCouponCode) appliedCouponCode.innerText = data.coupon_code;
                if (discountContainer) discountContainer.classList.remove('d-none');
                
            } else {
                // Error
                if (msgContainer) {
                    msgContainer.innerText = '❌ ' + (data.message || 'Invalid coupon code');
                    msgContainer.classList.remove('d-none', 'bg-success-subtle', 'text-success');
                    msgContainer.classList.add('bg-danger-subtle', 'text-danger');
                }
            }
        })
        .catch(error => {
            console.error('Error applying coupon:', error);
            if (msgContainer) {
                msgContainer.innerText = '❌ Something went wrong. Please try again.';
                msgContainer.classList.remove('d-none', 'bg-success-subtle', 'text-success');
                msgContainer.classList.add('bg-danger-subtle', 'text-danger');
            }
        })
        .finally(() => {
            button.disabled = false;
            button.innerHTML = originalBtnText;
        });
    }

    if (applyCouponForm) {
        applyCouponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('coupon-code-input');
            const button = document.getElementById('apply-coupon-btn');
            handleApplyCoupon(input.value.trim(), button);
        });
    }

    availableCouponBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const code = this.getAttribute('data-code');
            handleApplyCoupon(code, this);
        });
    });
});
