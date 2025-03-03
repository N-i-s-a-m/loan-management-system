"""
URL configuration for loan_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import JsonResponse
from django.urls import path, include
from django.contrib import admin

def home_view(request):
    return JsonResponse({"message": "Welcome to Loan Management API"}, status=200)

urlpatterns = [
    path('', home_view),  # Root route
    path('admin/', admin.site.urls),
    path('api/', include('your_app.urls')),
]