from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.manage_orders, name='manage_orders'),
    path('orders/assign/<int:order_id>/', views.assign_delivery, name='assign_delivery'),
    path('returns/', views.returns_list, name='returns_list'),
    path('returns/manage/', views.returns_list, name='manage_returns'),
    path('returns/assign-rider/<int:return_id>/', views.assign_pickup_rider, name='assign_pickup_rider'),
    path('returns/approve/<int:return_id>/', views.approve_return, name='approve_return'),
    path('returns/refund/<int:return_id>/', views.process_refund, name='process_refund'),
    path('returns/reject/<int:return_id>/', views.reject_return, name='reject_return'),
    path('products/', views.manage_products, name='manage_products'),
    path('products/add/', views.admin_add_product, name='admin_add_product'),
    path('products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('users/', views.manage_users, name='manage_users'),
]
