from django.shortcuts import render,  get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from .models import *

@login_required
def dishList(request):
    return render(request, 'dishes/dishlist.html', {'dishes': Dish.objects.all()})

@login_required
def myDishes(request,):
    dishes = Dish.getUserDishes(request.user)
    return render(request, 'dishes/mydishes.html', {'dishes': dishes})

@login_required
def dishLog(request):
    dish_id=request.POST.get('dish_id')
    ent = DishLog.getDishUsageLog(dish_id, 10)
    usr = []
    btns = [False] * len(ent)
    entries = zip(ent,btns)

    for i in range(len(ent)):
        if not ent[i].getTakeUser() in usr:
            usr.append(ent[i].getTakeUser())
            btns[i]=True
        elif not ent[i].getPutUser() in usr:
            usr.append(ent[i].getPutUser())
            btns[i]=True

    return render(request, 'dishes/dishlog.html', {'entries': entries})

@login_required
def newDish(request):
    if request.POST:
        ud = UnregisteredDish.objects.filter(
            pk__in=request.POST.getlist('checkdish'))
        if len(ud) == 0:
            messages.info(request, 'Please select at least 1 dish.')
        else:
            s = ''
            from django.db import IntegrityError
            try:
                import re
                for d in ud:
                    txt_Title = request.POST.get('title_' + str(d.id))
                    reg = re.compile(r'^[\w\s]+$')
                    if reg.search(txt_Title) is None:
                        messages.info(request, 'Please use only alphanumeric symbols and whitespaces to name dish.')
                        return render(request, 'dishes/newdish.html', {'dishes': UnregisteredDish.objects.all()})
                    d.registerDish(txt_Title)
                    s += '\"%s\" ' % d.getTitle()
            except IntegrityError:
                messages.error(request, 'Dish with tag already exists.')
            else:
                messages.info(request, s + 'were successfully registered.')
                return redirect('dishes:dishlist')

    return render(request, 'dishes/newdish.html', {'dishes': UnregisteredDish.objects.all()})


@login_required
def editDish(request):
    dish_id=request.POST.get('dish_id')
    dish = get_object_or_404(Dish, pk=dish_id)
    if request.POST:
        if 'btn_save' in request.POST:
            import re
            txt_Title = request.POST.get('txt_Title')
            reg = re.compile(r'^[\w\s]+$')
            if reg.search(txt_Title) is None:
                messages.info(request, 'Please   use only alphanumeric symbols and whitespaces to name dish.')
                return render(request, 'dishes/editdish.html', {'dish': dish})
            dish.setTitle(txt_Title)
            dish.save()
            return redirect('dishes:dishlist')
        if 'btn_rmv' in request.POST:
            return redirect(reverse('dishes:rmvdish', args=[dish.id]))
        else:
            return render(request, 'dishes/editdish.html', {'dish': dish})


@login_required
def rmvDish(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    if request.POST:
        dish.delete()
        messages.info(request, '%s was successfully deleted.' %
                      dish.getTitle())
        return redirect('dishes:dishlist')
    else:
        return render(request, 'dishes/rmvdish.html', {'dish': dish})

@login_required
def newDishChore(request):
    from django.contrib.auth.models import User

    reported_user = None
    dish_log = get_object_or_404(DishLog, pk=request.POST.get('entry_id'))
    user_radio = request.POST.get('usrlist')
    message = request.POST.get('txt_message')
    active_chores = DishChore.objects.filter(dish=dish_log.dish, active=True)
    
    if message:
        message = message.strip()
    if request.POST:
        if active_chores:
            messages.info(request, 'A dish chore for this dish is already existing.')
            return redirect('dishes:dishlist')
        if ((dish_log.taken_by != request.user) and
            (dish_log.returned_by != request.user) and
            (dish_log.taken_by != dish_log.returned_by) and
            (dish_log.returned_by is not None)):
            if user_radio is not None:
                reported_user = (dish_log.taken_by, dish_log.returned_by)[int(user_radio)]
            else:
                messages.info(request, 'Please select an assignee')
        elif (dish_log.taken_by != request.user):
            reported_user = dish_log.taken_by
        elif (dish_log.returned_by != request.user):
            reported_user = dish_log.returned_by
        else:
            return HttpResponseBadRequest()
        
        if not message:
            messages.info(request, 'Please leave a message')
        
        if message and reported_user:
            DishChore.create_new(
                initiator = request.user,
                assignee = reported_user,
                dish = dish_log.dish,
                message = message
                )
            messages.info(request, 'Dish chore successfully added.')
            return redirect('dishes:dishlist')
        else:
            user_list = []
            for user in {dish_log.taken_by, dish_log.returned_by}:
                if (user != request.user) and (user is not None):
                    user_list.append(user)
            
            if not user_list:
                return HttpResponseBadRequest()
            else:
                context = {
                    'dish': dish_log.dish,
                    'usr': user_list,
                    'entry_id': dish_log.pk,
                    }
                return render(request, 'dishes/newdishchore.html', context)
    else:
        return HttpResponse(3)