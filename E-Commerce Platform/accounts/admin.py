from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Roles & Fields', {'fields': ('role', 'phone_number', 'address', 'city', 'state', 'pincode', 'vehicle_number', 'store_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Roles & Fields', {'fields': ('role', 'phone_number', 'address', 'city', 'state', 'pincode', 'vehicle_number', 'store_name')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
