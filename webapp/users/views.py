from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from .models import *
from .forms import CreateUserForm, SelectCardForm
#from django.contrib.auth.forms import UserChangeForm, UserCreationForm, SetPasswordForm
import random
import string
# These are the views pertaining to USERS and other MANAGEMENT

def start(request):
    if User.objects.all().count() > 0:
        return redirect('login')
    else:
        return redirect('setup')

def setup(request):
    if User.objects.all().count() > 0:
        return redirect('login')
    elif request.method == 'POST':
        form = CreateUserForm(request.POST)
        try:
            card = Card.objects.get(key=request.POST.get('card_key'))
        except Card.DoesNotExist:
            card = None
            messages.error(request, "The card you have chosen does not exist.")
        if form.is_valid() and card:
            if card.user is not None:
                messages.error(request, "The card you have chose has already been assigned.")
            elif form.cleaned_data['password'] != request.POST.get('password2'):
                messages.error(request, "Passwords do not match.")
            else:
                user = User.objects.create_user(**form.cleaned_data)
                UserDetail.objects.create(user=user)
                card.user = user
                card.save()
                return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = CreateUserForm()
    cards = Card.objects.filter(user__isnull=True, is_broken=False)
    return render(request, 'users/setup.html', {'form': form, 'cards': cards})

@login_required
def settings(request):
    cards = Card.objects.filter(user__isnull=True, is_broken=False)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent})

# def register(request):
    # if request.method == 'POST':
        # password_form = UserPasswordDefaultForm(request.POST)
        # username_form = UserDefaultForm(request.POST)
        # if password_form.is_valid() and username_form.is_valid():
            # username_form.save()
            # username_form.user.set_password(password_form.cleaned_data['password'])
            # username_form.user.save()
            # return redirect('logout')
        # else:
            # for error in password_form.errors.values():
                # messages.error(request, error)
                # password_form = SetPasswordForm(user=request.user)
            # for error in username_form.errors.values():
                # messages.error(request, error)
                # username_form = UserDefaultForm(instance=request.user)
    # else:
        # username_form = UserDefaultForm(instance=request.user)
        # password_form = UserPasswordDefaultForm()
    # return render(request, 'users/default_user.html', {'password_form': password_form, 'username_form': username_form})
        

'''
HARDWARE request
'''
def getcardlist(request):
    s = '<%s>' % ''.join([di['card'] for di in Card.objects.values('card')])
    return HttpResponse(s)
