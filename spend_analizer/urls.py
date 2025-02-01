from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='expenses/', permanent=True)),
    path('admin/', admin.site.urls),
    path('expenses/', include('expenses.urls')),
    path('accounts/', include('allauth.urls')),
]
