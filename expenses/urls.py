from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_receipt, name='upload_receipt'),
    path('upload_csv/', views.upload_csv, name='upload_csv'),
    path('list/', views.list, name='list'),
    path('details/', views.expense_details, name='expense_details'),
    path('update-expense-items/', views.update_expenses_items, name='update_expenses_items'),
    path('update-expense-info/', views.update_expense_info, name='update_expense_info'),
    path('remove-receipt/<int:receipt_id>/', views.remove_receipt, name='remove_receipt'),
]
