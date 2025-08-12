from django.urls import path, include
from .views import *

urlpatterns = [
    path("", ChatView.as_view(), name="chat"),
]
