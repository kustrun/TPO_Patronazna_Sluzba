# -*- coding: utf-8 -*-

from django import forms
from django.core.validators import RegexValidator
from .models import *
from .fields import *
from django.contrib.auth.models import User,Group
import re
from .DelovniNalogValidators import *
from django.utils.translation import ugettext_lazy as _
from datetime import datetime,date

class PlaniranjeObiskovForm(forms.Form):
    datum = forms.DateField(label=_('Datum'), widget=forms.DateInput, required=False)
    obiski = forms.ModelMultipleChoiceField(label=_('Izbrani obiski'), required=False, widget=forms.CheckboxSelectMultiple, queryset=DodeljenoOsebje.objects.filter(id_obisk__status_obiska_id=1).order_by('id_obisk__predviden_datum', 'id_obisk__status_obiska'))

class UporabniskiRacunForm(forms.ModelForm):
    password = forms.CharField(label='Geslo',widget=forms.PasswordInput(),min_length=8)
    password2 = forms.CharField(label='Ponovno geslo',widget=forms.PasswordInput())
    email = forms.EmailField(label='Email',required=True)
    class Meta:
        model = User
        fields = ['email','password']

    def password_regex(self):
        password = self.cleaned_data.get('password')
        regex = r'^(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9]+$'

        if(re.match(regex,password)):
            return True
        return False

    def password_match(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            return False
        if password1 != password2:
            return False
        return True

class PacientForm(forms.ModelForm):
    CHOICES = [('moski', 'Moški'), ('zenska', 'Ženska')]
    spol = forms.CharField(widget=forms.Select(choices=CHOICES))
    telefon = forms.CharField(required=True)
    datum_rojstva = forms.DateField(input_formats=['%d.%m.%Y'])
    st_kartice=forms.CharField(max_length=9,min_length=9)
    class Meta:
        model = Pacient
        fields = ['ime','priimek','datum_rojstva','naslov','id_posta','st_kartice','telefon','spol']
        labels = {
            "id_posta": "Posta"
        }
    def telefon_regex(self):
        telefon = self.cleaned_data.get('telefon')
        regex = r'([0-9]+)$'
        if re.match(regex,telefon):
            return True
        return False
    def date_valid(self):
        date = self.cleaned_data.get('datum_rojstva')

        if(date <= datetime.now().date()):
            return True
        else:
            return False

class UporabniskiRacunEmailForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)
    class Meta:
        model = User
        fields = ['email']

class SkrbnistvoForm(forms.ModelForm):
    CHOICES = [('moski', 'Moški'), ('zenska', 'Ženska')]
    spol = forms.CharField(widget=forms.Select(choices=CHOICES))
    telefon = forms.CharField(required=False)
    datum_rojstva = forms.DateField(input_formats=['%d.%m.%Y'])
    st_kartice = forms.CharField(max_length=9, min_length=9)
    class Meta:
        model = Pacient
        fields = ['ime','priimek','datum_rojstva','naslov','id_posta','st_kartice','telefon','spol','razmerje_ur']
        labels = {
            "id_posta": "Posta",
            "razmerje_ur":"Sorodstveno razmerje"
        }
    def date_valid(self):
        date = self.cleaned_data.get('datum_rojstva')

        if(date <= datetime.now().date()):
            return True
        else:
            return False
    def telefon_regex(self):
        telefon = self.cleaned_data.get('telefon')
        regex = r'([0-9]*)$'
        if re.match(regex,telefon):
            return True
        return False


class KontaktForm(forms.ModelForm):
    class Meta:
        model = KontaktnaOseba
        exclude = ['pacient']




class DelovniNalogOsebjeForm(forms.ModelForm):
    sifraVnos = forms.CharField(max_length=64)
    ime = forms.CharField(max_length=64)
    priimek = forms.CharField(max_length=64)

    class Meta:
        model = Osebje
        fields = ['ime', 'priimek']

class DelovniNalogTipObiskaForm(forms.ModelForm):
    tipObiskaDB = TipObiska.objects.all()

    TIP_OBISKA = []
    for t in tipObiskaDB:
        TIP_OBISKA.append((t.tip, t.tip))

    tip = forms.ChoiceField(choices=TIP_OBISKA, widget=forms.RadioSelect)

    class Meta:
        model = TipObiska
        fields = ['tip']

class DelovniNalogVrstaObiskaForm(forms.ModelForm):
    vrstaObiskaDB = VrstaObiska.objects.all()

    VRSTA_OBISKA = []
    for v in vrstaObiskaDB:
        VRSTA_OBISKA.append((v.naziv + "_" + v.tip.tip, v.naziv))

    vrstaObiska = forms.ChoiceField(choices=VRSTA_OBISKA, widget=forms.RadioSelect)

    class Meta:
        model = VrstaObiska
        fields = ['vrstaObiska']

class DelovniNalogPacientForm(forms.ModelForm):
    pacientDB = Pacient.objects.all()

    PACIENTI = []
    for p in pacientDB:
        PACIENTI.append((p.st_kartice + ": " + p.ime + " " + p.priimek + "_" + str(p.lastnik_racuna) + "&" + str(p.id_racuna_id), p.st_kartice + ": " + p.ime + " " + p.priimek))

    ime = forms.CharField(widget=forms.Select(choices=PACIENTI))

    class Meta:
        model = Pacient
        fields = ['ime']

class DelovniNalogForm(forms.ModelForm):
    TIP_PRVEGA_OBISKA = [('obvezen', 'obvezen'), ('okviren', 'okviren')]

    datum_prvega_obiska = forms.DateField(input_formats=["%d.%m.%Y"], validators=[dateGreaterThanToday])
    tip_prvega_obiska = forms.ChoiceField(choices=TIP_PRVEGA_OBISKA, widget=forms.RadioSelect)
    st_obiskov = forms.IntegerField(label='Število obiskov', min_value=1, max_value=10)
    cas_med_dvema = forms.IntegerField(label='Čas med dvema zaporednima obiskoma (v dneh)')
    casovno_obdobje = forms.DateField(input_formats=["%d.%m.%Y"])

    class Meta:
        model = DelovniNalog
        fields = ['datum_prvega_obiska', 'tip_prvega_obiska', 'st_obiskov', 'cas_med_dvema', 'casovno_obdobje']

class DelovniNalogZdravilaForm(forms.ModelForm):
    zdravilaDB = Zdravila.objects.all()

    ZDRAVILA = []
    for z in zdravilaDB:
        ZDRAVILA.append((z.naziv, z.naziv))

    naziv = forms.CharField(max_length=64, widget=forms.Select(choices=ZDRAVILA))
    st_injekcij = forms.IntegerField(label='Število injekcij')

    class Meta:
        model = Zdravila
        fields = ['naziv']

class DelovniNalogBarvaEpruveteForm(forms.ModelForm):
    barvaDB = BarvaEpruvete.objects.all()

    BARVA_EPRUVETE = []
    for b in barvaDB:
        BARVA_EPRUVETE.append((b.barva, b.barva))

    barva = forms.CharField(max_length=20, widget=forms.Select(choices=BARVA_EPRUVETE))
    st_epruvet = forms.IntegerField(label='Število epruvet')

    class Meta:
        model = BarvaEpruvete
        fields = ['barva']

class DelovniNalogBarvaEpruveteForm(forms.ModelForm):
    barvaDB = BarvaEpruvete.objects.all()

    BARVA_EPRUVETE = []
    for b in barvaDB:
        BARVA_EPRUVETE.append((b.barva, b.barva))

    barva = forms.CharField(max_length=20, widget=forms.Select(choices=BARVA_EPRUVETE))
    st_epruvet = forms.IntegerField(label='Število epruvet')

    class Meta:
        model = BarvaEpruvete
        fields = ['barva']


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


class OsebjeForm(forms.ModelForm):
    class Meta:
        model=Osebje
        fields=['ime', 'priimek', 'sifra','telefon', 'id_zd']
        labels = {
            'id_zd': _('Izvajalec zdravstvene dejavnosti'),
        }

class UporabniskiForm(forms.ModelForm):
    groups = forms.ModelChoiceField(queryset=Group.objects.exclude(name="Pacient"), required=True)
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
        cleaned_data = super(UporabniskiForm, self).clean()
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

class UporabniskiOkolisForm(forms.ModelForm):
    class Meta:
        model=Osebje
        fields=['okolis']