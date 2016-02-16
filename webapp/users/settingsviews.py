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
                    msgcreuser="Database Connectivity Error:Please try again"
                try:
                    userdet=UserDetail.objects.get(user=nwuser)
                    userdet.valid_key=randstring
                    userdet.valid_key_time = timezone.now()
                    userdet.save()
                except:
                    nwuser.delete()
                    msgcreuser="Database Connectivity Error:Please try again"
                try:
                    resetlink='http://'+request.get_host()+'/register/'+request.POST.get('newuser')+'/'+randstring
                    message="Hi %s,\n\nYou have been invited to join COLEMASS by %s. Please follow the link to join our network and set your COLEMASS password.\n%s \nRegards,\nColemass Team" % (request.POST.get('newuser'), request.user, resetlink)
                    email = EmailMessage("COLEMASS:Invite", message,  to=[request.POST.get('newuser')])
                    email.send()
                    j='09'
                    msgcreuser="Invite Sent"
                except:
                    nwuser.delete()
                    msgcreuser="Error in sending email Please try again later"
            else:
                msgcreuser="User has already been invited"
        else:
            if not (validatemail(request.POST.get('newuser'))):
                msgcreuser="Please provide a valide email ID"
            elif len(cards)<1:
                msgcreuser="Sorry colemass has reached its limit\nPlease add new cards to invite people"
            else:
                raise HttpResponseServerError("Please try agin later")
    except:
        msgcreuser="Unknown Error: Please try again"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html',{'cards': cards, 'is_absent':is_absent, 'msgcreuser':msgcreuser, })


@login_required
def cardupdate(request):
    '''
    Updates card for the user with available cards
    '''
    if request.method=='POST':
        try:
            carddetails = Card(key=request.POST.get('card_id'))
            carddetails.user=request.user
            carddetails.save()
            msgcard="Card Changed"
        except:
            msgcard="Database Connectivity Error: Please Try Again"
    else:
        msgcard="Unknow Error: Please Try Again"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgcard':msgcard})

@login_required
def pswdupdate(request):
    '''
    Updates user password
    '''
    if request.method=='POST':
        try:
            msgpaswd=update_password(request.user, request.POST.get('newpswd'), request.POST.get('oldpswd'))
        except:
            msgpaswd="Unknown Error:Please try again"
    else:
        return redirect('users:settings')
    if 'Error' in msgpaswd:
        cards = Card.objects.filter(user=None).exclude(is_broken=True)
        is_absent= UserDetail.objects.get(user=request.user).is_absent
        return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgpaswd':msgpaswd})
    else:
        return redirect('login')


@login_required
def emailupdate(request):
    '''
    Updates Email of the user
    '''
    if request.method=='POST':
        try:
            userdetails = User.objects.get(username=request.user)
        except:
            msgemail="Database Connectivity Error: Please Try Again"
        if(check_password(request.POST.get('pswd'), userdetails.password)):
            try:
                userdetails.email=request.POST.get('newemail')
                msgemail="Email Changed Sucessfully"
                userdetails.save()
            except:
                msgemail="Database Connectivity Error: Please Try Again"
    else:
        msgemail="Unknown Error: Please Try Again"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user)
    is_absent=is_absent.is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgemail':msgemail})

@login_required
def cardbroken(request):
    '''
    Reports your current card as broken
    '''
    if request.method=='POST':
        try:
            if Card.objects.filter(user=request.user).exists():
                carddetails = Card.objects.get(user=request.user)
                carddetails.user=None
                carddetails.is_broken=True
                msgcard="Card has been reported please choose a new one"
                carddetails.save()
            else:
                msgcard="You currently don't have a card assigned you"

        except:
            msgcard="Database Connectivity Error: Please Try Again"
    else:
        msgcard="Unknow Error: Please Try Again"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgcard':msgcard})

@login_required
def set_absent(request):
    '''
    Sets the user as absent at the same time removing him from all the reccuring chores
    '''
    if(check_password(request.POST.get('pswd'), User.objects.get(username=request.user).password)):
        user_det=get_object_or_404(UserDetail, user=request.user)
        user_det.set_absent(request.POST.get('reason'))
        return redirect('users:settings')
        msgpres="Database Connectivity Error: Please Try again later"
        msgpres= str(sys.exc_info())
    else:
        msgpres="Please Check the password you have provided"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgpres':msgpres})

@login_required
def set_present(request):
    '''
    Sets the user as present at the same time adding him at random in all the reccuring chores
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
    if(check_password(request.POST.get('pswd'), User.objects.get(username=request.user).password)):
        user_det=get_object_or_404(UserDetail, user=request.user)
        user_det.deactivate(request.POST.get('reason'))
        users=get_object_or_404(User, username=request.user)
        users.is_active=False
        users.save()
        return redirect('logout')

        msgpres="Database Connectivity Error: Please Try again later"
    else:
        msgpres="Please Check the password you have provided"
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent, 'msgpres':msgpres})
