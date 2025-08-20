from django.db import models
from chat.models import Potraviny, Makroziviny
from django.contrib.auth.models import User


class Profile(models.Model):
    uzivatel = models.OneToOneField(User, on_delete=models.CASCADE)
    denni_kalorie = models.IntegerField(blank=True, null=True)


class Food(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    potravina = models.ForeignKey(Potraviny, on_delete=models.CASCADE)
