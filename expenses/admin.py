from django.contrib import admin
from .models import Receipt, Expense
# Register your models here.
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['user', 'uploaded_at']
    list_filter = ['user', 'uploaded_at']
    search_fields = ['user__username', 'uploaded_at']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['receipt', 'category', 'amount', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['category', 'description']
