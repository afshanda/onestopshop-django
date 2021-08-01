from django.contrib import admin
from .import models

class OrderProductInline(admin.TabularInline):
    model = models.OrderProduct
    readonly_fields = ('user', 'payment', 'product','quantity','product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    inlines = [OrderProductInline]

admin.site.register(models.Payment)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.OrderProduct)
