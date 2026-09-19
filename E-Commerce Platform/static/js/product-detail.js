document.addEventListener('DOMContentLoaded', function() {
    const addToBagBtn = document.getElementById('addToBagBtn');
    const buyNowBtn = document.getElementById('buyNowBtn');
    const form = document.getElementById('addToCartForm');
    const actionTypeInput = document.getElementById('action_type');

    if (addToBagBtn && form) {
        addToBagBtn.addEventListener('click', function(e) {
            e.preventDefault();
            actionTypeInput.value = 'add';
            
            const formData = new FormData(form);
            
            // Add loading state
            const originalText = addToBagBtn.innerHTML;
            addToBagBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
            addToBagBtn.disabled = true;

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(async response => {
                const data = await response.json().catch(() => ({}));
                if (data.login_required || response.status === 401) {
                    alert('Please login or register to add items to your cart.');
                    window.location.href = data.redirect_url || '/accounts/login/';
                    return;
                }
                if (data.success) {
                    // Show success toast
                    showToast('Success', 'Item added to your bag!', 'success');
                    
                    // Update cart badge in navbar
                    const cartBadge = document.querySelector('.fa-cart-shopping').nextElementSibling;
                    if (cartBadge) {
                        cartBadge.textContent = data.cart_items_count;
                        cartBadge.style.display = 'inline-block';
                    } else {
                        // Create badge if it doesn't exist
                        const cartIcon = document.querySelector('.fa-cart-shopping');
                        if (cartIcon) {
                            const badge = document.createElement('span');
                            badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger border border-white';
                            badge.style.fontSize = '0.7rem';
                            badge.style.padding = '0.35em 0.5em';
                            badge.textContent = data.cart_items_count;
                            cartIcon.parentNode.appendChild(badge);
                        }
                    }
                } else {
                    showToast('Error', data.message || 'Failed to add item.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error', 'An unexpected error occurred.', 'danger');
            })
            .finally(() => {
                // Restore button
                addToBagBtn.innerHTML = originalText;
                addToBagBtn.disabled = false;
            });
        });
    }

    if (buyNowBtn && form) {
        buyNowBtn.addEventListener('click', function(e) {
            e.preventDefault();
            actionTypeInput.value = 'buy_now';
            form.submit();
        });
    }
});

// Toast notification helper
function showToast(title, message, type='success') {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1100';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    const iconClass = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2 fw-bold">
                    <i class="fa-solid ${iconClass} fs-5"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    
    // Ensure bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, {
            delay: 3000
        });
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });
    } else {
        // Fallback if bootstrap JS is not loaded
        toastElement.classList.add('show');
        setTimeout(() => {
            toastElement.classList.remove('show');
            setTimeout(() => toastElement.remove(), 300);
        }, 3000);
    }
}
