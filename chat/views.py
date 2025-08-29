import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from .main import chatbot,chatbot_picture
from .models import *
from user_profile.models import Profile


class ChatView(View):
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            all_messages = user.message_set.all().order_by("id")
            return render(request, "chat.html", {"messages": all_messages})
        return render(request, "not_logged_in.html",{})

    def post(self, request):
        user = request.user
        profile = request.user.profile
        celkove_kalorie, celkove_bilkoviny, celkove_sacharidy, celkove_tuky = (
            0, 0, 0, 0)
        for food_item in profile.food_set.all():
            makroziviny = food_item.potravina.makroziviny
            hmotnost = food_item.hmotnost_g
            multiplier = hmotnost / 100
            celkove_kalorie += makroziviny.kalorie*multiplier
            celkove_bilkoviny += makroziviny.bilkoviny_gramy*multiplier
            celkove_sacharidy += makroziviny.sacharidy_gramy*multiplier
            celkove_tuky += makroziviny.tuky_gramy*multiplier
        denni_udaje = {
            "kalorie":celkove_kalorie,
            "bilkoviny":celkove_bilkoviny,
            "sacharidy":celkove_sacharidy,
            "tuky":celkove_tuky
        }
        if not request.FILES.get("image"):
            last_agent_msg = user.message_set.order_by("-id").first()
            if last_agent_msg and last_agent_msg.text:
                if last_agent_msg.text == "Pro některé potraviny chybí hmotnost v gramech, prosím zadejte hmotnost potravin, abych je mohl zaznamenat do tabulky.":
                    last_user_msg = user.message_set.filter(sender="Vy").order_by("-id").first().text
                else:
                    last_user_msg=None
            else:
                last_user_msg=None
            data = json.loads(request.body)
            message = data.get("message")
            user.message_set.create(text=message, sender="Vy", role="user")

            agent_response = chatbot(message,profile,last_user_msg,denni_udaje)
            user.message_set.create(text=agent_response,
                                sender="Podpora", role="agent")
        else:
            image_file = request.FILES["image"]
            image_bytes = image_file.read()
            mime_type = image_file.content_type
            user.message_set.create(text="[Obrázek]", sender="Vy", role="user")
            agent_response = chatbot_picture(image_bytes=image_bytes,mime_type=mime_type)
            user.message_set.create(text=agent_response,
                                sender="Podpora", role="agent")
            
        return JsonResponse({"response":agent_response})
