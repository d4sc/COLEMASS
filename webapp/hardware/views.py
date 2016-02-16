from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from users.models import Card
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def getOTP(request, hardwareId):
    hw = Hardware.objects.get(hwid=hardwareId)
    return HttpResponse('<%s>' % hw.generatePad())


def responseToChallenge(request, hardwareId, randomBytes):
    return HttpResponse('<%s>' % Hardware.generateHash(hardwareId, randomBytes))


def processMessage(request, hardwareId, msg):
    return HttpResponse('<%s>' % Hardware.decryptMessage(hardwareId, msg))


def gcl(request):
    cards = Card.objects.filter(is_broken=False)
    s=''
    for c in cards:
        if len(s) > 0:
            s+=','          
        s+=c.key
    # s = '<%s>' % ','.join([di['key'] for di in cl])
    return HttpResponse('<%s>' % s)


@login_required
def hwList(request):
    return render(request, 'hardware/hwlist.html', {'hws': Hardware.objects.all()})


@login_required
def newHw(request):
    if request.POST:
        txt_hwid = request.POST.get('txt_hwid').strip()
        txt_psw = request.POST.get('txt_sn').strip()
        txt_title = request.POST.get('txt_title').strip()
        import re
        reg = re.compile(r'^[\w\s]+$')
        if reg.search(txt_hwid) is None:
            messages.info(request, 'Please use only alphanumeric symbols and whitespaces for hwid.')
            return render(request, 'hardware/newhw.html')
        if reg.search(txt_psw) is None:
            messages.info(request, 'Please use only alphanumeric symbols and whitespaces for serial number.')
            return render(request, 'hardware/newhw.html')
        if reg.search(txt_title) is None:
            messages.info(request, 'Please use only alphanumeric symbols and whitespaces for title.')
            return render(request, 'hardware/newhw.html')

        from django.db import IntegrityError
        if hwtype_radio is not None:
            if hwtype_radio == '0':
                try:
                    a = Appliance()
                    a.hwid = txt_hwid
                    a.password = txt_psw
                    a.name = txt_title
                    a.generatePad()
                    a.save()
                except IntegrityError:
                    messages.error(request, 'Appliance with this id already exists.')
                    return render(request, 'hardware/newhw.html')  
                else:
                    messages.info(request, a.getName() + ' successfully registered.')
                    return redirect('hardware:hwlist')

            elif hwtype_radio == '1':
                try:
                    h = ItemTracker()
                    h.hwid = txt_hwid
                    h.password = txt_psw
                    h.name = txt_title
                    h.generatePad()
                    h.save()
                except IntegrityError:
                    messages.error(request, 'Item tracker with this id already exists.')
                    return render(request, 'hardware/newhw.html')
                else:
                    messages.info(request, h.getName() + ' successfully registered.')
                    return redirect('hardware:hwlist')

        else:
            messages.info(request, 'Please select hardware type')
            return render(request, 'hardware/newhw.html')

    return render(request, 'hardware/newhw.html')


@login_required
def rmvHw(request, hw_id):
    hw = get_object_or_404(Hardware, pk=hw_id)
    if request.POST:
        hw.delete()
        messages.info(request, '%s was successfully deleted.' %
                      hw.getName())
        return redirect('hardware:hwlist')
    else:
        return render(request, 'hardware/rmvhw.html', {'hw': hw})
