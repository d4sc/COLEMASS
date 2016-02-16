from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *

from users.models import Card

# These are the views pertaining to APPLIANCES

@login_required
def appliances(request):
    appliances = Appliance.objects.all()
    return render(request, 'appliances/appliances.html', {'appliances': appliances})

@login_required
def appliance_report(request):
    appliance = get_object_or_404(Appliance, pk=request.POST.get('pk'))
    message = appliance.report()
    messages.info(request, message)
    return redirect('appliances:appliances')

def getUserName(request, cardID):
    try:
        cd = Card.objects.get(key=cardID)
        usr = cd.user
        s = "<"+str(usr)+">"
        return HttpResponse("<"+str(usr)+">")
    except Card.DoesNotExist:
        return HttpResponse("card does not exist")


'''
APPLMAN
'''
def getApplianceStatus(request,hardwareId):
    try:
        ap = Appliance.objects.get(hwid=hardwareId)
    except Appliance.DoesNotExist:
        return HttpResponse("appliance does not exist")
    if ap.getStatus():
        return HttpResponse("<1>")
    else:
        return HttpResponse("<0>")
