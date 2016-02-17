from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

from .models import UserDetail, Card

class CreateUserForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class SelectCardForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    card = forms.ModelChoiceField(queryset=Card.objects.filter(user__isnull=True, is_broken=False), required=True)
        
# class UserDefaultForm(forms.ModelForm):
    # username = forms.CharField(required=True)
    # email = forms.EmailField(required=True)

    # class Meta:
        # model = User
        # fields = ("username", "email")
    
    # def clean_username(self):
        # username = self.cleaned_data['username']
        # if username == "default":
            # raise forms.ValidationError("Please choose a username.")
        # return username
        
# class UserPasswordDefaultForm(forms.Form):
    # password = forms.CharField(required=True, widget=forms.PasswordInput)
    # password2 = forms.CharField(required=True, widget=forms.PasswordInput)
    
    # def clean_password2(self):
        # password = self.cleaned_data['password']
        # password2 = self.cleaned_data['password2']
        # if password != password2:
            # raise forms.ValidationError("Passwords do not match.")
        # return password