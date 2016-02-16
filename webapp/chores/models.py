from django.db import models
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone
from django.core.urlresolvers import reverse

import datetime, random

# These are the models pertaining to CHORES

NUDGE_DELAY = 10 #seconds
INFRACTION_THRESHOLD = 3 #nudges
STATISTICS_PERIOD = 30 #days

def random_order():
    users = User.objects.filter(is_active=True, userdetail__is_absent=False)
    return ','.join([str(user.pk) for user in sorted(users, key=lambda k: random.random())])

def random_user():
    users = User.objects.filter(is_active=True, userdetail__is_absent=False)
    return random.choice(users)

def a_long_time_ago():
    return timezone.now() - datetime.timedelta(days=100)


class Chore(models.Model):
    name = models.CharField(max_length=50)
    assignee = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    assigned_time = models.DateTimeField(default=timezone.now)
    nudges = models.SmallIntegerField(default=0)
    last_nudge = models.DateTimeField(default=a_long_time_ago)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['nudges', '-assigned_time']

    def __str__(self):
        return self.name

    def reset_nudges(self):
        ''' Resets nudges. '''
        self.nudges = 0
        self.last_nudge = a_long_time_ago()

    def assign(self, user):
        ''' Assigns chore to use. '''
        self.reset_nudges()
        self.active = True
        self.assignee = user
        self.assigned_time = timezone.now()
        self.save()

    def complete(self, user):
        ''' Completes assigned chore. '''
        # confirm previous unconfirmed completed chore
        for chore in CompletedChore.objects.filter(chore=self, confirmed=False):
            chore.confirmed = True
            chore.save()
        # confirm previous unconfirmed refused chore
        for chore in RefusedChore.objects.filter(chore=self, confirmed=False):
            chore.confirmed = True
            chore.save()
        # create new completed chore
        CompletedChore.objects.create(chore=self, user=user, nudges=self.nudges)

    def refuse(self, reason):
        ''' Refuses assigned chore. '''
        # confirm previous unconfirmed refused chore
        for chore in RefusedChore.objects.filter(chore=self, confirmed=False):
            chore.confirmed = True
            chore.save()
        # log refused chore
        RefusedChore.objects.create(chore=self, user=self.assignee, reason=reason)

    def report(self):
        '''
        Nudges assignee, possibly logs infraction. Emails relevant user.
        Returns a message to be displayed in the web app
        '''
        message = "It is too early to nudge {0} for \"{1}\"".format(self.assignee.username, self.name)
        if (timezone.now() - self.last_nudge) > datetime.timedelta(seconds=NUDGE_DELAY):
            # anti spam check
            self.nudges += 1
            self.last_nudge = timezone.now()
            self.save()
            if (self.nudges % INFRACTION_THRESHOLD == 0) and not (self.nudges == 0):
                # every three reports, log an infraction
                Infraction.objects.create(chore=self, user=self.assignee)
                email = EmailMessage("Infraction",
                    "Hi {0},\n\nAn infraction has been logged " \
                    "for not completing \"{1}\".".format(self.assignee.username, self.name),
                    to=[self.assignee.email]
                    )
                email.send()
                message = "{0} was nudged for \"{1}\" and an infraction was logged.".format(self.assignee.username, self.name)
            else:
                email = EmailMessage("Friendly reminder",
                    "Hi {0},\n\nYou have been nudged {1} time{2} "
                    "to complete the chore \"{3}\".".format(self.assignee.username,
                        self.nudges,
                        ('s','')[self.nudges==1],
                        self.name),
                    to=[self.assignee.email]
                    )
                email.send()
                message = "{0} was nudged for \"{1}\".".format(self.assignee.username, self.name)
        return message

class RecurringChore(Chore):
    round_robin = models.CharField(max_length=50, default=random_order, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('chores:edit', kwargs={'pk': self.pk})
     
    def get_round_robin(self):
        ''' Round robin as list of int '''
        if self.round_robin:
            return [int(i) for i in self.round_robin.split(',')]
        else:
            return []

    def set_round_robin(self, id_list):
        ''' Updates round robin from list of int '''
        self.round_robin = ','.join([str(i) for i in id_list])
        
    def remove_from_round_robin(self, user):
        pk = user.pk
        order = self.get_round_robin()
        if pk in order:
            order.remove(pk)
        self.set_round_robin(order)
    
    def add_randomly_to_round_robin(self, user):
        pk = user.pk
        order = self.get_round_robin()
        if order:
            order.insert(random.randint(1,len(order)),pk)
        else:
            order = [pk]
        self.set_round_robin(order)
        
    def send_to_end(self, user):
        ''' Sends user at the end of round-robin. '''
        order = self.get_round_robin()
        order.remove(user.pk)
        order.append(user.pk)
        self.set_round_robin(order)
        super(RecurringChore, self).assign(User.objects.get(pk=order[0]))

    def complete(self, user):
        ''' Base chore completion + round-robin reassignment. '''
        super(RecurringChore, self).complete(user)
        self.send_to_end(user)
        email = EmailMessage("Chore assignment",
            "Hi %s,\n\nThe chore \"%s\" has been assigned to you." % (self.assignee.username, self.name),
            to=[self.assignee.email]
            )
        email.send()

    def refuse(self, reason):
        ''' Base chore refusal + round-robin reassignment. '''
        refusing_user = self.assignee
        super(RecurringChore, self).refuse(reason)
        self.send_to_end(self.assignee)
        print(self.assignee.username)
        print(self.name)
        print(refusing_user.username)
        email = EmailMessage("Chore assignment",
            "Hi {0},\n\nThe chore \"{1}\" has been refused by {2} and it has been assigned to you." +
            "\nYou can challenge this assignment in your Colemass.".format(self.assignee.username, self.name, refusing_user.username),
            to=[self.assignee.email]
            )
        email.send()


class CompletedChore(models.Model):
    chore = models.ForeignKey(Chore)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    nudges = models.SmallIntegerField()
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__ (self):
        return self.chore.name

    def confirm(self):
        ''' Confirms completion log entry. '''
        self.confirmed = True
        self.save()

    def challenge(self):
        '''
        Reassigns the chore to the user claiming the completion,
        logs an infraction, deletes completion log entry.
        '''
        self.chore.assign(self.user)
        Infraction.objects.create(user=self.user, chore=self.chore)
        self.delete()


class RefusedChore(models.Model):
    chore = models.ForeignKey(Chore)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=140)
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__ (self):
        return self.chore.name

    def confirm(self):
        ''' Confirms refusal log entry. '''
        self.confirmed = True
        self.save()

    def challenge(self):
        '''
        Reassigns the chore to the user refusing it,
        logs an infraction, deletes refusal log entry.
        '''
        self.chore.assign(self.user)
        Infraction.objects.create(user=self.user, chore=self.chore)
        self.delete()


class Infraction(models.Model):
    user = models.ForeignKey(User)
    chore = models.ForeignKey(Chore)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__ (self):
        return self.user.username
    
    def is_recent(self):
        return (timezone.now() - self.date) < datetime.timedelta(days=STATISTICS_PERIOD)
    is_recent.boolean = True
