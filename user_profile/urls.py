from django.urls import path, include
from .views import *

urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path("edit/", EditView.as_view(), name="edit"),
    path("choice/", ChoiceView.as_view(), name="choice"),
    path("form/", StartFormView.as_view(), name="form"),
    path("form/info/", InfoView.as_view(), name="info"),
]
