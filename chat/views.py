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
            all_messages = user.message_set.all().order_by("id")
            return render(request, "chat.html", {"messages": all_messages})
        return render(request, "not_logged_in.html",{})

    def post(self, request):
        user = request.user
        data = json.loads(request.body)
        message = data.get("message")
        user.message_set.create(text=message, sender="Vy", role="user")

        agent_response = chatbot(message)
        user.message_set.create(text=agent_response,
                               sender="Podpora", role="agent")
        return JsonResponse({"response":agent_response})
