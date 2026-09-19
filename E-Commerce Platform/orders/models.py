from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from store.models import Product, ProductVariant

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text='Percentage value (0 to 100)')
    active = models.BooleanField()
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.code

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=200, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())

    @property
    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / 100.0) * float(self.get_total_price)
        return 0

    @property
    def get_total_price_after_discount(self):
        return float(self.get_total_price) - self.get_discount

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    def get_cost(self):
        price = self.product.price
        if self.variant:
            price += self.variant.additional_price
        return price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('Placed', 'Placed'),
        ('Assigned', 'Assigned to Partner'),
        ('Picked Up', 'Picked Up'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Return Approved', 'Return Approved'),
        ('Refunded', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    shipping_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    
    # Razorpay Integration
    razorpay_order_id = models.CharField(max_length=250, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=250, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=250, blank=True, null=True)
    
    # Payment method (COD or Razorpay)
    payment_method = models.CharField(max_length=20, default='Razorpay')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Placed')
    
    # Delivery assignment
    delivery_partner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_deliveries'
    )

    # Coupon tracking
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    wallet_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Return & Refund
    return_reason = models.CharField(max_length=255, blank=True, null=True)
    return_comment = models.TextField(blank=True, null=True)
    refund_status = models.CharField(max_length=50, blank=True, null=True, default='Pending')

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        total_cost = sum(item.get_cost() for item in self.items.all())
        return float(total_cost) - float(self.discount_amount) - float(self.wallet_discount)

    @property
    def total_amount(self):
        return self.get_total_cost()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

class ReturnRequest(models.Model):
    RETURN_REASON_CHOICES = [
        ('DEFECTIVE', 'Defective or Damaged Item'),
        ('WRONG_ITEM', 'Wrong Item Delivered'),
        ('SIZE_FIT', 'Size/Fit Issue'),
        ('QUALITY', 'Quality Not as Expected'),
        ('OTHER', 'Other Reason')
    ]
    
    REFUND_METHOD_CHOICES = [
        ('ORIGINAL', 'Original Payment Method (Razorpay)'),
        ('UPI', 'UPI / Bank Transfer'),
        ('STORE_WALLET', 'ShopEase Wallet / Credit')
    ]
    
    STATUS_CHOICES = [
        ('REQUESTED', 'Return Requested'),
        ('PICKUP_ASSIGNED', 'Pickup Assigned'),
        ('PICKED_UP', 'Picked Up'),
        ('APPROVED', 'Return Approved'),
        ('RECEIVED', 'Item Received at Warehouse'),
        ('REFUNDED', 'Refund Completed'),
        ('REJECTED', 'Return Rejected')
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_rider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_tasks')
    reason = models.CharField(max_length=100, choices=RETURN_REASON_CHOICES)
    additional_notes = models.TextField(blank=True, null=True)
    refund_method = models.CharField(max_length=50, choices=REFUND_METHOD_CHOICES, default='ORIGINAL')
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REQUESTED')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Return for Order {self.order.id} - {self.get_status_display()}"
