from django.conf.urls import url
from . import views

app_name = 'hardware'

urlpatterns = [
    # Get Card List
    url(r'^gcl$', views.gcl),

    # return one time pad for message encryption
    url(r'^getotp/(?P<hardwareId>\w+)$', views.getOTP),

    # challenge server, server should return hash of randomBytes
    # and a password of hadrware with hwid = hadrwareId
    url(r'^c/(?P<hardwareId>\w+)/(?P<randomBytes>[0-9a-f]+)$',
        views.responseToChallenge),

    # m = 'encrypted command message' request from hardware
    url(r'^m/(?P<hardwareId>\w+)/(?P<msg>(?:[A-Za-z0-9-_]{4})*(?:[A-Za-z0-9-_]{2}==|[A-Za-z0-9-_]{3}=)?)$',
        views.processMessage),

    url(r'^$', views.hwList, name='hwlist'),
    url(r'^new$', views.newHw, name='newhw'),
    url(r'^remove/(?P<hw_id>\d+)$', views.rmvHw, name='removehw'),
]
