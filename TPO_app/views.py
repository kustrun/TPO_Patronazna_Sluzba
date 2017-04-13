from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .forms import LoginForm, PasswordChangeForm
from .auth import EmailBackend, BlackListBackend

def index(request):
    return HttpResponse("Hello, world.")

def login(request):
	context = {'loginForm':LoginForm(), 'message':""}
	ip = request.META.get('REMOTE_ADDR')
	message = ""
	
	if request.method=='POST':
		if BlackListBackend().login_allowed(ip=ip):
			form = LoginForm(request.POST)
			if form.is_valid():
				user = EmailBackend().authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['geslo'])
				if user is not None:
					auth_login(request, user)
					BlackListBackend().add_ip_to_user(user=user, ip=ip)
					return HttpResponse("Hello, " + user.email)
				else:
					message = "Napacen email in/ali geslo."
					BlackListBackend().failed_login(ip=ip)
					form = LoginForm()
			else:
				message = "Napacen vnos podatkov."
				BlackListBackend().failed_login(ip=ip)
				form = LoginForm()
		else:
			form = LoginForm()
			message = "Blokirani ste zaradi 3x zapored napacno vnesenih podatkov.\nPreostali cas: " + BlackListBackend().lockup_to_string(ip=ip)
	else:
		form = LoginForm()
		
	context['loginForm'] = form
	context['message'] = message
	return render(request, 'TPO_app/login.html', context)

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect(reverse('index'))

def change_password(request):
	context = {'passwordChangeForm':PasswordChangeForm(), 'message':"", 'error':False}
	error = False
	message = ""
	
	if request.method=='POST':
		form = PasswordChangeForm(request.POST)
		user = request.user
		old_password = user.password
		if user is not None and form.is_valid() and user.is_authenticated():
			user.set_password(form.cleaned_data['new_password'])
			user.save()
			auth_user = EmailBackend().authenticate(username=user.email, password=form.cleaned_data['new_password'])
			if auth_user is not None:
				auth_login(request, user)
				message = "Geslo uspesno spremenjeno!"
			else:
				user.set_password(old_password)
				user.save()
				error = True
				message = "Napaka pri spremembi gesla. Vase geslo ni spremenjeno!"
	else:
		form = PasswordChangeForm()
		
	context['message'] = message
	context['error'] = error
	context['passwordChangeForm'] = form
	
	for field, errors in form.errors.items():
		if not error:
			context['message'] = ""
			context['error'] = True
		for error in errors:
			context['message'] += error
	
	print(form.errors.items())
	return render(request, 'TPO_app/change_password.html', context)