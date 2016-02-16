from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    url(r'^$', views.chores, name="chores"),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^done/$', views.done, name="done"),
    url(r'^nudge/$', views.nudge, name="nudge"),
    url(r'^completion/approve/$', views.completed_chore_approve, name="approve completion"),
    url(r'^completion/challenge/$', views.completed_chore_challenge, name="challenge completion"),
    url(r'^refuse/$', views.refuse, name="refuse"),
    url(r'^refusal/approve/$', views.refusal_approve, name="approve refusal"),
    url(r'^refusal/challenge/$', views.refusal_challenge, name="challenge refusal"),
    url(r'^settings/$', login_required(views.RecurringChoreListView.as_view()), name="settings"),
    url(r'^edit/(?P<pk>[0-9]+)/$', login_required(views.RecurringChoreUpdate.as_view()), name="edit"),
    url(r'^new/$', login_required(views.RecurringChoreCreate.as_view()), name="new"),
    url(r'^delete/(?P<pk>[0-9]+)/$', login_required(views.RecurringChoreDelete.as_view()), name="delete"),
    url(r'^update/$', views.update_active_chores, name="update"),
]
