from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.models import Group,User
from .forms import OsebjeForm, UporabniskiRacunForm

from TPO_app.models import Osebje, StatusUr

def index(request):
	context = {}
	return render(request,"TPO_app/index.html",context)


def osebjeAdd(request):
	context={}
	
	if request.method=='POST':
		uForm=UporabniskiRacunForm(request.POST, request.FILES)
		oForm=OsebjeForm(request.POST, request.FILES)

		if uForm.is_valid() and oForm.is_valid():
			if(not uForm.password_regex()):
				context['regex']=True
				context['uForm']=uForm
				context['oForm']=oForm
				return render(request, "TPO_app/osebjeAdd.html", context)

			u = User.objects.create_user(username=uForm.cleaned_data['email'],email=uForm.cleaned_data['email'],password=uForm.cleaned_data['password'],is_active=True)
			u.save()
			o=oForm.save(commit=False)
			o.id_racuna = u
			o.izbrisan=0
			o.save()
			uForm.cleaned_data['groups'].user_set.add(u)
			return HttpResponseRedirect(reverse('index'))			
	else:
		uForm=UporabniskiRacunForm()
		oForm=OsebjeForm()

	context['uForm']=uForm
	context['oForm']=oForm

	return render(request, "TPO_app/osebjeAdd.html", context)