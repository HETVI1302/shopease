from .models import Category
from orders.models import Cart

def global_categories(request):
    return {
        'global_categories': Category.objects.all()
    }

def cart_items_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            pass
    else:
        session_id = request.session.session_key
        if session_id:
            try:
                cart = Cart.objects.get(session_id=session_id)
                count = sum(item.quantity for item in cart.items.all())
            except Cart.DoesNotExist:
                pass
    return {'cart_items_count': count}

def wishlist_data(request):
    wishlist_count = 0
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_items = request.user.wishlist.all()
        wishlist_count = wishlist_items.count()
        wishlist_product_ids = list(wishlist_items.values_list('product_id', flat=True))
    return {
        'wishlist_count': wishlist_count,
        'wishlist_product_ids': wishlist_product_ids
    }
