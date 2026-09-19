import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopease_project.settings')
django.setup()

from store.models import Category, Product, ProductVariant
from orders.models import Coupon, Order, OrderItem
from accounts.models import CustomUser

def create_users():
    print("Creating users...")
    users_data = [
        # Admin
        {
            'username': 'admin', 'password': 'password123', 'email': 'admin@shopease.com',
            'role': 'ADMIN', 'first_name': 'Super', 'last_name': 'Admin', 'is_superuser': True, 'is_staff': True
        },
        # Customers
        {
            'username': 'rahul_sharma', 'password': 'password123', 'email': 'rahul@example.com',
            'role': 'CUSTOMER', 'first_name': 'Rahul', 'last_name': 'Sharma', 'city': 'Mumbai', 'phone_number': '9876543210'
        },
        {
            'username': 'priya_patel', 'password': 'password123', 'email': 'priya@example.com',
            'role': 'CUSTOMER', 'first_name': 'Priya', 'last_name': 'Patel', 'city': 'Ahmedabad', 'phone_number': '9876543211'
        },
        {
            'username': 'amit_verma', 'password': 'password123', 'email': 'amit@example.com',
            'role': 'CUSTOMER', 'first_name': 'Amit', 'last_name': 'Verma', 'city': 'Delhi', 'phone_number': '9876543212'
        },
        # Delivery Partners
        {
            'username': 'delivery_ravi', 'password': 'password123', 'email': 'ravi@shopease.com',
            'role': 'DELIVERY_PARTNER', 'first_name': 'Ravi', 'last_name': 'Kumar', 'vehicle_number': 'MH-01-AB-1234', 'phone_number': '9123456780'
        },
        {
            'username': 'delivery_vikas', 'password': 'password123', 'email': 'vikas@shopease.com',
            'role': 'DELIVERY_PARTNER', 'first_name': 'Vikas', 'last_name': 'Singh', 'vehicle_number': 'GJ-01-CD-5678', 'phone_number': '9123456781'
        }
    ]

    for u_data in users_data:
        is_superuser = u_data.pop('is_superuser', False)
        is_staff = u_data.pop('is_staff', False)
        if not CustomUser.objects.filter(username=u_data['username']).exists():
            user = CustomUser.objects.create_user(**u_data)
            if is_superuser or is_staff:
                user.is_superuser = is_superuser
                user.is_staff = is_staff
                user.save()
            print(f" - Created {u_data['role']}: {u_data['username']}")
        else:
            print(f" - User {u_data['username']} already exists")

def create_categories():
    print("Creating categories...")
    categories = ['Clothes', 'Grocery', 'Jewellery', 'Toys', 'Electronics', 'Yoga']
    cat_objs = {}
    for cat_name in categories:
        slug = cat_name.lower()
        obj, created = Category.objects.get_or_create(name=cat_name, slug=slug)
        cat_objs[cat_name] = obj
        if created:
            print(f" - Created category: {cat_name}")
    return cat_objs

def create_products(categories):
    print("Creating products and variants...")
    
    products_data = [
        {
            'name': 'Men Classic Cotton T-Shirt',
            'slug': 'men-classic-cotton-tshirt',
            'category': categories['Clothes'],
            'description': 'A comfortable and breathable classic cotton t-shirt for everyday wear. Made from 100% organic cotton.',
            'price': '499.00',
            'stock': 50,
            'target': 'Men',
            'ai_tags': 'tshirt, casual, cotton, comfortable, men, top',
            'variants': [
                {'size': 'S', 'color': 'Blue', 'additional_price': '0.00'},
                {'size': 'M', 'color': 'Black', 'additional_price': '0.00'},
                {'size': 'L', 'color': 'White', 'additional_price': '0.00'},
                {'size': 'XL', 'color': 'Red', 'additional_price': '50.00'},
            ]
        },
        {
            'name': 'Women Floral Summer Dress',
            'slug': 'women-floral-summer-dress',
            'category': categories['Clothes'],
            'description': 'Light and breezy floral summer dress perfect for the beach or casual outings. Features a comfortable elastic waist.',
            'price': '1299.00',
            'stock': 30,
            'target': 'Women',
            'ai_tags': 'dress, summer, floral, casual, women, beach',
            'variants': [
                {'size': 'S', 'color': 'Blue', 'additional_price': '0.00'},
                {'size': 'M', 'color': 'Red', 'additional_price': '0.00'},
                {'size': 'L', 'color': 'White', 'additional_price': '0.00'},
            ]
        },
        {
            'name': 'Organic Almonds (1kg)',
            'slug': 'organic-almonds-1kg',
            'category': categories['Grocery'],
            'description': 'Premium quality, unroasted, and unsalted organic Californian almonds. Packed with nutrients.',
            'price': '899.00',
            'stock': 100,
            'target': 'Unisex',
            'ai_tags': 'almonds, nuts, organic, healthy, snack, grocery',
            'variants': []
        },
        {
            'name': 'Premium Darjeeling Tea',
            'slug': 'premium-darjeeling-tea',
            'category': categories['Grocery'],
            'description': 'Authentic first flush Darjeeling tea with a delicate floral aroma and muscatel flavor.',
            'price': '450.00',
            'stock': 80,
            'target': 'Unisex',
            'ai_tags': 'tea, beverage, hot, premium, morning, grocery',
            'variants': []
        },
        {
            'name': 'Silver Plated Pendant Necklace',
            'slug': 'silver-plated-pendant-necklace',
            'category': categories['Jewellery'],
            'description': 'Elegant silver plated pendant necklace featuring a minimalist cubic zirconia crystal design.',
            'price': '799.00',
            'stock': 20,
            'target': 'Women',
            'ai_tags': 'necklace, jewelry, silver, elegant, women, accessory',
            'variants': []
        },
        {
            'name': 'Men Stainless Steel Chronograph Watch',
            'slug': 'men-stainless-steel-watch',
            'category': categories['Jewellery'],
            'description': 'Sleek stainless steel chronograph watch with water resistance up to 50 meters and a luminous dial.',
            'price': '2499.00',
            'stock': 15,
            'target': 'Men',
            'ai_tags': 'watch, timepiece, men, stainless steel, accessory, formal',
            'variants': []
        },
        {
            'name': 'Building Blocks 500 pcs Set',
            'slug': 'building-blocks-500-pcs',
            'category': categories['Toys'],
            'description': 'Unleash creativity with this 500-piece building block set. Includes various shapes and vibrant colors.',
            'price': '999.00',
            'stock': 40,
            'target': 'Kids',
            'ai_tags': 'toys, kids, building blocks, creative, educational, fun',
            'variants': []
        },
        {
            'name': 'Remote Control Stunt Car',
            'slug': 'remote-control-stunt-car',
            'category': categories['Toys'],
            'description': 'High-speed 4WD remote control stunt car capable of 360-degree flips and off-road driving.',
            'price': '1599.00',
            'stock': 25,
            'target': 'Kids',
            'ai_tags': 'toys, kids, remote control, car, fun, action',
            'variants': [
                {'size': 'NA', 'color': 'Red', 'additional_price': '0.00'},
                {'size': 'NA', 'color': 'Blue', 'additional_price': '0.00'},
            ]
        },
        {
            'name': 'Noise Cancelling Wireless Headphones',
            'slug': 'noise-cancelling-wireless-headphones',
            'category': categories['Electronics'],
            'description': 'Over-ear wireless headphones with active noise cancellation, deep bass, and 40-hour battery life.',
            'price': '4999.00',
            'stock': 10,
            'target': 'Unisex',
            'ai_tags': 'electronics, headphones, wireless, audio, music, noise cancelling',
            'variants': [
                {'size': 'NA', 'color': 'Black', 'additional_price': '0.00'},
                {'size': 'NA', 'color': 'White', 'additional_price': '200.00'},
            ]
        },
        {
            'name': 'Smart Fitness Band',
            'slug': 'smart-fitness-band',
            'category': categories['Electronics'],
            'description': 'Track your health and workouts with this smart fitness band featuring heart rate monitoring and sleep tracking.',
            'price': '1999.00',
            'stock': 60,
            'target': 'Unisex',
            'ai_tags': 'electronics, fitness, band, smartwatch, health, tracking',
            'variants': [
                {'size': 'NA', 'color': 'Black', 'additional_price': '0.00'},
            ]
        },
        {
            'name': 'Non-Slip Eco-Friendly Yoga Mat',
            'slug': 'non-slip-eco-friendly-yoga-mat',
            'category': categories['Yoga'],
            'description': 'Premium 6mm thick eco-friendly TPE yoga mat with excellent grip and cushioning for joint support.',
            'price': '899.00',
            'stock': 45,
            'target': 'Unisex',
            'ai_tags': 'yoga, fitness, exercise, health, gym, mat',
            'variants': [
                {'size': 'NA', 'color': 'Red', 'additional_price': '0.00'},
                {'size': 'NA', 'color': 'Blue', 'additional_price': '0.00'},
            ]
        }
    ]

    for p_data in products_data:
        variants_data = p_data.pop('variants')
        product, created = Product.objects.get_or_create(
            slug=p_data['slug'],
            defaults=p_data
        )
        if created:
            print(f" - Created product: {product.name}")
            for v_data in variants_data:
                ProductVariant.objects.create(product=product, **v_data)
        else:
            print(f" - Product {product.name} already exists")

def create_coupons():
    print("Creating coupons...")
    now = timezone.now()
    
    coupons = [
        {'code': 'WELCOME50', 'discount': 5, 'valid_from': now, 'valid_to': now + timedelta(days=365), 'active': True, 'min_order_amount': 500.00},
        {'code': 'FESTIVE20', 'discount': 20, 'valid_from': now, 'valid_to': now + timedelta(days=30), 'active': True, 'min_order_amount': 1000.00},
        {'code': 'FREESHIP', 'discount': 10, 'valid_from': now, 'valid_to': now + timedelta(days=90), 'active': True, 'min_order_amount': 1500.00},
    ] # Note: discount is percentage. Welcome50 is supposed to be ₹50 off, but coupon model only supports percentage discount. Changing to 5% off for WELCOME50, and 10% off for FREESHIP.
    
    for c_data in coupons:
        obj, created = Coupon.objects.get_or_create(code=c_data['code'], defaults=c_data)
        if created:
            print(f" - Created coupon: {c_data['code']} ({c_data['discount']}% off)")
        else:
            print(f" - Coupon {c_data['code']} already exists")

def create_orders():
    print("Creating sample orders...")
    rahul = CustomUser.objects.get(username='rahul_sharma')
    priya = CustomUser.objects.get(username='priya_patel')
    amit = CustomUser.objects.get(username='amit_verma')

    ravi = CustomUser.objects.get(username='delivery_ravi')
    vikas = CustomUser.objects.get(username='delivery_vikas')

    products = list(Product.objects.all())
    
    if len(products) < 3:
        print("Not enough products to create orders.")
        return

    # Order 1: Assigned to Ravi (Out for Delivery)
    if not Order.objects.filter(user=rahul).exists():
        order1 = Order.objects.create(
            user=rahul, first_name=rahul.first_name, last_name=rahul.last_name, email=rahul.email,
            address='123 Marine Drive', postal_code='400001', city=rahul.city, paid=True, payment_method='Razorpay',
            status='Out for Delivery', delivery_partner=ravi
        )
        OrderItem.objects.create(order=order1, product=products[0], price=products[0].price, quantity=2)
        print(" - Created Order 1 (Out for Delivery - Assigned to delivery_ravi)")
    else:
        print(" - Order 1 already exists")

    # Order 2: Assigned to Vikas (Delivered)
    if not Order.objects.filter(user=priya).exists():
        order2 = Order.objects.create(
            user=priya, first_name=priya.first_name, last_name=priya.last_name, email=priya.email,
            address='456 SG Highway', postal_code='380015', city=priya.city, paid=True, payment_method='COD',
            status='Delivered', delivery_partner=vikas
        )
        OrderItem.objects.create(order=order2, product=products[1], price=products[1].price, quantity=1)
        OrderItem.objects.create(order=order2, product=products[2], price=products[2].price, quantity=3)
        print(" - Created Order 2 (Delivered - Assigned to delivery_vikas)")
    else:
        print(" - Order 2 already exists")

    # Order 3: Unassigned (Placed)
    if not Order.objects.filter(user=amit).exists():
        order3 = Order.objects.create(
            user=amit, first_name=amit.first_name, last_name=amit.last_name, email=amit.email,
            address='789 Connaught Place', postal_code='110001', city=amit.city, paid=False, payment_method='COD',
            status='Placed'
        )
        OrderItem.objects.create(order=order3, product=products[3], price=products[3].price, quantity=5)
        print(" - Created Order 3 (Placed - Unassigned)")
    else:
        print(" - Order 3 already exists")

def run():
    print("=== Starting Database Seeding ===")
    create_users()
    categories = create_categories()
    create_products(categories)
    create_coupons()
    create_orders()
    print("=== Seeding Completed ===")

if __name__ == '__main__':
    run()
