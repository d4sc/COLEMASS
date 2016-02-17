
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113

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
        hwtype_radio = request.POST.get('hwtype')
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
                from appliances.models import Appliance, ApplianceChore
                try:
                    a = Appliance()
                    a.hwid = txt_hwid
                    a.password = txt_psw
                    a.name = txt_title
                    a.generatePad()
                    a.save()

                    ac = ApplianceChore()
                    ac.appliance =  a
                    ac.name = a.name + " Chore"
                    ac.save()

                except IntegrityError:
                    messages.error(request, 'Appliance with this id already exists.')
                    return render(request, 'hardware/newhw.html')
                else:
                    messages.info(request, a.getName() + ' successfully registered.')
                    return redirect('hardware:hwlist')

            elif hwtype_radio == '1':
                from dishes.models import ItemTracker
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
