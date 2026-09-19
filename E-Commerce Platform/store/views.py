from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, Review, Wishlist
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .ai_services import get_ai_search_intent, generate_review_summary, auto_generate_product_description, get_chatbot_response
import json

def index(request):
    featured_products = Product.objects.filter(available=True)[:4]
    latest_products = Product.objects.filter(available=True).order_by('-created')[:8]
    categories = Category.objects.all()
    return render(request, 'index.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    })

def contact_view(request):
    from django.contrib import messages
    if request.method == 'POST':
        # Simple processing
        name = request.POST.get('first_name', '') + ' ' + request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        
        messages.success(request, "Thank you! Your message has been received.")
        return redirect('store:contact')
        
    return render(request, 'contact.html')

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()

    # Filter by Category (via slug or GET param)
    req_category = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    elif req_category and req_category != request.path:
        # category could be slug or name
        category = Category.objects.filter(Q(slug=req_category) | Q(name__iexact=req_category)).first()
        if category:
            products = products.filter(category=category)

    # AI Search Intent
    query = request.GET.get('q', '')
    if query:
        intent = get_ai_search_intent(query)
        cats = intent.get('categories', [])
        tags = intent.get('tags', [])
        
        q_objects = Q()
        if cats:
            q_objects |= Q(category__name__in=cats)
        if tags:
            for tag in tags:
                q_objects |= Q(name__icontains=tag) | Q(description__icontains=tag) | Q(ai_tags__icontains=tag)
        
        # If AI didn't find anything useful, fallback to standard text search
        if not cats and not tags:
            q_objects = Q(name__icontains=query) | Q(description__icontains=query)

        products = products.filter(q_objects).distinct()

    # Advanced Multi-Filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    target = request.GET.get('target')
    if target:
        products = products.filter(target=target)

    rating = request.GET.get('rating')
    if rating:
        # A simple approach for filtering by average rating (could be optimized with aggregation)
        products = [p for p in products if p.average_rating >= float(rating)]
        # Re-convert to queryset if possible or handle sorting below carefully
        # Actually, sorting on list is different from sorting on queryset.
        # It's better to avoid converting to list here if we need to order_by later.
        # But average_rating is a property. Let's just keep as list if rating is used, 
        # or we can do it after ordering.
        
    in_stock = request.GET.get('in_stock', '').strip().lower()
    if in_stock in ['on', 'true', '1']:
        if isinstance(products, list):
            products = [p for p in products if p.stock > 0]
        else:
            products = products.filter(stock__gt=0)

    # Sort
    sort = request.GET.get('sort')
    if sort:
        if isinstance(products, list):
            if sort == 'price_low':
                products.sort(key=lambda x: x.price)
            elif sort == 'price_high':
                products.sort(key=lambda x: x.price, reverse=True)
            elif sort == 'rating':
                products.sort(key=lambda x: (x.average_rating, x.created), reverse=True)
            elif sort == 'newest':
                products.sort(key=lambda x: x.created, reverse=True)
        else:
            if sort == 'price_low':
                products = products.order_by('price')
            elif sort == 'price_high':
                products = products.order_by('-price')
            elif sort == 'rating':
                products = products.order_by('-created') # Fallback if average_rating is not a DB column
            elif sort == 'newest':
                products = products.order_by('-created')
    elif not isinstance(products, list):
        products = products.order_by('-created')

    return render(request, 'shop.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug)
    reviews = product.reviews.all()
    
    # AI Review Summary Logic
    ai_summary = ""
    if reviews.exists() and len(reviews) >= 2:
        reviews_text = " ".join([r.comment for r in reviews[:10]]) # take top 10
        ai_summary = generate_review_summary(reviews_text)
        
    variants = product.variants.all()
    
    # Compute unique images for the gallery
    unique_images = []
    if product.image:
        unique_images.append(product.image.url)
    for variant in variants:
        if variant.image and variant.image.url not in unique_images:
            unique_images.append(variant.image.url)

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews,
        'ai_summary': ai_summary,
        'variants': variants,
        'unique_images': unique_images,
    })

import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from store.models import Product, Category

@csrf_exempt
def ai_chat_response(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'reply': 'Invalid request method.'})

    try:
        body = json.loads(request.body.decode('utf-8'))
        user_message = body.get('message', '').strip()
    except Exception:
        user_message = request.POST.get('message', '').strip()

    if not user_message:
        return JsonResponse({'success': False, 'reply': 'Please ask a question!'})

    # Fetch store catalog context from DB
    try:
        categories = list(Category.objects.values_list('name', flat=True))
        category_list_str = ", ".join(categories) if categories else "Clothes, Grocery, Jewellery, Toys, Electronics, Yoga"
        
        products = Product.objects.all()[:20]
        catalog_items = [f"- {p.name} (Category: {getattr(p.category, 'name', 'General')}, Price: ₹{p.price})" for p in products]
        catalog_text = "\n".join(catalog_items)
    except Exception as e:
        category_list_str = "Clothes, Grocery, Jewellery, Toys, Electronics, Yoga"
        catalog_text = "Various premium products available in store."

    gemini_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    # System prompt strictly instructing ShopEase context
    system_prompt = f"""
    You are 'ShopEase AI', the official friendly shopping assistant for ShopEase.
    Our available product categories are: {category_list_str}.
    Some available products in our store:
    {catalog_text}

    Store Policies:
    - 10% discount on first purchase with coupon: WELCOME10
    - Fast delivery in 24-48 hours.
    - 7-day easy returns with doorstep pickup by rider.

    Answer the user warmly and concisely. Recommend products and mention categories clearly.
    """

    # If Gemini API Key is available, call Gemini API
    if gemini_key and gemini_key != 'your_actual_gemini_api_key_here':
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt + "\n\nUser: " + user_message}
                    ]
                }
            ]
        }
        try:
            res = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                ai_text = data['candidates'][0]['content']['parts'][0]['text']
                return JsonResponse({'success': True, 'reply': ai_text})
            else:
                print("Gemini API Error details:", res.status_code, res.text)
        except Exception as err:
            print("Gemini API Request Exception:", err)

    # Smart local fallback: If API key is missing or failed, answer directly from store catalog!
    msg_lower = user_message.lower()
    if 'categor' in msg_lower:
        fallback_reply = f"At ShopEase, we offer a wide variety of categories including: **{category_list_str}**! What are you shopping for today?"
    elif 'discount' in msg_lower or 'offer' in msg_lower or 'coupon' in msg_lower:
        fallback_reply = "You can use coupon code **WELCOME10** at checkout to get an instant **10% OFF** on your order! 🎁"
    elif 'return' in msg_lower or 'refund' in msg_lower:
        fallback_reply = "We have a hassle-free **7-day return policy**. Once requested, our delivery partner will pick up the item from your doorstep! 🚚"
    elif 'delivery' in msg_lower or 'shipping' in msg_lower:
        fallback_reply = "We offer fast 24-48 hour delivery across India! ⚡"
    else:
        fallback_reply = f"Welcome to ShopEase! We have popular products across {category_list_str}. You can also use code **WELCOME10** for 10% off! How can I assist you with your shopping?"

    return JsonResponse({'success': True, 'reply': fallback_reply})

def admin_generate_desc(request):
    """AJAX endpoint for admin panel to generate description"""
    if request.user.is_staff and request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            tags = data.get('tags', '')
            desc = auto_generate_product_description(title, tags)
            return JsonResponse({'description': desc})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Unauthorized'}, status=403)

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
@csrf_exempt
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed', 'message': 'Removed from wishlist'})
        else:
            return JsonResponse({'status': 'added', 'message': 'Added to wishlist'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import NewsletterSubscriber

from django.views.decorators.http import require_POST

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from orders.models import Coupon
from django.utils import timezone
from datetime import timedelta

@require_POST
def newsletter_subscribe(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
    except:
        email = request.POST.get('email', '').strip().lower()

    if not email:
        return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)
    
    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if created:
        coupon, _ = Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount': 10,
                'active': True,
                'valid_from': timezone.now(),
                'valid_to': timezone.now() + timedelta(days=365*10),
                'min_order_amount': 0
            }
        )
        
        subject = '🎁 Welcome to ShopEase! Here is your 10% OFF Coupon'
        html_message = render_to_string('store/email_welcome_coupon.html', {'code': coupon.code})
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message)
        except Exception as e:
            pass # Failsafe if SMTP misconfigured locally
            
        return JsonResponse({'success': True, 'message': f'Coupon code {coupon.code} has been sent to your email!'})
    else:
        return JsonResponse({'success': False, 'message': 'You are already subscribed!'})

def about_view(request):
    return render(request, 'store/about.html')

def faq_view(request):
    return render(request, 'store/faq.html')

def returns_policy_view(request):
    return render(request, 'store/returns_policy.html')
