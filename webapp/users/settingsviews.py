from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth import views as auth_views
from colemass import settings

import random
import string, sys

from .models import *
from datetime import datetime

@login_required
def change_username(request):
    new_username = request.POST.get('new_username')
    if request.user.username == "default":
        user = request.user
        if check_username(new_username) and new_username:
            user.username = new_username
            user.save()
        else:
            messages.error(request, "Username already exists.")
            return redirect('users:settings')
    else:
        messages.error(request, "You may not change your username.")
        return redirect('users:settings')
    return redirect('login')

@login_required
def newuser(request):
    '''
    Checks for the validity of the email.
    Checks if space is available for more users
    Creates a user with email as the username and also creates a valid key which
    is used for security purpose.
    '''
    try:
        cards = Card.objects.filter(user=None).exclude(is_broken=True)
        if ((request.method=='POST') & (validatemail(request.POST.get('newuser')))) & (len(cards)>0):
            if not (User.objects.filter(email=request.POST.get('newuser')).exists()) or not (User.objects.filter(username=request.POST.get('newuser')).exists()):
                randstring = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
                try:
                    nwuser = User.objects.create_user(request.POST.get('newuser'), request.POST.get('newuser'))
                    nwuser.is_active=False
                    nwuser.save()
                    UserDetail.objects.create(user=nwuser)
                except:
                    messages.error(request, "Database Connectivity Error:Please try again.")
                try:
                    userdet=UserDetail.objects.get(user=nwuser)
                    userdet.valid_key=randstring
                    userdet.valid_key_time = timezone.now()
                    userdet.save()
                except:
                    nwuser.delete()
                    messages.error(request, "Database Connectivity Error:Please try again.")
                try:
                    resetlink='http://'+request.get_host()+'/user/register/'+request.POST.get('newuser')+'/'+randstring

                    from dishes.tasks import sendemail
                    title = "[COLEMASS] Invitation"
                    body = "Hi {0},\n\nYou have been invited to join COLEMASS by {1}. Please follow the link to join our network and set your COLEMASS password.\n{2} \nRegards,\nColemass Team".format(request.POST.get('newuser'), request.user, resetlink)
                    sender = getattr(settings, "EMAIL_HOST_USER", 'colemass')
                    to = [request.POST.get('newuser'), ]
                    sendemail(title, body, sender, to)
                    j='09'
                    messages.success(request, "Invitation sent.")
                except:
                    nwuser.delete()
                    messages.error(request, "Error in sending email Please try again later.")
            else:
                messages.error(request, "User has already been invited")
        else:
            if not (validatemail(request.POST.get('newuser'))):
                messages.error(request, "Please provide a valid email address.")
            elif len(cards)<1:
                messages.error(request, "There are not enough cards for a new user.")
            else:
                messages.error(request, "Error.")
    except:
        messages.error(request, "Unknown Error: Please try again")
    return redirect('users:settings')


@login_required
def cardupdate(request):
    '''
    Updates card for the user with available cards
    '''
    if request.method=='POST':
        try:
            new_card = Card.objects.get(key=request.POST.get('card_id'))
        except Card.DoesNotExist:
            new_card = None
            messages.error(request, "The card you have chosen does not exist.")
        if new_card:
            try:
                old_card = Card.objects.get(user=request.user)
                old_card.user = None
                old_card.save()
            except Card.DoesNotExist:
                messages.warning(request, "You did not originally have a card.")
            new_card.user = request.user
            new_card.save()
            messages.success(request, "You successfully changed card.")
    return redirect('users:settings')

@login_required
def cardbroken(request):
    '''
    Reports your current card as broken
    '''
    if request.method=='POST':
        try:
            broken_card = Card.objects.get(user=request.user)
            broken_card.user = None
            broken_card.is_broken = True
            broken_card.save()
            messages.warning(request, "Your card has been reported as broken. Don't forget to choose a new one!")
        except Card.DoesNotExist:
            messages.error(request, "There is no card assigned to you.")
    return redirect('users:settings')

@login_required
def change_password(request):
    '''
    Updates user password
    '''
    if not check_password(request.POST.get('old_password'), request.user.password):
        messages.error(request, "Your old password is incorrect.")
    elif not request.POST.get('new_password1') == request.POST.get('new_password2'):
        messages.error(request, "The new password fields didn't match")
    else:
        request.user.set_password(request.POST.get('new_password1'))
        request.user.save()
        messages.success(request, "Your password has been updated.")
    return redirect('users:settings')

@login_required
def emailupdate(request):
    '''
    Updates Email of the user
    '''
    if request.method=='POST':
        if check_password(request.POST.get('password'), request.user.password):
            request.user.email = request.POST.get('new_email')
            request.user.save()
            messages.success(request, "Your email has been updated.")
        else:
            messages.error(request, "You must provide your password to change your email.")
    return redirect('users:settings')

@login_required
def set_absent(request):
    '''
    Sets the user as absent at the same time removing him from all the recurring chores
    '''
    reason = request.POST.get('reason')
    reason = reason.strip() if reason else ''
    if reason:
        user_detail = UserDetail.objects.get(user=request.user)
        user_detail.set_absent(reason)
    else:
        messages.error(request, "You must provide a reason for your absence.")
    return redirect('users:settings')

@login_required
def set_present(request):
    '''
    Sets the user as present at the same time adding him at random in all the recurring chores
    '''
    if(check_password(request.POST.get('pswd'), User.objects.get(username=request.user).password)):
        try:
            user_det=get_object_or_404(UserDetail, user=request.user)
            user_det.set_present()
            return redirect('users:settings')
        except:
            msgpres="Database Connectivity Error: Please Try again later"
            print(sys.exc_info()[0])
    else:
        msgpres="Please Check the password you have provided"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgpres':msgpres})

@login_required
def come_back(request):
    request.user.userdetail.set_present()
    return redirect('mycolemass')

@login_required
def deactivate(request):
    if(check_password(request.POST.get('pswd'), request.user.password)):
        user_det=get_object_or_404(UserDetail, user=request.user)
        user_det.deactivate(request.POST.get('reason'))
        request.user.is_active=False
        request.user.save()
        if not User.objects.filter(is_active=True).count():
            for user in User.objects.all():
                user.delete()
        return redirect('logout')
    else:
        messages.error(request, "The password you entered is incorrect.")
    return redirect('users:settings')
