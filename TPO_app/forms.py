from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from .models import *
from .fields import *
from django.contrib.auth.models import User
import re
from .validators.DelovniNalogValidators import *

class LoginForm(forms.Form):
        username = forms.CharField(label='',max_length=48)
        password = forms.CharField(label='',max_length=48, widget=forms.PasswordInput())


class UporabniskiRacunForm(forms.ModelForm):
    password = forms.CharField(label='Geslo',widget=forms.PasswordInput(),min_length=8)
    password2 = forms.CharField(label='Ponovno geslo',widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email','password']
        labels = {
            "email": "Email"
        }

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
    class Meta:
        model = Pacient
        fields = ['ime','priimek','datum_rojstva','naslov','id_posta','st_kartice','telefon','spol']
        labels = {
            "id_posta": "Posta"
        }


class SkrbnistvoForm(forms.ModelForm):
    CHOICES = [('moski', 'Moški'), ('zenska', 'Ženska')]
    spol = forms.CharField(widget=forms.Select(choices=CHOICES))
    telefon = forms.CharField(required=True)
    class Meta:
        model = Pacient
        fields = ['ime','priimek','datum_rojstva','naslov','id_posta','st_kartice','telefon','spol','razmerje_ur']
        labels = {
            "id_posta": "Posta",
            "razmerje_ur":"Sorodstveno razmerje"
        }

class KontaktForm(forms.ModelForm):
    class Meta:
        model = KontaktnaOseba
        exclude = ['pacient']



class DelovniNalogOsebjeForm(forms.ModelForm):
    sifra = forms.CharField(max_length=64)
    ime = forms.CharField(max_length=64)
    priimek = forms.CharField(max_length=64)

    class Meta:
        model = Osebje
        fields = ['sifra', 'ime', 'priimek']

class DelovniNalogTipObiskaForm(forms.ModelForm):
    tip = TipObiskaModelChoiceField(TipObiska.objects.all(), widget=forms.RadioSelect, empty_label=None)

    class Meta:
        model = TipObiska
        fields = ['tip']

class DelovniNalogVrstaObiskaForm(forms.ModelForm):
    vrstaObiska = VrstaObiskaModelChoiceField(VrstaObiska.objects.all(), widget=forms.RadioSelect, empty_label=None)

    class Meta:
        model = VrstaObiska
        fields = ['vrstaObiska']

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


#FORMSETS
'''
class DelovniNalogInjekcijeForm(forms.ModelForm):
    st_injekcij = forms.IntegerField(label='Število injekcij')

    class Meta:
        model = Injekcije
        fields = ['st_injekcij']
'''

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


class LoginForm(forms.Form):
    email = forms.CharField(label=_('Email'), max_length=64, localize=True)
    geslo = forms.CharField(label=_('Password'), max_length=128, widget=forms.PasswordInput, localize=True)


class PasswordChangeForm(forms.Form):
    new_password = forms.CharField(label=_('Password'), min_length=8, max_length=128, widget=forms.PasswordInput,
                                   localize=True,
                                   validators=[
                                       RegexValidator(
                                           regex='^(?=.*\d+)(?=.*[a-zA-Z])[0-9a-zA-Z]{8,}$',
                                           message='Password must contain at least one numeric and one letter character',
                                       ),
                                   ])
    re_password = forms.CharField(label=_('Password (again)'), max_length=128, widget=forms.PasswordInput,
                                  localize=True)

    def clean(self):
        cleaned_data = super(PasswordChangeForm, self).clean()
        password1 = self.cleaned_data.get('new_password')
        password2 = self.cleaned_data.get('re_password')

        if not password2:
            raise forms.ValidationError("You must confirm your password")
        if password1 != password2:
            raise forms.ValidationError("Your passwords do not match")

        return cleaned_data