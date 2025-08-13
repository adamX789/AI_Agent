import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from .main import chatbot
from .models import *


class ChatView(View):
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            all_messages = Message.objects.all().order_by("id")
            return render(request, "chat.html", {"messages": all_messages})
        return render(request, "not_logged_in.html",{})

    def post(self, request):
        data = json.loads(request.body)
        message = data.get("message")
        Message.objects.create(text=message, sender="Vy", role="user")

        agent_response = chatbot(message)
        Message.objects.create(text=agent_response,
                               sender="Podpora", role="agent")
        return JsonResponse({"response":agent_response})
