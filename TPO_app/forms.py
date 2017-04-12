from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

class LoginForm(forms.Form):
	email = forms.CharField(label=_('Email'), max_length=64, localize=True)
	geslo = forms.CharField(label=_('Password'), max_length=128, widget=forms.PasswordInput, localize=True)
	
class PasswordChangeForm(forms.Form):
	new_password = forms.CharField(label=_('Password'), min_length=8, max_length=128, widget=forms.PasswordInput, localize=True, 
		validators=[
            RegexValidator(
                regex='^(?=.*\d+)(?=.*[a-zA-Z])[0-9a-zA-Z]{8,}$',
                message='Password must contain at least one numeric and one letter character',
            ),
        ])
	re_password = forms.CharField(label=_('Password (again)'), max_length=128, widget=forms.PasswordInput, localize=True)
	
	def clean(self):
		cleaned_data = super(PasswordChangeForm, self).clean()
		password1 = self.cleaned_data.get('new_password')
		password2 = self.cleaned_data.get('re_password')

		if not password2:
			raise forms.ValidationError("You must confirm your password")
		if password1 != password2:
			raise forms.ValidationError("Your passwords do not match")
		
		return cleaned_data