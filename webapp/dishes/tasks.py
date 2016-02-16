from __future__ import absolute_import
from celery import shared_task, Celery
from django.core.mail import send_mail
from celery import Celery

#celery = Celery(__name__)
#celery.config_from_object(__name__)

@shared_task
def activateChoreTask(dish_tag):
    try:
        from .models import DishLog, DishChore
        log = DishLog.objects.get(pk=dish_tag)
        dish=DishChore.objects.filter(dish=log.dish).exclude(active=False).exists()
        if log.returned_by is None:
            if not dish:
                message = "Automated message: Please put {0} in cupbord".format(log.getDish())
                DishChore.create_new(assignee=log.taken_by, dish=log.dish, message=message)
        else:
            pass
    except:
        pass

@shared_task
def sendemail(title, body, sender, to):
    send_mail(
        subject=title, message=body, from_email=sender, recipient_list=to)
