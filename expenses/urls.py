from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_receipt, name='upload_receipt'),
    path('upload_csv/', views.upload_csv, name='upload_csv'),
    path('list/', views.list, name='list'),
    path('details/', views.expense_details, name='expense_details'),
]
