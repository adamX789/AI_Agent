from django.db import models


class Message(models.Model):
    text = models.CharField(max_length=1000)
    sender = models.CharField(max_length=128)
    role = models.CharField(max_length=15, null=True, blank=True)
    time_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.text)
