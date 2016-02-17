from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from chores.models import RecurringChore
from random import randint
from django.contrib.auth.hashers import check_password
import datetime
# These are the models pertaining to USERS and other MANAGEMENT

PASSWORD_SET_LENGTH=4
STEP_CHECK=True
INVITE_TIMEOUT = 120 #seconds

class Card(models.Model):
    key = models.CharField(max_length=14, primary_key=True)
    user = models.OneToOneField(User, blank=True, null=True, unique=True, on_delete=models.SET_NULL)
    is_broken = models.BooleanField(default=False)

    def __str__(self):
        return self.key

    def is_usable(self):
        return ((not self.is_broken) and bool(self.user))


class UserDetail(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    valid_key = models.CharField(max_length=32, blank=True, null=True, default=None)
    valid_key_time = models.DateTimeField(default=timezone.now, blank=True, null=True)
    is_absent = models.BooleanField(default=False)
    is_absent_since = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return ("User detail for %s." % self.user.username)

    def check_validkey(self, valid_key):
        if self.valid_key_time < (timezone.now() - datetime.timedelta(seconds=INVITE_TIMEOUT)):
            self.valid_key = ''
            self.save()
        return (self.valid_key == valid_key)

    def set_absent(self, reason):
        self.is_absent=True
        self.is_absent_since= timezone.now()
        chores= RecurringChore.objects.all()
        for chore in chores:
            if chore.assignee==self.user:
                chore.refuse(reason)
            chore.remove_from_round_robin(self.user)
            chore.save()
        self.save()
        return None

    def set_present(self):
        self.is_absent=False
        self.is_absent_since= timezone.now()
        chores= RecurringChore.objects.all()
        for chore in chores:
            chore.add_randomly_to_round_robin(self.user)
            chore.save()
        self.save()
        return None

    def deactivate(self, reason):
        try:
            self.set_absent(reason)
        except:
            msg='non'
        return None

    def getusername(self):
        return self.user

def validatemail(email):
    try:
        validate_email(email)
        return True
    except:
        return False

def update_password(user, newpswd, oldpswd):
    if len(newpswd)<=PASSWORD_SET_LENGTH:
        return "Error:New Password is too short"
    try:
        user=User.objects.get(username=user)
    except:
        return "Database Connectivity Error: Please Try Again"
    if(check_password(oldpswd, user.password)):
        try:
            user.set_password(newpswd)
            user.save()
            return "Password updated"
        except:
            return "Database Connectivity Error: Please Try Again"
    else:
        return "Error:Password Doesn't Match"

def create_password(user, nwpswd, repswd):
    if len(nwpswd)<=PASSWORD_SET_LENGTH:
        return "Error:Your Password is too short"
    if str(nwpswd)==str(repswd):
        return "Sucess"
    else:
        return "Error:Password Doesn't Match"

def check_email(email):
    if validatemail(email):
        try:
            email_list=User.email.all()
            if email in email_list:
                return False
            else:
                return True
        except:
            return False
    else:
        return False

def check_username(uname):
    try:
        User.objects.get(username=uname)
        return False
    except:
        return True
