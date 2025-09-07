from django.urls import path, include
from .views import *

urlpatterns = [
    path("",MyDayView.as_view(),name="my_day"),
    path("add/",AddView.as_view(),name="add"),
    path("add_food/",AddFoodView.as_view(),name="add_food"),
]