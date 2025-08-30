from django.urls import path, include
from .views import *

urlpatterns = [
    path("",MyDayView.as_view(),name="my_day")
]