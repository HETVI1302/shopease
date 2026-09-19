from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('cart/update-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/mock-verify/', views.mock_payment_verify, name='mock_payment_verify'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('invoice/<int:order_id>/', views.invoice_pdf, name='invoice_pdf'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('detail/<int:order_id>/request-return/', views.request_return, name='request_return'),
]
