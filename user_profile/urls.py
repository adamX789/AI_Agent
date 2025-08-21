from django.urls import path, include
from .views import *

urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path("edit/",EditView.as_view(),name="edit")
]