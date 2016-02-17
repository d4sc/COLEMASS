#django package import
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib.auth.models import User
from django.http import *
from django.contrib.auth.hashers import check_password


#importing models from different apps
from chores.models import Chore
from .models import *

#importing python packages
import random
import string

def createuserform(request, user, valid_key):
    '''
    catches incoming email link process it for validity and redirects to register
    user form
    '''
    try:
        userdet=UserDetail.objects.get(user=User.objects.get(username=user))
    except:
         return  HttpResponseForbidden("You have not been invited")
    if userdet.check_validkey(valid_key):
        cards = Card.objects.filter(user=None).exclude(is_broken=True)
        if len(cards)<1:
            return HttpResponseForbidden("Sorry we cannot accept any new Invites at the moment")
        
        return render(request, 'users/register_user.html',{'user':user, 'valid_key':valid_key, 'cards':cards})
    else:
        return HttpResponseForbidden("Your invite has expired")

def registeruser(request):
    '''
    Register new user by updating the temp user model instance, into system
    after through checks on the inputs
    '''
    if not request.POST:
        return HttpResponseServerError("Please try agin later")
    else:
        msgemail=''
        msgpswd=''
        msguser=''
        cards = Card.objects.filter(user=None).exclude(is_broken=True)
        nwuser=User.objects.get(username=request.POST.get('oldusename'))
        ############################EmailCheck##################################
        if not (str(request.POST.get('email').strip()) == (str(request.POST.get('oldusename').strip()))):
            if check_email(request.POST.get('email')):
                nwuser.email=str(request.POST.get('email'))
            else:
                msgemail="Error:Email is not valid"
        elif len((str(request.POST.get('email')).strip()))==0:
            msgemail="Error:Email is a mandatory feild"
        if "Error" in msgemail:
            return render(request, 'users/register_user.html',{'msgemail':msgemail, 'valid_key':request.POST.get('valid_key'),
                'user':request.POST.get('oldusename'), 'cards':cards})


        #############################optional###################################
        if request.POST.get('fname'):
            nwuser.first_name=request.POST.get('fname')
        if request.POST.get('fname'):
            nwuser.last_name=request.POST.get('lname')

        #######################usernamecheck####################################
        if len(str(request.POST.get('nwuname').strip()))==0:
            msguser="Error:Username is mandatory feild"

        elif not check_username(str(request.POST.get('nwuname'))):
            msguser="Error:Sorry Username is not available"

        if "Error" in msguser:
            return render(request, 'users/register_user.html',{'msguser':msguser, 'valid_key':request.POST.get('valid_key'),
                            'user':request.POST.get('oldusename'), 'cards':cards})
        nwuser.username=str(request.POST.get('nwuname')).strip()

        #########################PaswordCheck###################################
        msgpswd=create_password(nwuser, request.POST.get('nwpaswd'), request.POST.get('repaswd'))
        if "Error" in msgpswd:
            return render(request, 'users/register_user.html',{'msgpswd':msgpswd, 'valid_key':request.POST.get('valid_key'),
                    'user':request.POST.get('oldusename'), 'cards':cards})

        nwuser.set_password(request.POST.get('nwpaswd'))
        nwuser.is_active=True
        nwuser.valid_key = ''
        nwuser.save()
        chores=RecurringChore.objects.all()
        for chore in chores:
            order = chore.round_robin.split(',')
            if len(order)==0:
                order.append(str(self.user.pk))
            else:
                order.insert(random.randint(1,len(order)), str(nwuser.pk))
            chore.round_robin = ','.join(order)
            chore.save()
        if request.POST.get('card_id'):
            carddetails = Card.objects.get(key=request.POST.get('card_id'))
            carddetails.user=nwuser
            carddetails.save()
        return redirect('login')
