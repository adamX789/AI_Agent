import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from .main import chatbot,chatbot_picture
from .models import *
from user_profile.models import Profile
from datetime import datetime,timedelta
from dotenv import load_dotenv
from google.cloud import speech_v1p1beta1 as speech
import io
load_dotenv()

zaznamy={}
denni_zaznamy={}
MAX_REQUESTS = 10
TIME = 60
DAILY_MAX_REQUESTS = 100
DAILY_TIME = 60*60*24

def convert_audio_to_text(audio_file):
    client = speech.SpeechClient()
    content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="cs-CZ",
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        return result.alternatives[0].transcript
    return ""


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
        ip_adresa = request.META.get("REMOTE_ADDR")
        ted = datetime.now()
        if ip_adresa in zaznamy:
            zaznamy[ip_adresa] = [t for t in zaznamy[ip_adresa] if ted - t <= timedelta(seconds=TIME)]
        if ip_adresa in denni_zaznamy:
            denni_zaznamy[ip_adresa] = [t for t in zaznamy[ip_adresa] if ted - t <= timedelta(seconds=DAILY_TIME)]
        if ip_adresa in zaznamy and len(zaznamy[ip_adresa]) > MAX_REQUESTS:
            return JsonResponse({"response":"Překročil jste povolený limit pro odesílaní zpráv, zkuste to prosím za minutu znovu!"},status=429)
        if ip_adresa in denni_zaznamy and len(denni_zaznamy[ip_adresa]) > DAILY_MAX_REQUESTS:
            return JsonResponse({"response":"Překročil jste denní povolený limit pro odesílaní zpráv, zkuste to prosím znovu za 24 hodin!"},status=429)
        if ip_adresa not in zaznamy:
            zaznamy[ip_adresa] = []
        if ip_adresa not in denni_zaznamy:
            denni_zaznamy[ip_adresa] = []
        zaznamy[ip_adresa].append(ted)
        denni_zaznamy[ip_adresa].append(ted)
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
        historie_zprav = user.message_set.all().order_by("id")[:10]
        last_agent_msg = user.message_set.order_by("-id").first()
        last_agent_msg_text = last_agent_msg.text if last_agent_msg else None
        if request.FILES.get("audio"):
            audio_file = request.FILES["audio"]
            message = convert_audio_to_text(audio_file=audio_file)
            print(message)
            user.message_set.create(text="Posíláte hlasovou zprávu", sender="Vy", role="user")
            if message == "":
                agent_response="Z hlasové zprávy jsem nebyl schopen rozpoznat dotaz."
            else:
                agent_response = chatbot(query=message,profile=profile,last_agent_msg=last_agent_msg_text,denni_udaje=denni_udaje,historie=historie_zprav)
            user.message_set.create(text=agent_response,
                                sender="Podpora", role="agent")
        elif not request.FILES.get("image"):
            data = json.loads(request.body)
            message = data.get("message")
            user.message_set.create(text=message, sender="Vy", role="user")

            agent_response = chatbot(message,profile,last_agent_msg_text,denni_udaje,historie=historie_zprav)
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
