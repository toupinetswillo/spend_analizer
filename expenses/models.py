from django.db import models
from django.contrib.auth.models import User

class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link receipt to a user
    image = models.ImageField(upload_to='receipts/')  # Store scanned receipt image
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Date when the receipt was uploaded

class Expense(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, null=True)  # Link expense to the receipt
    category = models.CharField(max_length=100)  # Expense category (e.g., Grocery, Entertainment)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Expense amount
    description = models.CharField(max_length=255, blank=True, null=True)  # Optional description
    transaction_date = models.DateField(null=True)  # Date when the expense was made
    post_date = models.DateField(null=True)  # Date when the expense
    merchant = models.CharField(max_length=255, null=True)  # Merchant name
    created_at = models.DateTimeField(auto_now_add=True)  # Date when the expense was recorded
