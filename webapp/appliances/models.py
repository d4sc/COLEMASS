from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.utils import timezone

from colemass import settings
from users.models import Card
from chores.models import Chore
from hardware.models import Hardware

# These are the models pertaining to APPLIANCES

class Appliance(Hardware):
    is_in_use = models.BooleanField(default=False)
    last_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    current_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="current")

    def logout(self):
        if (self.is_in_use):
            self.is_in_use = False
            self.last_user = self.current_user
            self.current_user = None
            self.save()

    def login(self, userCard):
        try:
            card = Card.objects.get(key=userCard)
            # bad user card id
            if not card.is_usable():
                return '-11'
        except ObjectDoesNotExist:
            # bad user card id
            return '-11'
        usr = Card.objects.get(key=userCard).user
        ud = usr.userdetail
        if (ud.is_absent):
            ud.set_present()
        self.current_user = usr
        self.is_in_use = True
        self.save()

    def report(self):
        message = self.appliancechore.report()
        return message

    def getStatus(self):
        if (self.is_in_use):
            return True
        else:
            return False


class ApplianceChore(Chore):
    appliance = models.OneToOneField(Appliance, on_delete=models.CASCADE)

    def complete(self, user):
        ''' General chore completion + inactivation. '''
        super(ApplianceChore, self).complete(user)
        self.active = False
        self.save()

    def refuse(self, reason):
        ''' General chore refusal + inactivation. '''
        super(ApplianceChore, self).refuse(reason)
        self.active = False
        self.save()

    def report(self):
        ''' Activates chore if necessary, otherwise nudges/logs infraction. '''
        message = ""
        if not self.active:
            usr = self.appliance.last_user
            ud = usr.userdetail
            if(ud.is_absent):
                Infraction.objects.create(chore=self, user=usr)
                message = "{0} is absent. An infraction was logged.".format(usr.username)
            else:
                self.assigned_time=timezone.now()
                self.active = True
                self.assignee = usr
                self.reset_nudges()
                self.save()

                from dishes.tasks import sendemail
                title = "[COLEMASS] Appliance chore assignment"
                body = "Dear {0},\n\nYou left the appliance {1} in an unsatisfactory condition."  \
                " Please fix it".format(self.assignee.username, self.appliance)
                sender = getattr(settings, "EMAIL_HOST_USER", 'colemass')
                to = [self.asignee.email, ]
                sendemail(title, body, sender, to)

                message = "{0} has been notified to complete the chore \"{1}\".".format(usr.username, self.name)
        else:
            message = super(ApplianceChore, self).report()
        return message
