from django.conf.urls import url
from . import views, registrationviews, settingsviews


urlpatterns = [
    url(r'^broken_card/$', settingsviews.cardbroken, name='broken_card'),
    url(r'^update_card/$', settingsviews.cardupdate, name='update_card'),
    url(r'^deactivate/$', settingsviews.deactivate, name='deactivate'),
    url(r'^update_email/$', settingsviews.emailupdate, name='update_email'),
    url(r'^newuser/$', settingsviews.newuser, name='newuser'),
    url(r'^update_password/$', settingsviews.pswdupdate, name='update_password'),
    url(r'^change_username/$', settingsviews.change_username, name='change_username'),
    url(r'^register/(?P<user>.*@\w+.\w+)/(?P<valid_key>\w+)/$', registrationviews.createuserform),
    url(r'^registeruser/$', registrationviews.registeruser),
    url(r'^set_absent/$', settingsviews.set_absent, name='set_absent'),
    url(r'^set_present/$', settingsviews.set_present, name='set_present'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^come_back/$', settingsviews.come_back, name='come_back'),
]
