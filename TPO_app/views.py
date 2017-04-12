from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .forms import LoginForm, PasswordChangeForm
from .auth import EmailBackend, BlackListBackend

def index(request):
    return HttpResponse("Hello, world.")

def login(request):
	context = {'loginForm':LoginForm(), 'errorMessage':""}
	ip = request.META.get('REMOTE_ADDR')
	
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
					error = "Napacen email ali geslo"
					ip_user = BlackListBackend().failed_login(ip=ip)
					form = LoginForm()
		else:
			form = LoginForm()
			error = "Blokirani ste zaradi 3x zapored napacno vnesenih podatkov\nPreostali cas: " + BlackListBackend().lockup_to_string(ip=ip)
	else:
		form = LoginForm()
		error = ""
		
	context['loginForm'] = form
	context['errorMessage'] = error
	return render(request, 'TPO_app/login.html', context)

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect(reverse('index'))

def change_password(request):
	context = {'passwordChangeForm':PasswordChangeForm()}
	
	if request.method=='POST':
		form = PasswordChangeForm(request.POST)
		user = request.user
		if user is not None and form.is_valid() and user.is_authenticated():
			user.set_password(form.cleaned_data['new_password'])
			user.save()
			user = EmailBackend().authenticate(username=user.email, password=user.password)
			if user is not None:
				return HttpResponse("Password successfully changed")
			else:
				return HttpResponse("Error with authentication")
	else:
		form = PasswordChangeForm()
		
	context['passwordChangeForm'] = form
	return render(request, 'TPO_app/change_password.html', context)