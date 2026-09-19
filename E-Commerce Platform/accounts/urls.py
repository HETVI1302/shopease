from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.smart_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('redirect/', views.login_redirect, name='login_redirect'),
    path('register/', views.unified_register, name='register'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
