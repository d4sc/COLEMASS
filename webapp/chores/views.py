from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.contrib import messages
from .models import *
from dishes.models import *
from appliances.models import *
from users.models import *

# These are the views pertaining to CHORES

CHORE_MODELS = (DishChore, ApplianceChore, RecurringChore)

def get_chore_with_model(pk):
    '''
    returns a specific type of chore rather than a generic Chore instance
    '''
    chore = get_object_or_404(Chore, pk=pk)
    defined_chore = chore
    for chore_model in CHORE_MODELS:
        try:
            defined_chore = chore_model.objects.get(pk=chore.pk)
        except:
            pass
    return defined_chore

@login_required
def mycolemass(request):
    ''' Colemass home page view '''
    user = request.user
    chores = Chore.objects.filter(assignee=user)
    completed_chores = CompletedChore.objects.filter(confirmed=False)
    refused_chores = RefusedChore.objects.filter(confirmed=False)
    absent_users = User.objects.filter(userdetail__is_absent=True)
    context = {
        'chores': chores,
        'completed_chores': completed_chores,
        'refused_chores': refused_chores,
        'absent_users': absent_users,
    }
    return render(request, 'chores/mycolemass.html', context)

@login_required
def chores(request):
    chores = Chore.objects.filter(active=True).order_by('-assigned_time')
    return render(request, 'chores/chores.html', {'chores': chores})

@login_required
def stats(request):
    user_stat=Infraction.objects.filter(date__gt= timezone.now()-datetime.timedelta(days=31))
    top_list=user_stat.values('user').annotate(dcount=Count('chore')).order_by('-dcount')
    users=[User.objects.get(pk=i['user']) for i in top_list]
    hall_of_fame= CompletedChore.objects.filter(chore__in=RecurringChore.objects.all()).filter(date__gt= timezone.now()-datetime.timedelta(days=31))
    list_hof=top_list=hall_of_fame.values('user').annotate(dcount=Count('chore')).order_by('-dcount')
    users_hof=[User.objects.get(pk=i['user']) for i in list_hof]
    countOf_Infractions=[i['dcount'] for i in top_list]
    return render(request,'chores/stats.html', {'users': users,'users_hof':users_hof, 'countOf_Infractions':countOf_Infractions})

@login_required
def done(request):
    chore = get_chore_with_model(pk=request.POST.get('pk'))
    chore.complete(user=request.user)
    messages.info(request, "You've completed \"{0}\"".format(chore.name))
    return redirect('mycolemass')

@login_required
def refuse(request):
    chore = get_chore_with_model(pk=request.POST.get('pk'))
    reason = request.POST.get('reason')
    chore.refuse(reason)
    return redirect('mycolemass')

@login_required
def nudge(request):
    chore = get_chore_with_model(pk=request.POST.get('pk'))
    message = chore.report()
    messages.info(request, message)
    return redirect('chores:chores')

@login_required
def completed_chore_approve(request):
    completed_chore = get_object_or_404(CompletedChore, pk=request.POST.get('pk'))
    completed_chore.confirm()
    messages.info(request, "You confirmed that {0} completed \"{1}\"".format(completed_chore.user.username, completed_chore.chore.name))
    return redirect('mycolemass')

@login_required
def completed_chore_challenge(request):
    completed_chore = get_object_or_404(CompletedChore, pk=request.POST.get('pk'))
    completed_chore.challenge()
    messages.info(request, "You rejected {0}'s completion of \"{1}\"".format(completed_chore.user.username, completed_chore.chore.name))
    return redirect('mycolemass')

@login_required
def refusal_approve(request):
    refused_chore = get_object_or_404(RefusedChore, pk=request.POST.get('pk'))
    refused_chore.confirm()
    messages.info(request, "You confirmed that {0} has a valid reason" \
        " not to complete\"{1}\"".format(refused_chore.user.username, refused_chore.chore.name))
    return redirect('mycolemass')

@login_required
def refusal_challenge(request):
    refused_chore = get_object_or_404(RefusedChore, pk=request.POST.get('pk'))
    refused_chore.confirm()
    messages.info(request, "You rejected {0}'s reason for refusing \"{1}\"".format(refused_chore.user.username, refused_chore.chore.name))
    return redirect('mycolemass')

@login_required
def infractions_stat(request):
    pass

class RecurringChoreListView(ListView):
    queryset = RecurringChore.objects.order_by('name')
    context_object_name = 'chores'
    template_name = 'chores/settings.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RecurringChoreListView, self).dispatch(*args, **kwargs)

class RecurringChoreUpdate(UpdateView):
    model = RecurringChore
    fields = ['name']
    template_name = 'chores/edit.html'
    success_url = reverse_lazy('chores:settings')

class RecurringChoreCreate(CreateView):
    model = RecurringChore
    fields = ['name']
    template_name = 'chores/new.html'
    success_url = reverse_lazy('chores:settings')
    
    def form_valid(self, form):
        form.instance.assignee = self.request.user
        form.instance.active = True
        return super(RecurringChoreCreate, self).form_valid(form)

class RecurringChoreDelete(DeleteView):
    model = RecurringChore
    success_url = reverse_lazy('chores:settings')
    template_name = 'chores/confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.completedchore_set.all() and not self.object.refusedchore_set.all():
            name = self.object.name
            self.object.delete()
            success_url = self.get_success_url()
            messages.info(request, "You successfully deleted \"{0}\".".format(name))
            return HttpResponseRedirect(success_url)
        else:
            messages.error(request, 'You may not delete this chore.')
            return HttpResponseRedirect(self.get_success_url())


@login_required
def update_active_chores(request):
    chores_to_activate = RecurringChore.objects.filter(pk__in=request.POST.getlist('active'))
    activated_chores = []
    deactivated_chores = []
    for chore in RecurringChore.objects.all():
        if chore in chores_to_activate and not chore.active:
            chore.active = True
            chore.save()
            activated_chores.append(chore)
        elif chore not in chores_to_activate and chore.active:
            chore.active = False
            chore.save()
            deactivated_chores.append(chore)
    if activated_chores:
        messages.info(request,
            "Activated: {0}".format(', '.join([chore.name for chore in activated_chores]))
            )
    if deactivated_chores:
        messages.info(request,
            "Deactivated: {0}".format(', '.join([chore.name for chore in deactivated_chores]))
            )
    if not activated_chores and not deactivated_chores:
        messages.info(request, "No chore was updated.")
    return redirect('chores:settings')