from django import forms
from .models import Osebje, AuthGroup
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from django.utils.translation import ugettext_lazy as _
import re


class OsebjeForm(forms.ModelForm):
	class Meta:
		model=Osebje
		fields=['ime', 'priimek', 'šifra','telefon', 'id_zd', 'okolis']
		labels = {
			'id_zd': _('Izvajalec zdravstvene dejavnosti'),
		}

class UporabniskiRacunForm(forms.ModelForm):
	groups = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)
	email=forms.EmailField(required=True)
	ponovno_geslo=forms.CharField(max_length=128,widget=forms.PasswordInput())
	password=forms.CharField(label="Geslo", widget=forms.PasswordInput(), min_length=8)

	class Meta:
		model=User
		fields=[ 'groups', 'email','password']
		labels = {
			'groups': _('Vloga'),
			'email': _('Email'),
			'password': _('Geslo'),
		}

	def clean(self):
		cleaned_data = super(UporabniskiRacunForm, self).clean()
		password = cleaned_data.get("password")
		confirm_password = cleaned_data.get("ponovno_geslo")

		if password != confirm_password:
			raise forms.ValidationError(
				"Gesli se ne ujemata!"
			)
	def password_regex(self):
		password=self.cleaned_data.get("password")
		regex = r'^(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9]+$'

		if(re.match(regex,password)):
			return True
		return False