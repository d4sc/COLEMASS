from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
import random
import string
from django.core.mail import EmailMessage
# These are the views pertaining to USERS and other MANAGEMENT

@login_required
def settings(request):
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent})

'''
HARDWARE request
'''
def getcardlist(request):
    s = '<%s>' % ''.join([di['card'] for di in Card.objects.values('card')])
    return HttpResponse(s)
