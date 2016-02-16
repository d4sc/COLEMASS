from django.conf.urls import url
from . import views

app_name = 'dishes'

urlpatterns = [
    url(r'^$', views.dishList, name='dishlist'),

    url(r'^mine$', views.myDishes, name='mydishes'),

    url(r'^editdish$', views.editDish, name='editdish'),

    url(r'^log$', views.dishLog, name='dishlog'),

    url(r'^new$', views.newDish, name='newdish'),

    url(r'^remove/(?P<dish_id>\d+)$', views.rmvDish, name='rmvdish'),

    url(r'^newchore$', views.newDishChore, name='newdishchore'),
]
