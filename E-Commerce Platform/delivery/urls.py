from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-status/<int:order_id>/', views.update_status, name='update_status'),
    path('pickup/confirm/<int:return_id>/', views.confirm_pickup, name='confirm_pickup'),
]
