from django.db import models
from django.contrib.auth.models import User

class Receipt(models.Model):
    image = models.ImageField(upload_to='receipts/', null=True)  # Image of the receipt
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Date when the receipt was uploaded
    expense = models.ForeignKey('Expense', related_name="receipts", on_delete=models.CASCADE, null=True)  # Link receipt to an expense
class Expense(models.Model):
    category = models.CharField(max_length=100, null=True)  # Expense category (e.g., Grocery, Entertainment)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Expense amount
    description = models.CharField(max_length=255, blank=True, null=True)  # Optional description
    transaction_date = models.DateField(null=True)  # Date when the expense was made
    post_date = models.DateField(null=True)  # Date when the expense
    merchant = models.CharField(max_length=255, null=True)  # Merchant name
    created_at = models.DateTimeField(auto_now_add=True)  # Date when the expense was recorded


class ExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)  # Link item to an expense
    description = models.CharField(max_length=255)  # Item description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Item price
    total = models.DecimalField(max_digits=10, decimal_places=2)  # Total price
