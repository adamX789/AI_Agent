from django.db import models
from chat.models import Recepty
from user_profile.models import Profile

# Create your models here.
class Jidelnicek(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    seznam_snidani = models.ManyToManyField(Recepty,related_name="snidane_recepty")
    seznam_svacin1 = models.ManyToManyField(Recepty,related_name="svacina1_recepty")
    seznam_obedu = models.ManyToManyField(Recepty,related_name="obed_recepty")
    seznam_svacin2 = models.ManyToManyField(Recepty,related_name="svacina2_recepty")
    seznam_veceri = models.ManyToManyField(Recepty,related_name="vecere_recepty")

class VybraneRecepty(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    snidane = models.ForeignKey(Recepty,on_delete=models.CASCADE,blank=True,null=True,related_name="vybrana_snidane")
    snidane_snezena = models.BooleanField(default=False)
    svacina1 = models.ForeignKey(Recepty,on_delete=models.CASCADE,blank=True,null=True,related_name="vybrana_svacina1")
    svacina1_snezena = models.BooleanField(default=False)
    obed = models.ForeignKey(Recepty,on_delete=models.CASCADE,blank=True,null=True,related_name="vybrany_obed")
    obed_snezen = models.BooleanField(default=False)
    svacina2 = models.ForeignKey(Recepty,on_delete=models.CASCADE,blank=True,null=True,related_name="vybrana_svacina2")
    svacina2_snezena = models.BooleanField(default=False)
    vecere = models.ForeignKey(Recepty,on_delete=models.CASCADE,blank=True,null=True,related_name="vybrana_vecere")
    vecere_snezena = models.BooleanField(default=False)