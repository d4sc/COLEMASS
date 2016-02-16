from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
import random
import string
from django.core.mail import EmailMessage
# These are the views pertaining to USERS and other MANAGEMENT

@login_required
def settings(request):
    cards = Card.objects.filter(user=None).exclude(is_broken=True)
    is_absent= UserDetail.objects.get(user=request.user).is_absent
    return render(request, 'users/settings.html', {'cards': cards, 'is_absent':is_absent})

def pswd_link_gen(request):
    '''
    Basic redirection to password reset form
    '''
    return render(request, 'users/pswd_link_gen.html')

def sendresetemail(request):
    '''
    Sends a password reset link via email to user.
    '''
    randstring = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
    if len(request.POST.get('email'))>0:
        try:
            userdetails = User.objects.get(email=request.POST.get('email'))
            userdet=UserDetail.objects.get(user=userdetails)
            userdet.valid_key=randstring
            userdet.save()
            resetlink='http://'+request.get_host()+'/resetform/'+userdetails.username+'/'+randstring
        except:
            messages.error(request, "Database Connectivity Error: Please check the email provided")
            return render(request, 'users/pswd_link_gen.html')
        email = EmailMessage("COLEMASS:Password Reset",
                    "Hi %s,\n\nPlease follow the link to reset your COLEMASS password.\n%s \nRegards,\nColemass Team" % (userdetails, resetlink),
                    to=[request.POST.get('email')]
                    )
        messages.info(request, "Email sent to your registered address.")
        email.send()
        return render(request, 'users/pswd_link_gen.html')
    elif len(request.POST.get('uname'))>0:
        try:
            userdetails = User.objects.get(username=request.POST.get('uname'))
            userdet=UserDetail.objects.get(user=userdetails)
            userdet.valid_key=randstring
            userdet.save()
            resetlink='http://'+request.get_host()+'/resetform/'+userdetails.username+'/'+randstring
        except:
            messages.error(request, "Database Connectivity Error: Please check the email provided")
            return render(request, 'users/pswd_link_gen.html')
        email = EmailMessage("COLEMASS:Password Reset",
                            "Hi %s,\n\nPlease follow the link to reset your COLEMASS password.\n%s \nRegards,\nColemass Team" % (userdetails, resetlink),
                            to=[userdetails.email])
        messages.info(request, "Email sent to your registered address.")
        email.send()
        return render(request, 'users/pswd_link_gen.html')
    else:
        messages.error(request, "Please enter a username or email address.")
        return render(request, 'users/pswd_link_gen.html')

def reset(request, user, valid_key):
    '''
    Checks validity of the reset link and redirects it password reset form
    '''
    try:
        userdet=UserDetail.objects.get(user=User.objects.get(username=user))
    except:
        raise Http404("You are not a user of this colemass")
    if userdet.check_validkey(valid_key):
        return render(request, 'users/resetpswd.html',{'user':user, 'valid_key':valid_key})
    else:
        raise Http404("Your reset link has expired")

def resetpass(request):
    '''
    Resets the password of the user after thorough checks.
    '''
    if len(request.POST.get('newpswd'))<PASSWORD_SET_LENGTH:
        messages.error(request, "Password should be at least {0} characters.".format(PASSWORD_SET_LENGTH))
        return render(request, 'users/resetpswd.html', {'user':request.POST.get('user'), 'valid_key':request.POST.get('valid_key')})
    elif not len(request.POST.get('newpswd'))<PASSWORD_SET_LENGTH:
        if not(request.POST.get('repswd')==request.POST.get('newpswd')):
            messages.error(request, "Password doesn't match.")
            return render(request, 'users/resetpswd.html', {'user':request.POST.get('user'), 'valid_key':request.POST.get('valid_key')})

        elif (request.POST.get('repswd')==request.POST.get('newpswd')):
            try:
                userdetails = User.objects.get(username=request.POST.get('user'))
                userdetails.set_password(request.POST.get('newpswd'))
                userdet=UserDetail.objects.get(user=userdetails)
                userdet.valid_key=''
                userdet.save()
                userdetails.save()
            except:
                messages.error(request, "Database Connectivity Error: Please check the email provided")
                return render(request, 'users/resetpswd.html', {'user':request.POST.get('user'), 'valid_key':request.POST.get('valid_key')})
            messages.success(request, "Successfully changed password")
            request.next=""
            return redirect('/accounts/login/')
    else:
        messages.error(request, "An unknown error occured. Please try again.")
        return render(request, 'users/resetpswd.html', {'user':request.POST.get('user'), 'valid_key':request.POST.get('valid_key')})

'''
HARDWARE request
'''
def getcardlist(request):
    s = '<%s>' % ''.join([di['card'] for di in Card.objects.values('card')])
    return HttpResponse(s)
