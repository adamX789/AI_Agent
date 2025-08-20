from django.urls import path, include
from .views import *

urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
]