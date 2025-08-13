from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    text = models.TextField()
    sender = models.CharField(max_length=128)
    role = models.CharField(max_length=15, null=True, blank=True)
    time_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.text)
