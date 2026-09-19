document.addEventListener("DOMContentLoaded", function() {
    const urlsElem = document.getElementById("checkout-urls");
    if (!urlsElem) return; // not on checkout page

    const removeCouponUrl = urlsElem.dataset.removeCoupon;
    const checkoutUrl = urlsElem.dataset.checkout;
    const verifyUrl = urlsElem.dataset.verify;
    const mockVerifyUrl = urlsElem.dataset.mockVerify;
    const csrfToken = urlsElem.dataset.csrf;

    // Remove Coupon Logic
    const removeCouponBtn = document.getElementById("remove-coupon-btn");
    if (removeCouponBtn) {
        removeCouponBtn.addEventListener("click", function() {
            const originalContent = removeCouponBtn.innerHTML;
            removeCouponBtn.disabled = true;
            removeCouponBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            
            fetch(removeCouponUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("cart-subtotal").innerText = "₹" + data.subtotal;
                    document.getElementById("cart-total").innerText = "₹" + data.total;
                    document.getElementById("discount-container").classList.add("d-none");
                }
            })
            .catch(error => console.error("Error removing coupon:", error))
            .finally(() => {
                removeCouponBtn.disabled = false;
                removeCouponBtn.innerHTML = originalContent;
            });
        });
    }

    // Checkout form logic
    let isSubmitting = false;
    const checkoutForm = document.getElementById('checkoutForm');
    const submitBtn = document.getElementById('place-order-btn') || document.querySelector('button[type="submit"]');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');

    if (checkoutForm) {
        if (submitBtn) {
            submitBtn.removeAttribute('onclick');
        }

        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (isSubmitting) {
                return false; // Strictly block duplicate requests
            }
            
            isSubmitting = true;
            
            // Disable button to prevent duplicate submissions
            if (submitBtn) submitBtn.disabled = true;
            if (btnText) btnText.innerText = "Processing...";
            if (btnSpinner) btnSpinner.classList.remove('d-none');

            const formData = new FormData(checkoutForm);
            
            fetch(checkoutUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.is_free_order || data.redirect_url) {
                        if (btnText) btnText.innerHTML = '<i class="fa-solid fa-check"></i> Success!';
                        if (btnSpinner) btnSpinner.classList.add('d-none');
                        window.location.href = data.redirect_url;
                    } else if (data.payment_method === 'Razorpay') {
                        var options = {
                            "key": data.razorpay_merchant_key,
                            "amount": data.razorpay_amount,
                            "currency": data.currency,
                            "name": "ShopEase",
                            "description": "Order Payment",
                            "order_id": data.razorpay_order_id,
                            "handler": function (response){
                                // Post to verify URL
                                submitFormTo(verifyUrl, {
                                    'csrfmiddlewaretoken': csrfToken,
                                    'razorpay_payment_id': response.razorpay_payment_id,
                                    'razorpay_order_id': response.razorpay_order_id,
                                    'razorpay_signature': response.razorpay_signature
                                });
                            },
                            "modal": {
                                "ondismiss": function(){
                                    isSubmitting = false;
                                    if (submitBtn) submitBtn.disabled = false;
                                    if (btnText) btnText.innerText = "Place Order & Pay";
                                    if (btnSpinner) btnSpinner.classList.add('d-none');
                                }
                            }
                        };
                        var rzp1 = new Razorpay(options);
                        rzp1.open();
                    } else if (data.payment_method === 'Mock') {
                        // Open Mock Payment Modal
                        const mockModal = new bootstrap.Modal(document.getElementById('mockPaymentModal'));
                        
                        document.getElementById('mock-order-id').value = data.order_id;
                        const finalPayable = (data.amount / 100).toFixed(2);
                        document.getElementById('mock-amount').innerText = finalPayable;
                        
                        // Dynamically update QR code with actual discounted amount (after coupon and wallet deduction)
                        const qrImg = document.getElementById('mock-qr-image');
                        if (qrImg) {
                            const upiPayload = `upi://pay?pa=shopease@upi&pn=ShopEase Store&am=${finalPayable}&cu=INR`;
                            qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(upiPayload)}`;
                        }
                        
                        mockModal.show();
                        
                        document.getElementById('mockPaymentModal').addEventListener('hidden.bs.modal', function () {
                            // Reset button if modal closed
                            isSubmitting = false;
                            if (submitBtn) submitBtn.disabled = false;
                            if (btnText) btnText.innerText = "Place Order & Pay";
                            if (btnSpinner) btnSpinner.classList.add('d-none');
                        });
                    }
                } else {
                    alert(data.message || data.error || 'Error processing order');
                    isSubmitting = false;
                    if (submitBtn) submitBtn.disabled = false;
                    if (btnText) btnText.innerText = "Place Order & Pay";
                    if (btnSpinner) btnSpinner.classList.add('d-none');
                }
            })
            .catch(error => {
                console.error('Checkout error:', error);
                alert("Something went wrong. Please try again.");
                isSubmitting = false;
                if (submitBtn) submitBtn.disabled = false;
                if (btnText) btnText.innerText = "Place Order & Pay";
                if (btnSpinner) btnSpinner.classList.add('d-none');
            });
        });
    }

    // Handle Mock Payment Confirm for sleek UI
    const mockPayTriggers = document.querySelectorAll('#simulateUpiSuccessBtn, #payNowCardBtn');
    if (mockPayTriggers.length > 0) {
        mockPayTriggers.forEach(btn => {
            btn.addEventListener('click', function() {
                const orderId = document.getElementById('mock-order-id').value;
                const originalHtml = btn.innerHTML;
                
                // Disable all triggers
                mockPayTriggers.forEach(b => b.disabled = true);
                
                // Show spinner
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing Securely...';
                
                // Fake delay 1.5s
                setTimeout(() => {
                    submitFormTo(mockVerifyUrl, {
                        'csrfmiddlewaretoken': csrfToken,
                        'order_id': orderId
                    });
                }, 1500);
            });
        });
    }

    function submitFormTo(url, dataObj) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        
        for (const [key, value] of Object.entries(dataObj)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            form.appendChild(input);
        }

        document.body.appendChild(form);
        form.submit();
    }
});
