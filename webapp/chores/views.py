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

from .forms import RecurringChoreForm
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
    chores = Chore.objects.filter(assignee=user, active=True)
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
    messages.success(request, "You've completed \"{0}\"".format(chore.name))
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
    messages.success(request, "You confirmed that {0} completed \"{1}\"".format(completed_chore.user.username, completed_chore.chore.name))
    return redirect('mycolemass')

@login_required
def completed_chore_challenge(request):
    completed_chore = get_object_or_404(CompletedChore, pk=request.POST.get('pk'))
    completed_chore.challenge()
    messages.error(request, "You rejected {0}'s completion of \"{1}\"".format(completed_chore.user.username, completed_chore.chore.name))
    return redirect('mycolemass')

@login_required
def refusal_approve(request):
    refused_chore = get_object_or_404(RefusedChore, pk=request.POST.get('pk'))
    refused_chore.confirm()
    messages.success(request, "You confirmed that {0} has a valid reason" \
        " not to complete\"{1}\"".format(refused_chore.user.username, refused_chore.chore.name))
    return redirect('mycolemass')

@login_required
def refusal_challenge(request):
    refused_chore = get_object_or_404(RefusedChore, pk=request.POST.get('pk'))
    refused_chore.confirm()
    messages.error(request, "You rejected {0}'s reason for refusing \"{1}\"".format(refused_chore.user.username, refused_chore.chore.name))
    return redirect('mycolemass')

@login_required
def new(request):
    if request.method == 'POST':
        form = RecurringChoreForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['name'] in [i.name for i in RecurringChore.objects.all()]:
                messages.error(request, "There is already a chore by that name. Please chose another name.")
            else:
                form.instance.assignee = request.user
                form.instance.round_robin = random_order()
                form.save()
                messages.success(request, "\"{0}\" was successfully created.".format(form.cleaned_data['name']))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('chores:settings')

@login_required
def edit(request):
    if request.method == 'POST':
        chore = get_object_or_404(RecurringChore, pk=request.POST.get('pk'))
        old_name = chore.name
        form = RecurringChoreForm(request.POST, instance=chore)
        if form.is_valid():
            if form.cleaned_data['name'] != old_name:
                if form.cleaned_data['name'] in [i.name for i in RecurringChore.objects.all()]:
                    messages.error(request, "There is already a chore by that name. Please chose another name.")
                else:
                    form.save()
                    messages.success(request, "\"{0}\" was successfully updated.".format(chore.name))
            else:
                form.save()
                messages.success(request, "\"{0}\" was successfully {1}activated.".format(chore.name, ("de", "")[chore.active]))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('chores:settings')

@login_required
def delete(request):
    if request.method == 'POST':
        chore = get_object_or_404(RecurringChore, pk=request.POST.get('pk'))
        if chore.completedchore_set.all() or chore.refusedchore_set.all():
            messages.error(request, "You may not delete this chore.")
        else:
            messages.success(request, "You successfully deleted \"{0}\".".format(chore.name))
            chore.delete()
    return redirect('chores:settings')

class RecurringChoreListView(ListView):
    queryset = RecurringChore.objects.order_by('-active', 'name')
    context_object_name = 'chores'
    template_name = 'chores/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super(RecurringChoreListView, self).get_context_data(**kwargs)
        context['form'] = RecurringChoreForm()
        return context

# class RecurringChoreUpdate(UpdateView):
    # model = RecurringChore
    # fields = ['name']
    # template_name = 'chores/edit.html'
    # success_url = reverse_lazy('chores:settings')

# class RecurringChoreCreate(CreateView):
    # model = RecurringChore
    # fields = ['name']
    # template_name = 'chores/new.html'
    # success_url = reverse_lazy('chores:settings')
    
    # def form_valid(self, form):
        # form.instance.assignee = self.request.user
        # form.instance.active = True
        # return super(RecurringChoreCreate, self).form_valid(form)

# class RecurringChoreDelete(DeleteView):
    # model = RecurringChore
    # success_url = reverse_lazy('chores:settings')
    # template_name = 'chores/confirm_delete.html'
    
    # def delete(self, request, *args, **kwargs):
        # self.object = self.get_object()
        # if not self.object.completedchore_set.all() and not self.object.refusedchore_set.all():
            # name = self.object.name
            # self.object.delete()
            # success_url = self.get_success_url()
            # messages.success(request, "You successfully deleted \"{0}\".".format(name))
            # return HttpResponseRedirect(success_url)
        # else:
            # messages.error(request, 'You may not delete this chore.')
            # return HttpResponseRedirect(self.get_success_url())
