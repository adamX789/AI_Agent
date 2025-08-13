from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class RegisterForm(UserCreationForm):
    error_messages = {"password_mismatch": "Hesla se neshodují."}
    username = forms.CharField(label="Uživatelské jméno", error_messages={
                               "unique": "Uživatel s tímto jménem už existuje."})
    password1 = forms.CharField(label="Heslo", widget=forms.PasswordInput,)
    password2 = forms.CharField(
        label="Potvrzení hesla", widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ("username", "password1", "password2")