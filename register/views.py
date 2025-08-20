from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views import View
from .forms import RegisterForm
from user_profile.models import Profile

# Create your views here.


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "register.html", {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(uzivatel=user)
            login(request, user)
            return redirect('chat')
        return render(request, "register.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("chat")
