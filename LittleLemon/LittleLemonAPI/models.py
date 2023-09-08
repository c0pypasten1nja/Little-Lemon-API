from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

# Create your models here.
class MenuItem(models.Model):
    title = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.SmallIntegerField()
    def __str__(self):
        return self.title
    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    class Meta:
        unique_together =('menuitem', 'user')
    def __str__(self):
        return self.user
    
    
class Order(models.Model):
    STATUS_CHOICES = (
        (0, "Out for Delivery"),
        (1, "Delivered"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=0)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True, limit_choices_to={'groups__name': "Delivery crew"})
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()

    def __str__(self):
        return f"{self.order} - {self.menu_item.name}"