from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import TextInput, CharField, Textarea

class RegisterForm(UserCreationForm):
    first_name = CharField(widget=TextInput(attrs={'autofocus': 'autofocus'}))
    class Meta:
        model = User
        fields = ["first_name", "last_name", "mobile", "city", "email", "password1", "password2"]
