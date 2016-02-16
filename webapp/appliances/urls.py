from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.appliances, name='appliances'),
    url(r'report/$', views.appliance_report, name='report'),
    url(r'getappliancestatus/(?P<hardwareId>\w+)/$', views.getApplianceStatus),
    url(r'getusername/(?P<cardID>\w+)/$', views.getUserName),
]
