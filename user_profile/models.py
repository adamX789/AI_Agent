from django.db import models
from chat.models import Potraviny, Makroziviny
from django.contrib.auth.models import User


class Profile(models.Model):
    uzivatel = models.OneToOneField(User, on_delete=models.CASCADE)
    jmeno = models.CharField(blank=True,null=True,max_length=100)
    jednoduchy_formular = models.BooleanField(blank=True,null=True)
    pohlavi = models.CharField(blank=True,null=True,max_length=20)
    vyska_v_cm = models.DecimalField(decimal_places=2,max_digits=5,blank=True,null=True)
    vek = models.IntegerField(blank=True,null=True)
    dieta = models.CharField(blank=True,null=True,max_length=70)
    denni_kalorie = models.IntegerField(blank=True, null=True)
    denni_bilkoviny = models.IntegerField(blank=True, null=True)
    denni_sacharidy = models.IntegerField(blank=True, null=True)
    denni_tuky = models.IntegerField(blank=True, null=True)
    pitny_rezim_litry = models.DecimalField(decimal_places=2,max_digits=5,blank=True,null=True)
    aktualni_vaha = models.DecimalField(decimal_places=2,max_digits=5,blank=True,null=True)
    cilova_vaha = models.DecimalField(decimal_places=2,max_digits=5,blank=True,null=True)
    celkovy_cil = models.CharField(blank=True,null=True,max_length=50)
    aktivita = models.CharField(blank=True,null=True,max_length=30)
    zdravotni_omezeni = models.CharField(blank=True,null=True,max_length=150)



class Food(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    potravina = models.ForeignKey(Potraviny, on_delete=models.CASCADE)
    hmotnost_g = models.DecimalField(decimal_places=2,max_digits=6,blank=True,null=True)
