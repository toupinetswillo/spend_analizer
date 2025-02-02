from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', RedirectView.as_view(url='expenses/', permanent=True)),
    path('admin/', admin.site.urls),
    path('expenses/', include('expenses.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
