from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

class LoginForm(forms.Form):
	email = forms.CharField(label=_('Email'), max_length=64, localize=True)
	geslo = forms.CharField(label=_('Geslo'), max_length=128, widget=forms.PasswordInput, localize=True)
	
class PasswordChangeForm(forms.Form):
	new_password = forms.CharField(label=_('Novo geslo'), min_length=8, max_length=128, widget=forms.PasswordInput, localize=True, 
		validators=[
            RegexValidator(
                regex='^(?=.*\d+)(?=.*[a-zA-Z])[0-9a-zA-Z]{8,}$',
                message='Geslo mora vsebovati vsaj eno stevliko in vsaj eno crko.',
            ),
        ])
	re_password = forms.CharField(label=_('Ponovno vnesite novo geslo'), max_length=128, widget=forms.PasswordInput, localize=True)
	
	def clean(self):
		cleaned_data = super(PasswordChangeForm, self).clean()
		password1 = self.cleaned_data.get('new_password')
		password2 = self.cleaned_data.get('re_password')

		if password1:
			if not password2:
				raise forms.ValidationError("Potrdite vase geslo z ponovnim vnosom.")
			if password1 != password2:
				raise forms.ValidationError("Gesli se ne ujemata.")
		
		return cleaned_data