from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from colemass import settings
from django.utils import timezone

from hardware.models import Hardware
from chores.models import *
from .tasks import activateChoreTask

DELAY_BEFORE_REMINDING = 10 #seconds

class ItemTracker(Hardware):
    """docstring for ItemTracker"""

    @staticmethod
    def takeItemOut(dishTagList, userCard):
        from users.models import Card
        dishes = Dish.objects.filter(tag__in=dishTagList)
        try:
            card = Card.objects.get(key=userCard)
            # bad user card id
            if not card.is_usable():
                return '-11'
        except ObjectDoesNotExist:
            # bad user card id
            return '-11'

        cc = ''

        if len(dishes) > 0:

            ud = Card.objects.get(key=userCard).user
            for dish in dishes:
                t = timezone.now()
                dish.updateStatus(ud, t)
                dish.save()
                cc += '{0} assigned to {1}, '.format(
                    dish.getTitle(), str(ud))

                # add entry in the log
                dl=DishLog.log(dish, ud, t)
                activateChoreTask.apply_async([dl.id,], countdown=15)

        # if there are unregistered tags
        if len(dishTagList) > len(dishes):
            # remove existing dish tags from dishTagList
            for aDish in dishes:
                dishTagList.remove(aDish.tag)

            # remove remaining tags from UnregisteredDish model
            for utag in dishTagList:
                try:
                    UnregisteredDish.objects.get(tag=utag).delete()
                    cc += 'removed temporary dish %s, ' % utag
                except ObjectDoesNotExist:
                    cc += 'unrecognized dish %s, ' % utag

        return cc

    @staticmethod
    def putItemIn(dishTagList, userCard):
        from users.models import Card
        dishes = Dish.objects.filter(tag__in=dishTagList)
        try:
            card = Card.objects.get(key=userCard)
            # bad user card id
            if not card.is_usable():
                return '-11'
        except ObjectDoesNotExist:
            # bad user card id
            return '-11'

        cc = ''

        if len(dishes) > 0:

            ud = Card.objects.get(key=userCard).user
            for dish in dishes:
                t = timezone.now()
                dish.updateStatus(None, t)
                dish.save()
                cc += '%s is put in cupbpard, ' % dish.getTitle()

                DishLog.log(dish, ud, t)

        # if there are unregistered tags
        if len(dishTagList) > len(dishes):
            # remove existing dish tags from dishTagList
            for aDish in dishes:
                dishTagList.remove(aDish.tag)

            # add remaining tags into UnregisteredDish model
            for utag in dishTagList:
                UnregisteredDish.addDish(utag)
                cc += 'temporarily registered ' + utag

        return cc


class Item(models.Model):
    title = models.CharField(max_length=30, blank=True, null=True)
    tag = models.CharField(max_length=20, unique=True)

    def getTitle(self):
        return self.title

    def setTitle(self, newTitle):
        self.title = newTitle

    def getTag(self):
        return self.tag

    def setTag(self, newTag):
        # regex for checking: ^[0-9A-F]{1,14}$
        self.tag = newTag

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class Dish(Item):
    """docstring for Dish"""
    assignee = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL)
    update_time = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "dishes"

    def isTakenOut(self):
        return (not self.assignee is None)
    isTakenOut.boolean = True
    isTakenOut.short_description = 'Is taken out?'

    def getAssignee(self):
        return self.assignee

    def updateStatus(self, user, time):
        if self.assignee is None:
            if user is not None:
                self.assignee = user
                self.update_time = time
        else:
            if user is None:
                self.assignee = None
                self.update_time = time

    def getLastUpdateTime(self):
        return self.update_time

    @staticmethod
    def getUserDishes(user):
        return Dish.objects.filter(assignee=user)


class UnregisteredDish(Item):
    detection_time = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "unregistered dishes"

    @staticmethod
    def addDish(newTag):
        try:
            udish = UnregisteredDish.objects.get(tag=newTag)
            udish.detection_time = timezone.now()
            udish.save()
        except ObjectDoesNotExist:
            udish = UnregisteredDish()
            udish.setTag(newTag)
            udish.setTitle(newTag)
            udish.detection_time = timezone.now()
            udish.save()

    # add dish to Dish model
    def registerDish(self, newTitle):
        newdish = Dish()
        newdish.setTag(self.getTag())
        newdish.setTitle(newTitle)
        newdish.updateStatus(None, self.getDetectionTime())
        newdish.save()
        self.delete()

    def getDetectionTime(self):
        return self.detection_time


class DishLog(models.Model):
    """docstring for DishLog"""
    dish = models.ForeignKey(Dish,
        related_name='usage_log', on_delete=models.CASCADE)
    taken_by = models.ForeignKey(User,
        related_name='taken_dishes_log', on_delete=models.CASCADE)
    taken_time = models.DateTimeField()
    returned_by = models.ForeignKey(User,
        related_name='returned_dishes_log', on_delete=models.CASCADE, null=True, blank=True)
    returned_time = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def log(dish, user, time):
        try:
            nl = DishLog.objects.filter(dish=dish).latest('taken_time')
            if nl.returned_by is None:
                nl.returned_by = user
                nl.returned_time = time
                nl.save()
            else:
                nl = DishLog.objects.create(dish=dish, taken_by=user, taken_time=time)
        except ObjectDoesNotExist:
            nl = DishLog.objects.create(dish=dish, taken_by=user, taken_time=time)
        return nl

    @staticmethod
    def getDishUsageLog(dish_id, nn):
        return DishLog.objects.filter(dish=dish_id).order_by('-taken_time')[:nn]

    def getDish(self):
        return self.dish

    def getTakeUser(self):
        return self.taken_by

    def getTakeTime(self):
        return self.taken_time

    def getPutUser(self):
        return self.returned_by

    def getPutTime(self):
        return self.returned_time


class DishChore(Chore):
    # name
    # assignee
    # assigned_time
    # nudges
    # last_nudge
    # active

    initiator = models.ForeignKey(User,
        related_name='initiated_dish_chores', on_delete=models.CASCADE,
        null=True, blank=True) #null initiator indicate automatic chore creation
    solver = models.ForeignKey(User,
        related_name='solved_dish_chores', on_delete=models.CASCADE, null=True, blank=True)
    dish = models.ForeignKey(Dish,
        related_name='chores', on_delete=models.CASCADE)
    solved_time = models.DateTimeField(null=True, blank=True)
    reply = models.TextField(null=True, blank=True)

    def getInitiator(self):
        return self.initiator

    def getAssignee(self):
        return self.assignee

    def getSolver(self):
        return self.solver

    def getDish(self):
        return self.dish

    def getTitle(self):
        return self.name

    def getInitTime(self):
        return self.assigned_time

    def getDoneTime(self):
        return self.solved_time

    def getReply(self):
        return self.reply

    def getReminerCount(self):
        return self.nudges

    @staticmethod
    def create_new(assignee, dish, message, initiator=None):
        if initiator:
            dish_chore = DishChore.objects.create(
                name = "{0}: \"{1}\"".format(dish, message),
                assignee = assignee,
                active = True,
                initiator = initiator,
                dish = dish,
            )
        else:
            dish_chore = DishChore.objects.create(
                name = "{0}: \"{1}\"".format(dish, message),
                assignee = assignee,
                active = True,
                dish = dish,
            )


        from .tasks import sendemail
        title = "Someone assigned you a dish chore"
        if not dish_chore.initiator is None:
            body = "Dear {0},\n\n" \
                "{1} has assigned you a chore for using \"{2}\".\n" \
                "They left the following message:\n\n{3}".format(assignee, initiator, dish, message)
        else:
            body = "Dear {0},\n\n" \
                "A dish chore has automatically been assigned to you to return \"{1}\".".format(assignee, dish)
        sender = getattr(settings, "EMAIL_HOST_USER", 'colemass')
        to = [assignee.email, ]
        sendemail(title, body, sender, to)

    def assign(self, user):
        '''
        Assigns chore to user.
        For DishChores, should only happen when a completion or refusal is challenged.
        '''
        self.solver = None
        self.solved_time = None
        super(DishChore, self).assign(user)

    def complete(self, user):
        '''
        Bypasses base chore completion.
        Does not log a CompletedChore because DishChores are single use.
        '''
        if not self.isSolved():
            self.solver = user
            self.solved_time = timezone.now()
            self.active = False
            self.save()

            # from .tasks import sendemail
            # title = "A dish chore you've initiated is now solved"
            # body = "Dear {0},\n\n" \
                # "The dish chore you assigned to {1} for using \"{2}\" was completed by {3}.\n" \
                # "The solver left this message: \n\n\"{4}\"".format(self.initiator, self.assignee,
                                             # self.dish, self.solver)
            # sender = getattr(settings, "EMAIL_HOST_USER", 'colemass')
            # to = [self.initiator.email, ]
            # sendemail(title, body, sender, to)

    def refuse(self, reason):
        ''' General chore refusal + inactivation. '''
        super(DishChore, self).refuse(reason)
        self.active = False
        self.save()

        if not self.initiator is None:
            from .tasks import sendemail
            title = "A dish chore you've initiated was refused"
            body = "Dear {0},\n\n" \
                "The dish chore you assigned to {1} for using \"{2}\" " \
                "was refused for the following reason:\n\n\"{3}\"".format(self.initiator, self.assignee,
                                             self.dish, reason)
            sender = getattr(settings, "EMAIL_HOST_USER", 'colemass')
            to = [self.initiator.email, ]
            sendemail(title, body, sender, to)

    def isSolved(self):
        return (not self.solver is None)

    def __str__(self):
        return self.getTitle()
