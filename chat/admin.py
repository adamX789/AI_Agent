from django.contrib import admin
from .models import *


class MessageAdmin(admin.ModelAdmin):
    list_display = ("text", "sender", "role", "time_sent")


admin.site.register(Message, MessageAdmin)
