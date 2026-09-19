from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser

def unified_register(request):
    if request.user.is_authenticated:
        return redirect('accounts:login_redirect')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', 'CUSTOMER') # Default to CUSTOMER
        
        phone = request.POST.get('phone_number', '')
        phone_seller = request.POST.get('phone_number_seller', '')
        vehicle = request.POST.get('vehicle_number', '')
        store_name = request.POST.get('store_name', '')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return render(request, 'accounts/register.html', request.POST)
            
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'accounts/register.html', request.POST)
        
        # Merge phone numbers based on role
        if role == 'SELLER':
            phone = phone_seller
            
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('accounts:register')
            
        # Create user
        user = CustomUser.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone_number=phone,
            vehicle_number=vehicle,
            store_name=store_name
        )
        
        if role == 'SELLER':
            user.is_staff = True
            user.save()
            
        login(request, user)
        messages.success(request, f"Registration successful! Welcome {username}.")
        return redirect('accounts:login_redirect')
        
    return render(request, 'accounts/register.html')

def smart_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:login_redirect')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Drain any old messages so none leak into dashboard/store
            storage = messages.get_messages(request)
            for _ in storage:
                pass
            login(request, user)
            return redirect('accounts:login_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        # On GET request to login page, drain any stale messages
        storage = messages.get_messages(request)
        for _ in storage:
            pass
            
    return render(request, 'accounts/login.html')

@login_required
def login_redirect(request):
    """Redirects authenticated users to their respective dashboards based on role."""
    if request.user.is_store_admin() or request.user.is_seller():
        return redirect('custom_admin:dashboard')
    elif request.user.is_delivery_partner():
        return redirect('delivery:dashboard')
    else:
        # Default is CUSTOMER
        return redirect('store:index')

def user_logout(request):
    if request.method in ['GET', 'POST']:
        logout(request)
        # Drain any leftover messages so nothing persists
        storage = messages.get_messages(request)
        for _ in storage:
            pass
        return redirect('store:index')
    return redirect('store:index')

@login_required
def wallet_view(request):
    from .models import UserWallet
    wallet, created = UserWallet.objects.get_or_create(user=request.user)
    # This automatically deducts expired if logic is updated, but right now it just returns self.balance
    valid_balance = wallet.get_valid_balance()
    transactions = wallet.transactions.all().order_by('-created_at')
    
    return render(request, 'accounts/wallet.html', {
        'wallet': wallet,
        'valid_balance': valid_balance,
        'transactions': transactions
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        user.city = request.POST.get('city', user.city)
        user.state = request.POST.get('state', user.state)
        user.pincode = request.POST.get('pincode', user.pincode)
        
        if user.is_delivery_partner():
            user.vehicle_number = request.POST.get('vehicle_number', user.vehicle_number)
            
        if user.is_seller():
            user.store_name = request.POST.get('store_name', user.store_name)
            
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:edit_profile')
        
    return render(request, 'accounts/edit_profile.html')
