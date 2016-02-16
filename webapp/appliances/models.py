from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.utils import timezone

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
                email = EmailMessage("Appliance chore assignment",
                   "Hi %s,\n\nYou left the appliance \"%s\" in unsatisfactory condition. Please fix it." % (self.assignee.username, self.appliance.name),
                   to=[self.assignee.email]
                   )
                email.send()
                message = "{0} has been notified to complete the chore \"{1}\".".format(usr.username, self.name)
        else:
            message = super(ApplianceChore, self).report()
        return message
