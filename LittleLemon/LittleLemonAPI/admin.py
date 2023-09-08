from django.contrib import admin
from .models import MenuItem, Cart, Order, OrderItem

# Register your models here.
admin.site.register([MenuItem, Cart, Order, OrderItem])