"""colemass URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.template import RequestContext
from django.contrib.auth import views as auth_views

from chores.views import mycolemass, stats

authentication_urls = [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    url(r'^password_reset/$', auth_views.password_reset, {'post_reset_redirect': 'login'}, name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {'post_reset_redirect': 'login'}, name='password_reset_confirm'),
]

urlpatterns = [
    url(r'^$', mycolemass, name="mycolemass"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^dishes/', include('dishes.urls', namespace="dishes")),
    url(r'^appliances/', include('appliances.urls', namespace="appliances")),
    url(r'^stats/', stats, name="stats"),
    url(r'^chores/', include('chores.urls', namespace="chores")),
    url(r'^user/', include('users.urls', namespace="users")),
    url(r'^hw/', include('hardware.urls', namespace="hardware")),
] + authentication_urls

def handler404(request):
    response = render_to_response('error404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('error404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response

def handler403(request):
    response = render_to_response('error404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response
