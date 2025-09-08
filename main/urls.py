"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from register.views import RegisterView, user_logout,tutorial

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("chat.urls")),
    path("register/", RegisterView.as_view(), name="register"),
    path("tutorial/", tutorial, name="tutorial"),
    path("user_logout/", user_logout, name="logout"),
    path("profile/", include("user_profile.urls")),
    path("my_day/", include("muj_den.urls")),
]
