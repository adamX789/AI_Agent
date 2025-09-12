from django.db import models
from chat.models import Recepty
from user_profile.models import Profile
from decimal import Decimal

# Create your models here.

class Jidelnicek(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)

class JidelnicekRecept(models.Model):
    jidelnicek = models.ForeignKey(Jidelnicek,on_delete=models.CASCADE,blank=True,null=True)
    recept = models.ForeignKey(Recepty,on_delete=models.CASCADE)
    scale_factor = models.DecimalField(decimal_places=3,max_digits=5,default=Decimal(1))
    chod = models.CharField(max_length=50,blank=True,null=True)
    snezeno = models.BooleanField(default=False)