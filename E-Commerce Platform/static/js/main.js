document.addEventListener('DOMContentLoaded', () => {
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Global Quick Add to Bag Handler with strict login check
    document.querySelectorAll('.quick-add-to-cart, .btn-add-to-cart, [data-add-to-cart]').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url') || this.getAttribute('href');
            if (!url) return;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken') || ''
                    }
                });
                const data = await response.json().catch(() => ({}));

                if (data.login_required || response.status === 401) {
                    alert('Please login or register to add items to your cart.');
                    window.location.href = data.redirect_url || '/accounts/login/';
                    return;
                }

                if (data.success) {
                    window.location.reload();
                }
            } catch (err) {
                console.error('Add to cart error:', err);
            }
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
