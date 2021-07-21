from carts.models import Cart
from django.contrib import admin
from .import models

# Register your models here.
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_Added')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart' ,'qunatity' ,'is_active')

admin.site.register(models.Cart, CartAdmin)
admin.site.register(models.CartItem, CartItemAdmin)
