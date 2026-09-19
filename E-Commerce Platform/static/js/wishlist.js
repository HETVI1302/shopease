document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.wishlist-toggle-btn');
    const navWishlistCount = document.getElementById('nav-wishlist-count');

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.getAttribute('data-product-id');
            const removeOnly = this.getAttribute('data-remove-only') === 'true';
            
            fetch(`/wishlist/toggle/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.status === 403) {
                    window.location.href = '/accounts/login/';
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Error toggling wishlist:', data.error);
                    return;
                }

                // Update icon visually
                const icon = this.querySelector('i');
                if (data.status === 'added') {
                    icon.classList.remove('fa-regular', 'text-muted');
                    icon.classList.add('fa-solid', 'text-danger');
                    updateNavCount(1);
                } else if (data.status === 'removed') {
                    if (removeOnly) {
                        // We are on the wishlist page, so remove the whole card
                        const card = document.getElementById(`wishlist-item-${productId}`);
                        if (card) {
                            card.style.opacity = '0';
                            setTimeout(() => card.remove(), 300);
                        }
                    } else {
                        // Just on a product card, toggle the icon back
                        icon.classList.remove('fa-solid', 'text-danger');
                        icon.classList.add('fa-regular', 'text-muted');
                    }
                    updateNavCount(-1);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    function updateNavCount(change) {
        if (!navWishlistCount) return;
        
        let currentCount = parseInt(navWishlistCount.innerText || '0');
        currentCount += change;
        
        if (currentCount > 0) {
            navWishlistCount.innerText = currentCount;
            navWishlistCount.style.display = 'inline-block';
        } else {
            navWishlistCount.innerText = '0';
            navWishlistCount.style.display = 'none';
        }
    }
});
