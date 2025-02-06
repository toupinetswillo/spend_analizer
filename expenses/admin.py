from django.contrib import admin
from .models import Receipt, Expense, ExpenseItem
# Register your models here.
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['image', 'uploaded_at']
    list_filter = ['image', 'uploaded_at']
    search_fields = ['uploaded_at']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['category', 'description']


@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ['expense', 'description', 'price', 'total']
    list_filter = ['expense', 'description']
    search_fields = ['description']
