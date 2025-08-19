from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField

class Message(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    text = models.TextField()
    sender = models.CharField(max_length=128)
    role = models.CharField(max_length=15, null=True, blank=True)
    time_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.text)


class Potraviny(models.Model):
    nazev = models.CharField(max_length=150)
    popis = models.TextField()
    vyhody = ArrayField(models.CharField(max_length=256))
    nejlepsi_pro = ArrayField(models.CharField(max_length=256))
    nekonzumujte_pokud = ArrayField(models.CharField(max_length=256))
    embedding = VectorField(dimensions=768)

    def __str__(self) -> str:
        return str(self.nazev)

class Makroziviny(models.Model):
    potravina = models.OneToOneField(Potraviny, on_delete=models.CASCADE,blank=True,null=True)
    bilkoviny_gramy = models.DecimalField(decimal_places=2,max_digits=6)
    sacharidy_gramy = models.DecimalField(decimal_places=2,max_digits=6)
    tuky_gramy = models.DecimalField(decimal_places=2,max_digits=6)

class Recepty(models.Model):
    nazev = models.CharField(max_length=150)
    ingredience = ArrayField(models.CharField(max_length=150))
    instrukce = models.TextField()
    vhodne_pro = ArrayField(models.CharField(max_length=150))
    embedding = VectorField(dimensions=768)

    def __str__(self) -> str:
        return str(self.nazev)

class Situace(models.Model):
    popis_situace = models.TextField()
    rada = models.TextField()
    embedding = VectorField(dimensions=768)

class Diety(models.Model):
    nazev_diety = models.CharField(max_length=150)
    popis = models.TextField()
    vyhody = ArrayField(models.CharField(max_length=150))
    neni_doporuceno_pro = ArrayField(models.CharField(max_length=256))
    embedding = VectorField(dimensions=768)

    def __str__(self) -> str:
        return str(self.nazev_diety)

class StylyKomunikace(models.Model):
    styl = models.CharField(max_length=100)
    priklad = models.TextField()
    embedding = VectorField(dimensions=768)