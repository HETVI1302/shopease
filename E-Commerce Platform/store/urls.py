from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),
    path('shop/', views.product_list, name='shop'),
    path('shop/<slug:category_slug>/', views.product_list, name='category_list'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('ai-chat/', views.ai_chat_response, name='ai_chat'),
    path('api/admin-generate-desc/', views.admin_generate_desc, name='admin_generate_desc'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('contact/', views.contact_view, name='contact'),
    path('api/newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('about/', views.about_view, name='about'),
    path('faq/', views.faq_view, name='faq'),
    path('returns-policy/', views.returns_policy_view, name='returns_policy'),
]
