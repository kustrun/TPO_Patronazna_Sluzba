# -*- coding: utf-8 -*-

import simplejson as simplejson
from django.core import serializers
from django.shortcuts import render
from django import template
from itertools import chain
from django.forms import formset_factory
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from .forms import *
from .models import *
from django.db.models import Q,Count
from django.contrib.auth.models import User,Group
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from hashids import Hashids
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime
import re
from datetime import timedelta
from .auth import EmailBackend, BlackListBackend
import json
from collections import namedtuple

def posli_email(sendString,email):
    send_mail(
        'Aktivacija',
        sendString,
        'testko.test2@gmail.com',
        [email],
        fail_silently=False,
    )

class BasePacientaFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        pacienti = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                pacient = form.cleaned_data['ime']

                if pacient in pacienti:
                    duplicates = True

                pacienti.append(pacient)

                if duplicates:
                    raise forms.ValidationError(
                        'Podvojena vnosa pacienta: %(pacient)s.',
                        params={'pacient': pacient.split("_")[0]},
                    )

class BaseZdravilaFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        zdravila = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                zdravilo = form.cleaned_data['naziv']

                if zdravilo in zdravila:
                    duplicates = True

                zdravila.append(zdravilo)

                if duplicates:
                    raise forms.ValidationError(
                        'Podvojena vnosa zdravila: %(zdravilo)s.',
                        params={'zdravilo': zdravilo},
                    )

class BaseBarvaEpruvetFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        barve = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                barva = form.cleaned_data['barva']

                if barva in barve:
                    duplicates = True

                barve.append(barva)

                if duplicates:
                    raise forms.ValidationError(
                        'Podvojena vnosa barve epruvete: %(barva)s.',
                        params={'barva': barva},
                    )

@login_required
def delovniNalog(request):
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
        name = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    else:
        ime = request.user.username
    osebje = DelovniNalogOsebjeForm()
    osebje.fields["sifraVnos"].initial = ime.sifra
    osebje.fields["ime"].initial = ime.ime
    osebje.fields["priimek"].initial = ime.priimek

    tipObiska = DelovniNalogTipObiskaForm()
    vrstaObiska = DelovniNalogVrstaObiskaForm()
    delovniNalog = DelovniNalogForm()

    # Create the formset, specifying the form and formset we want to use.
    IzberiPacientaFormSet = formset_factory(DelovniNalogPacientForm, formset=BasePacientaFormSet)
    izberiPacientaFormSet = IzberiPacientaFormSet(prefix='izberiPacienta')

    ZdravilaFormSet = formset_factory(DelovniNalogZdravilaForm, formset=BaseZdravilaFormSet)
    zdravilaFormSet = ZdravilaFormSet(prefix='zdravila')

    BarvaEpruvetFormSet = formset_factory(DelovniNalogBarvaEpruveteForm, formset=BaseBarvaEpruvetFormSet)
    barvaEpruvetFormSet = BarvaEpruvetFormSet(prefix='barva')

    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        osebje = DelovniNalogOsebjeForm(request.POST)
        tipObiska = DelovniNalogTipObiskaForm(request.POST)
        vrstaObiska = DelovniNalogVrstaObiskaForm(request.POST)
        delovniNalog = DelovniNalogForm(request.POST)
        izberiPacientaFormSet = IzberiPacientaFormSet(request.POST, prefix='izberiPacienta')
        zdravilaFormSet = ZdravilaFormSet(request.POST, prefix='zdravila')
        barvaEpruvetFormSet = BarvaEpruvetFormSet(request.POST, prefix='barva')

        # check whether it's valid:
        if osebje.is_valid() and tipObiska.is_valid() and vrstaObiska.is_valid() and delovniNalog.is_valid() and izberiPacientaFormSet.is_valid():

            # SHRANI DELOVNI NALOG
            dn = delovniNalog.save(commit=False)
            dn.id_osebje = Osebje.objects.get(sifra=osebje.data['sifraVnos'], ime=osebje.data['ime'],
                                              priimek=osebje.data['priimek'])
            vrstaObiskaSplit = vrstaObiska.data['vrstaObiska'].split("_")

            dn.id_vrsta = VrstaObiska.objects.get(naziv=vrstaObiskaSplit[0],
                                                  tip=TipObiska.objects.get(tip=tipObiska.data['tip']))
            dn.vrsta_storitve = VrstaStoritve.objects.get(naziv="obisk")  # zakaj se uporablja to polje?
            dn.status_dn = StatusDn.objects.get(naziv="aktiven")

            dn.save()

            # SHRANI OSKRBO PACIENTA
            pacientovOkolis = None
            for pacient in izberiPacientaFormSet:
                data = str(pacient.cleaned_data.get('ime')).split("_")
                pacientSplit = data[0].split(":")

                trenutniPacient = Pacient.objects.get(st_kartice=pacientSplit[0])
                pacientovOkolis = trenutniPacient.id_okolis

                os = Oskrba(
                    id_dn=dn,
                    id_pacient=trenutniPacient
                )

                os.save()


            #IZBERI PATRONAZNO SESTRO
            vsePatronazneSestre = Osebje.objects.filter(id_racuna_id__in=[x.user.id for x in (
            AuthUserGroups.objects.filter(group=AuthGroup.objects.get(name='Patronažna sestra')))],
                                                        okolis=pacientovOkolis)

            min = 10000
            izbranaPS = None
            for patronaznaSestra in vsePatronazneSestre:
                obiski = DodeljenoOsebje.objects.filter(id_osebja=patronaznaSestra,
                                                        id_obisk__in=[x for x in (Obisk.objects.filter(
                                                            id_dn__in=[y for y in DelovniNalog.objects.filter(
                                                                status_dn=StatusDn.objects.get(naziv="aktiven"))
                                                            ]))
                                                        ],
                                                        id_nadomestna=None)

                if (int(len(obiski)) < min):
                    min = len(obiski)
                    izbranaPS = patronaznaSestra

            # USTVARI USTREZNE OBISKE
            datum = dn.datum_prvega_obiska
            if datum.weekday() == 5:
                datum = datum + timedelta(days=2)
            elif datum.weekday() == 6:
                datum = datum + timedelta(days=1)

            for i in range(0, dn.st_obiskov):
                tip_obiska = 0

                if(delovniNalog.data['tip_prvega_obiska'] == 'okviren'):
                    tip_obiska = 1

                ob = Obisk(id_dn=dn,
                           zaporedna_st_obiska=(i + 1),
                           status_obiska=StatusObiska.objects.get(naziv="aktiven"),
                           obvezen = tip_obiska,
                           datum_obiska=datum,
                           predviden_datum=datum,
                           podrobnosti_obiska=("%d. obisk" % (i + 1)),
                           izbran_datum=datum,
                           cena=0.00)

                ob.save()

                # obisk dodeli medicinski sestri
                # TO DO: medicinsko sestro izberi na podlagi okrožja
                do = DodeljenoOsebje(
                    id_obisk=ob,
                    id_osebja=izbranaPS,
                    id_nadomestna=None
                )

                do.save()

                # povecaj datum za naslednji obisk
                datum = datum + timedelta(days=(int(dn.cas_med_dvema) + 1))

                if datum.weekday() == 5:
                    datum = datum + timedelta(days=2)
                elif datum.weekday() == 6:
                    datum = datum + timedelta(days=1)

                # SHRANI APLIKACIJO INJEKCIJ
                if zdravilaFormSet.is_valid():
                    for zdravila in zdravilaFormSet:
                        ij = Injekcije(
                            id_obisk=ob,
                            id_zdravilo=Zdravila.objects.get(naziv=zdravila.cleaned_data.get('naziv')),
                            st_injekcij=int(zdravila.cleaned_data.get('st_injekcij'))
                        )

                        ij.save()

                # SHRANI ODVZEM KRVI
                if barvaEpruvetFormSet.is_valid():
                    for barva in barvaEpruvetFormSet:
                        ok = OdvzemKrvi(
                            id_obisk=ob,
                            barva=BarvaEpruvete.objects.get(barva=barva.cleaned_data.get('barva')),
                            st_epruvet=int(barva.cleaned_data.get('st_epruvet'))
                        )

                        ok.save()

            return HttpResponseRedirect('/patronaza/domov')

    return render(request, 'patronaza/delovniNalog.html', {
        'osebje': osebje,
        'tipObiska': tipObiska,
        'vrstaObiska': vrstaObiska,
        'izberiPacientaFormSet': izberiPacientaFormSet,
        'delovniNalog': delovniNalog,
        'zdravilaFormSet': zdravilaFormSet,
        'barvaEpruvetFormSet': barvaEpruvetFormSet,
        'ime': name
    })

@login_required
def delovniNalogPodrobnosti(request, delovniNalogId):
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
        name = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    else:
        ime = request.user.username

    osebje = DelovniNalogOsebjeForm()

    tipObiska = DelovniNalogTipObiskaForm()
    vrstaObiska = DelovniNalogVrstaObiskaForm()
    delovniNalog = DelovniNalogForm()

    # Create the formset, specifying the form and formset we want to use.
    IzberiPacientaFormSet = formset_factory(DelovniNalogPacientForm, formset=BasePacientaFormSet)
    izberiPacientaFormSet = IzberiPacientaFormSet(prefix='izberiPacienta')

    ZdravilaFormSet = formset_factory(DelovniNalogZdravilaForm, formset=BaseZdravilaFormSet)
    zdravilaFormSet = ZdravilaFormSet(prefix='zdravila')

    BarvaEpruvetFormSet = formset_factory(DelovniNalogBarvaEpruveteForm, formset=BaseBarvaEpruvetFormSet)
    barvaEpruvetFormSet = BarvaEpruvetFormSet(prefix='barva')

    # Get data from database
    delovniNalogDB = DelovniNalog.objects.get(id=delovniNalogId)
    obiskDB = Obisk.objects.filter(id_dn=delovniNalogDB)
    dodeljenoOsebjeDB = DodeljenoOsebje.objects.filter(id_obisk__in=[x for x in obiskDB])
    vrstaObiskaDB = delovniNalogDB.id_vrsta
    tipObiskaDB = vrstaObiskaDB.tip
    injekcijeDB = Injekcije.objects.filter(id_obisk=obiskDB[0])
    odvzemKrviDB = OdvzemKrvi.objects.filter(id_obisk=obiskDB[0])
    pacientiDB = Oskrba.objects.filter(id_dn=delovniNalogDB)

    osebje.fields["sifraVnos"].initial = delovniNalogDB.id_osebje.sifra
    osebje.fields["ime"].initial = delovniNalogDB.id_osebje.ime
    osebje.fields["priimek"].initial = delovniNalogDB.id_osebje.priimek

    delovniNalog.fields["datum_prvega_obiska"].initial = delovniNalogDB.datum_prvega_obiska

    status_obvezen = obiskDB[0].obvezen
    obvezen = 'obvezen'
    if status_obvezen == 1:
        obvezen = 'okviren'

    delovniNalog.fields["tip_prvega_obiska"].initial = obvezen
    delovniNalog.fields["st_obiskov"].initial = delovniNalogDB.st_obiskov
    delovniNalog.fields["cas_med_dvema"].initial = delovniNalogDB.cas_med_dvema
    delovniNalog.fields["casovno_obdobje"].initial = delovniNalogDB.casovno_obdobje

    tipObiska.fields["tip"].initial = tipObiskaDB.tip

    vrstaObiska.fields["vrstaObiska"].initial = vrstaObiskaDB.naziv + "_" + vrstaObiskaDB.tip.tip

    pacientiLen = len(pacientiDB)
    IzberiPacientaFormSet = formset_factory(DelovniNalogPacientForm, formset=BasePacientaFormSet, extra=pacientiLen)
    izberiPacientaFormSet = IzberiPacientaFormSet(prefix='izberiPacienta')

    for i in range(0, pacientiLen):
        izberiPacientaFormSet[i].fields["ime"].initial = pacientiDB[i].id_pacient.st_kartice + ": " + pacientiDB[
            i].id_pacient.ime + " " + pacientiDB[i].id_pacient.priimek + "_" + str(pacientiDB[i].id_pacient.lastnik_racuna) + "&" + str(pacientiDB[i].id_pacient.id_racuna_id)

    injekcijeLen = len(injekcijeDB)
    ZdravilaFormSet = formset_factory(DelovniNalogZdravilaForm, formset=BaseZdravilaFormSet, extra=injekcijeLen)
    zdravilaFormSet = ZdravilaFormSet(prefix='zdravila')

    for i in range(0, injekcijeLen):
        zdravilaFormSet[i].fields["naziv"].initial = injekcijeDB[i].id_zdravilo.naziv
        zdravilaFormSet[i].fields["st_injekcij"].initial = injekcijeDB[i].st_injekcij

    odvzemKrviLen = len(odvzemKrviDB)
    BarvaEpruvetFormSet = formset_factory(DelovniNalogBarvaEpruveteForm, formset=BaseBarvaEpruvetFormSet,
                                          extra=odvzemKrviLen)
    barvaEpruvetFormSet = BarvaEpruvetFormSet(prefix='barva')

    for i in range(0, odvzemKrviLen):
        barvaEpruvetFormSet[i].fields["barva"].initial = odvzemKrviDB[i].barva.barva
        barvaEpruvetFormSet[i].fields["st_epruvet"].initial = odvzemKrviDB[i].st_epruvet

    return render(request, 'patronaza/delovniNalogPodrobnosti.html', {
        'osebje': osebje,
        'tipObiska': tipObiska,
        'vrstaObiska': vrstaObiska,
        'izberiPacientaFormSet': izberiPacientaFormSet,
        'delovniNalog': delovniNalog,
        'zdravilaFormSet': zdravilaFormSet,
        'barvaEpruvetFormSet': barvaEpruvetFormSet,
        'dodeljenoOsebjeDB': dodeljenoOsebjeDB,
        'ime': name
    })

@login_required
def obiskPodrobnosti(request, obiskId):
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
        name = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
        name = str(request.user.groups.all()[0].name) + ' ' + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    else:
        ime = request.user.username

    obisk = Obisk.objects.get(id=obiskId)
    dodeljenoOsebje = DodeljenoOsebje.objects.get(id_obisk = obisk)
    ostaliPodatki = OstaliPodatki.objects.filter(id_obisk = obisk).order_by('id_podatki_aktivnosti')
    pacienti = Oskrba.objects.filter(id_dn=obisk.id_dn)

    return render(request, 'patronaza/obiskPodrobnosti.html', {
        'obisk': obisk,
        'dodeljenoOsebje': dodeljenoOsebje,
        'ostaliPodatki': ostaliPodatki,
        'pacienti': pacienti,
        'ime': name
    })

@login_required
def index(request):
    context = {}
    ime = ''
    if(Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = str(request.user.groups.all()[0].name) + ' ' +  str(Osebje.objects.get(id_racuna=request.user))
    elif(Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna = True)[0])
    else:
        ime = request.user.username
    context['ime'] = ime
    return render(request, 'patronaza/index.html', context)

def login(request):
    context = {'loginForm': LoginForm(), 'errorMessage': ""}
    ip = request.META.get('REMOTE_ADDR')

    if request.method == 'POST':
        if BlackListBackend().login_allowed(ip=ip):
            form = LoginForm(request.POST)
            if form.is_valid():
                user = EmailBackend().authenticate(username=form.cleaned_data['email'],
                                                   password=form.cleaned_data['geslo'])
                if user is not None:
                    auth_login(request, user)
                    BlackListBackend().add_ip_to_user(user=user, ip=ip)
                    return HttpResponseRedirect(reverse('index'))
                else:
                    error = "Napačen email ali geslo"
                    ip_user = BlackListBackend().failed_login(ip=ip)
                    form = LoginForm()
        else:
            form = LoginForm()
            error = "Blokirani ste zaradi " + str(BlackListBackend().get_max_login_attempts()) + "x zapored napačno vnešenih podatkov\nPreostali čas: " + BlackListBackend().lockup_to_string(
                ip=ip)
    else:
        form = LoginForm()
        error = ""

    context['loginForm'] = form
    context['errorMessage'] = error
    return render(request, 'patronaza/login.html', context)

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('login'))

@login_required
def change_password(request):
	context = {'passwordChangeForm':PasswordChangeForm(), 'message':"", 'error':False, 'ime': str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))}
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
	return render(request, 'patronaza/change_password.html', context)

def registracija(request):
    context = {'uporabniskiRacunForm' : UporabniskiRacunForm(),'pacientForm' : PacientForm(),'regex' : False, 'match' : False, 'telefon':False,'date':False}
    if request.method == 'POST':
        uform = UporabniskiRacunForm(request.POST)
        pform = PacientForm(request.POST)
        if uform.is_valid() and pform.is_valid():
            if (Pacient.objects.filter(st_kartice=pform.cleaned_data['st_kartice']).exists()):
                context['kartica'] = True
                return render(request, 'patronaza/registracija.html', context)
            elif (User.objects.filter(email=uform.cleaned_data['email']).exists()):
                context['email'] = True
                return render(request, 'patronaza/registracija.html', context)
            if(not pform.date_valid()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['date'] = True
                return render(request, 'patronaza/registracija.html', context)
            if(not pform.telefon_regex()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['telefon'] = True
                return render(request,'patronaza/registracija.html',context)
            if(not uform.password_regex()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['regex'] = True
                return render(request, 'patronaza/registracija.html', context)
            if(not uform.password_match()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['match'] = True
                return render(request, 'patronaza/registracija.html', context)
            u = User.objects.create_user(username=uform.cleaned_data['email'], password=uform.cleaned_data['password'], email=uform.cleaned_data['email'],
                                         is_superuser='f', is_staff='f', is_active='f')
            u.save()

            instance = pform.save(commit=False)
            instance.id_racuna = u
            instance.lastnik_racuna = True
            instance.id_okolis = Okolis.objects.get(sifra=str(instance.id_posta.st_poste))
            instance.save()

            g = Group.objects.get(name='Pacient')
            g.user_set.add(u)

            hashids = Hashids(salt="salt1234")
            ciphertext = hashids.encode(u.id)
            time = datetime.datetime.now().time()
            date = datetime.datetime.now().date()
            sendString = "Pozdravljeni \n Ustvarili ste si račun za uporabo naše" \
                         " aplikacije Patronažna služba. Da se boste lahko prijavili prosimo odprite spodnjo povezavo\n" \
                         "https://patronaza.herokuapp.com/patronaza/aktivacija/" + ciphertext + "/" + str(
                date) + "*" + str(time)
            posli_email(sendString, str(u.email))
            return HttpResponseRedirect(reverse('kontakt',kwargs={'id':instance.id}))
        else:
            print("Napaka")
    return render(request, 'patronaza/registracija.html', context)

def kontakt(request,id):
    context = {'kontaktForm': KontaktForm}
    if request.method == 'POST':
        if request.POST.get('dodaj'):
            kform = KontaktForm(request.POST)
            if kform.is_valid:
                kontakt = kform.save(commit=False)
                kontakt.pacient = Pacient.objects.get(pk=id)
                kontakt.save()

        return HttpResponseRedirect(reverse('login'))
    return render(request, 'patronaza/registracija_kontakt.html', context)

@login_required
def pregled_skrbnistev(request):
    context = {'pacijenti' : SkrbnistvoForm()}
    ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    context['ime'] = ime
    ur = request.user
    result = Pacient.objects.filter(id_racuna=ur).filter(lastnik_racuna = False)
    pacijenti = []
    for r in result:
        r.datum_rojstva = r.datum_rojstva.strftime('%d.%m.%Y')
        pacijenti.append(SkrbnistvoForm(instance=r))

    context['pacijenti'] = result
    return render(request, 'patronaza/pregled.html', context)

@login_required
def dodaj_skrbnistvo(request):
    context = {'skrbnistvoForm': SkrbnistvoForm(),'date':False, 'telefon':False}
    ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    context['ime'] = ime
    if(request.method == 'POST'):
        sform = SkrbnistvoForm(request.POST)
        if sform.is_valid():
            if (Pacient.objects.filter(st_kartice=sform.cleaned_data['st_kartice']).exists()):
                context['kartica'] = True
                return render(request, 'patronaza/dodajSkrbnistvo.html', context)
            if(not sform.telefon_regex()):
                context['telefon'] = True
                context['skrbnistvoForm'] = sform
                return render(request, 'patronaza/dodajSkrbnistvo.html', context)
            if(not sform.date_valid()):
                context['date'] = True
                context['skrbnistvoForm'] = sform
                return render(request, 'patronaza/dodajSkrbnistvo.html', context)
            instance = sform.save(commit=False)
            instance.id_racuna = request.user
            instance.lastnik_racuna = False
            instance.id_okolis = Okolis.objects.get(sifra=str(instance.id_posta.st_poste))
            instance.save()
            return HttpResponseRedirect(reverse('pregled_skrbnistev'))
    return render(request, 'patronaza/dodajSkrbnistvo.html', context)\

@login_required
def uredi_skrbnistvo(request,pacientId):
    context = {'napaka':False}
    ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    pacient = Pacient.objects.get(pk=pacientId)
    pacient.datum_rojstva = pacient.datum_rojstva.strftime('%d.%m.%Y')
    sform = SkrbnistvoForm(instance=pacient)
    context['ime'] = ime
    context['skrbnistvoForm'] = SkrbnistvoForm(instance=pacient)
    if(request.method == 'POST'):
        sform = SkrbnistvoForm(request.POST,instance=pacient)
        if sform.is_valid():
            if (Pacient.objects.filter(st_kartice=sform.cleaned_data['st_kartice']).exists() and sform.cleaned_data['st_kartice'] != pacient.st_kartice):
                context['napaka'] = "Številka kartice že obstaja"
                print(context['napaka'])
                return render(request, 'patronaza/urediSkrbnistvo.html', context)
            if(not sform.telefon_regex()):
                context['napaka'] = "Nepravilen format telefonske številke"
                context['skrbnistvoForm'] = sform
                print(context['napaka'])
                return render(request, 'patronaza/urediSkrbnistvo.html', context)
            if(not sform.date_valid()):
                context['napaka'] = "Nepravilna oblika datuma. Pravilna oblika %d.%m.%Y"
                print(context['napaka'])
                context['skrbnistvoForm'] = sform
                return render(request, 'patronaza/urediSkrbnistvo.html', context)
            sform.save()
            return HttpResponseRedirect(reverse('pregled_skrbnistev'))
        context['napaka'] = "Nepravilna oblika datuma. Pravilna oblika %d.%m.%Y"
    return render(request, 'patronaza/urediSkrbnistvo.html', context)

def aktivacija(request,ur_id,date):
    context = {'potekla':False}
    hashids = Hashids(salt="salt1234")
    id = hashids.decode(ur_id)
    ur = User.objects.get(pk=int(id[0]))
    if request.method == 'POST':
        time = datetime.datetime.now().time()
        date = datetime.datetime.now().date()
        sendString = "Pozdravljeni \n Ustvarili ste si račun za uporabo naše" \
                     " aplikacije Patronažna služba. Da se boste lahko prijavili prosimo odprite spodnjo povezavo\n" \
                     "https://patronaza.herokuapp.com/patronaza/aktivacija/" + hashids.encode(ur.id) + "/" + str(
            date) + "*" + str(time)
        posli_email(sendString, str('testko.test2@gmail.com'))
        return HttpResponseRedirect(reverse('login'))
    (d,t) = date.split("*")
    print(d,t)
    date = datetime.datetime.strptime(d,'%Y-%m-%d').date()
    time = datetime.datetime.strptime(t,'%H:%M:%S.%f').time()
    timeNow = datetime.datetime.now()
    if( (timeNow - datetime.datetime.combine(date,time)).days < 2):
        ur.is_active = True
        ur.save()
        return render(request, 'patronaza/aktivacija.html', context)
    context['potekla'] = True
    return render(request, 'patronaza/aktivacija.html', context)

@login_required
def izpisi_delavne_naloge(request):
    context = {'ime': ''}
    oseba = None
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
        oseba = Osebje.objects.get(id_racuna=request.user)
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    else:
        ime = request.user.username
    context['ime'] = ime
    context['oseba'] = oseba
    obiski = VrstaObiska.objects.all()
    zdravniki = None
    sestre = None
    dn_list = Oskrba.objects.filter(id_pacient__lastnik_racuna=True)
    dodeljeno = DodeljenoOsebje.objects.all()
    if (request.user.groups.all()[0].name == 'Patronažna sestra'):
        dn_list = dn_list.filter(id_pacient__id_okolis=oseba.okolis)
        dodeljeno = DodeljenoOsebje.objects.filter(Q(id_osebja=oseba) | Q(id_nadomestna=oseba))
        dn = DelovniNalog.objects.raw('SELECT d.* FROM delovni_nalog d, dodeljeno_osebje dodeljeno,'
                                      ' obisk o WHERE d.id = o.id_dn AND o.id = dodeljeno.id_obisk '
                                      'AND (dodeljeno.id_osebja=' + str(oseba.id) + 'OR dodeljeno.id_nadomestna=' + str(
            oseba.id) + ')')
        dn_list = dn_list.filter(id_dn__in=dn)
        zdravniki = Osebje.objects.filter(Q(id_racuna__groups__name='Zdravnik') | Q(id_racuna__groups__name='Vodja patronaže'))
    elif (request.user.groups.all()[0].name == 'Zdravnik'):
        dn_list = dn_list.filter(id_dn__id_osebje=oseba)
        sestre = Osebje.objects.filter(id_racuna__groups__name='Patronažna sestra')
    else:
        zdravniki = Osebje.objects.filter(Q(id_racuna__groups__name='Zdravnik') | Q(id_racuna__groups__name='Vodja patronaže'))
        sestre = Osebje.objects.filter(id_racuna__groups__name='Patronažna sestra')
    context['obiski'] = obiski
    context['zdravniki'] = zdravniki
    context['sestre'] = sestre
    if request.method == 'POST':
        izdajatelj = request.POST.get('izdajatelj', False)
        sestra = request.POST.get('sestra', False)
        nadomestnaSestra = request.POST.get('nadomestnaSestra', False)
        pacient = request.POST.get('pacient', False)
        od = request.POST.get('od', False)
        do = request.POST.get('do', False)
        error = False
        if (od and do):
            try:
                datetime.datetime.strptime(od, '%d.%m.%Y')
                datetime.datetime.strptime(do, '%d.%m.%Y')
            except:
                error = "Nepravilen format datuma. Pravilen format d.m.Y"
                pass
            if (not error):
                od = datetime.datetime.strptime(datetime.datetime.strptime(od, '%d.%m.%Y').strftime('%Y-%m-%d'),
                                                '%Y-%m-%d').date()
                do = datetime.datetime.strptime(datetime.datetime.strptime(do, '%d.%m.%Y').strftime('%Y-%m-%d'),
                                                '%Y-%m-%d').date()
        elif ((od and not do) or (not od and do)):
            error = "Izpolni oba datuma."
        vrsta = request.POST.get('vrsta', False)
        context['izdajatelj'] = izdajatelj
        context['sestraSifra'] = sestra
        context['nadomestnaSestra'] = nadomestnaSestra
        context['pacient'] = pacient
        if(vrsta):
            context['vrstaDN'] = int(vrsta)
        else:
            context['vrstaDN'] = vrsta
        print(context['vrstaDN'])
        context['odDatum'] = od
        context['doDatum'] = do
        if (izdajatelj):
            dn_list = dn_list.filter(id_dn__id_osebje__sifra=izdajatelj)
        if (pacient):
            dn_list = dn_list.filter(Q(id_pacient__ime__contains=pacient) | Q(id_pacient__priimek__contains=pacient))

        if (sestra and nadomestnaSestra and sestra == nadomestnaSestra):
            medicinska = Osebje.objects.get(sifra=sestra)
            dn = DelovniNalog.objects.raw('SELECT d.* FROM delovni_nalog d, dodeljeno_osebje dodeljeno,'
                                          ' obisk o WHERE d.id = o.id_dn AND o.id = dodeljeno.id_obisk '
                                          'AND (dodeljeno.id_osebja=' + str(
                medicinska.id) + 'OR dodeljeno.id_nadomestna=' + str(medicinska.id) + ')')

            dn_list = dn_list.filter(id_dn__in=dn)
        else:
            if (sestra):
                medicinska = Osebje.objects.get(sifra=sestra)
                dodeljeno = dodeljeno.filter(id_osebja__sifra=sestra)
                dn_list = dn_list.filter(id_pacient__id_okolis=medicinska.okolis)
            # to spodaj je narobe
            if (nadomestnaSestra):
                medicinska = Osebje.objects.get(sifra=nadomestnaSestra)
                dodeljeno = dodeljeno.filter(id_nadomestna=medicinska)
                dn = DelovniNalog.objects.raw('SELECT d.* FROM delovni_nalog d, dodeljeno_osebje dodeljeno,'
                                              ' obisk o WHERE d.id = o.id_dn AND o.id = dodeljeno.id_obisk '
                                              'AND (dodeljeno.id_nadomestna=' + str(medicinska.id) + ')')
                dn_list = dn_list.filter(id_dn__in=dn)
        if (od and do and not error):
            dn_list = dn_list.filter(id_dn__datum_prvega_obiska__range=(od, do))
        if (vrsta):
            dn_list = dn_list.filter(id_dn__id_vrsta__id=vrsta)
        context['error'] = error
    result = {}
    for d in dn_list:
        result.setdefault(d.id_dn.id,[]).append(d)
        zadolzenaSestra = None
        nadomestnaSestra = '/'
        for p in dodeljeno.filter(id_obisk__id_dn=d.id_dn):
            if zadolzenaSestra == None and p.id_osebja != None:
                zadolzenaSestra = p.id_osebja
            if nadomestnaSestra == '/' and p.id_nadomestna != None:
                nadomestnaSestra = p.id_nadomestna
        result[d.id_dn.id].append([zadolzenaSestra,nadomestnaSestra])
    paginator = Paginator(dn_list, 15)  # Show 10 contacts per page
    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        contacts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        contacts = paginator.page(paginator.num_pages)
    context['delavniNalogi'] = dn_list
    context['result'] = result
    context['paginator'] = result.items()
    return render(request, 'patronaza/izpisiDelavneNaloge.html', context)

@login_required
def izpisi_obiske(request):
    context = {'ime': ''}
    oseba = None
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
        oseba = Osebje.objects.get(id_racuna=request.user)
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    else:
        ime = request.user.username
    context['ime'] = ime
    context['oseba'] = oseba

    obiski = VrstaObiska.objects.all()
    statusi = StatusObiska.objects.all()
    zdravniki = None
    sestre = None
    dn_list = Oskrba.objects.filter(id_pacient__lastnik_racuna=True)
    dodeljeno = DodeljenoOsebje.objects.all()
    obiski_tmp = Obisk.objects.all()
    obiski_list = []
    pacient_list = []
    sestra_list = []
    nadomestnaSestra_list = []

    if (request.user.groups.all()[0].name == 'Patronažna sestra'):
        #   dn_list = dn_list.filter(id_pacient__id_okolis=oseba.okolis)
        dodeljeno = DodeljenoOsebje.objects.filter(Q(id_osebja=oseba) | Q(id_nadomestna=oseba))
        dodeljenoOsebje = DodeljenoOsebje.objects.filter(Q(id_osebja=oseba) | Q(id_nadomestna=oseba)).values('id_obisk')
        obiski_tmp = obiski_tmp.filter(id__in=dodeljenoOsebje)
        zdravniki = Osebje.objects.filter(
            Q(id_racuna__groups__name='Zdravnik') | Q(id_racuna__groups__name='Vodja patronaže'))
    elif (request.user.groups.all()[0].name == 'Zdravnik'):
        dn_list = dn_list.filter(id_dn__id_osebje=oseba)
        sestre = Osebje.objects.filter(id_racuna__groups__name='Patronažna sestra')
    else:
        zdravniki = Osebje.objects.filter(
            Q(id_racuna__groups__name='Zdravnik') | Q(id_racuna__groups__name='Vodja patronaže'))
        sestre = Osebje.objects.filter(id_racuna__groups__name='Patronažna sestra')
    context['obiski'] = obiski
    context['statusi'] = statusi
    context['zdravniki'] = zdravniki
    context['sestre'] = sestre

    # requested_status = ""


    if request.method == 'POST':
        izdajatelj = request.POST.get('izdajatelj', False)
        sestra = request.POST.get('sestra', False)
        nadomestnaSestra = request.POST.get('nadomestnaSestra', False)
        pacient = request.POST.get('pacient', False)
        odDejanski = request.POST.get('odDejanski', False)
        doDejanski = request.POST.get('doDejanski', False)
        odPredviden = request.POST.get('odPredviden', False)
        doPredviden = request.POST.get('doPredviden', False)
        error = False
        if (odDejanski and doDejanski):
            try:
                datetime.datetime.strptime(odDejanski, '%d.%m.%Y')
                datetime.datetime.strptime(doDejanski, '%d.%m.%Y')
            except:
                error = "Nepravilen format datuma. Pravilen format d.m.Y"
                pass
            if (not error):
                odDejanski = datetime.datetime.strptime(
                    datetime.datetime.strptime(odDejanski, '%d.%m.%Y').strftime('%Y-%m-%d'),
                    '%Y-%m-%d').date()
                doDejanski = datetime.datetime.strptime(
                    datetime.datetime.strptime(doDejanski, '%d.%m.%Y').strftime('%Y-%m-%d'),
                    '%Y-%m-%d').date()
        elif ((odDejanski and not doDejanski) or (not odDejanski and doDejanski)):
            error = "Izpolni oba datuma."

        if (odPredviden and doPredviden):
            try:
                datetime.datetime.strptime(odPredviden, '%d.%m.%Y')
                datetime.datetime.strptime(doPredviden, '%d.%m.%Y')
            except:
                error = "Nepravilen format datuma. Pravilen format d.m.Y"
                pass
            if (not error):
                odPredviden = datetime.datetime.strptime(
                    datetime.datetime.strptime(odPredviden, '%d.%m.%Y').strftime('%Y-%m-%d'),
                    '%Y-%m-%d').date()
                doPredviden = datetime.datetime.strptime(
                    datetime.datetime.strptime(doPredviden, '%d.%m.%Y').strftime('%Y-%m-%d'),
                    '%Y-%m-%d').date()
        elif ((odPredviden and not doPredviden) or (not odPredviden and doPredviden)):
            error = "Izpolni oba datuma."

        vrsta = request.POST.get('vrsta', False)
        status = request.POST.get('status', False)

        context['izdajatelj'] = izdajatelj
        context['sestraSifra'] = sestra
        context['nadomestnaSestra'] = nadomestnaSestra
        context['pacient'] = pacient
        context['odDatumDejanski'] = odDejanski
        context['doDatumDejanski'] = doDejanski
        context['odDatumPredviden'] = odPredviden
        context['doDatumPredviden'] = doPredviden
        context['vrsta'] = vrsta
        context['status'] = status

        if (izdajatelj):
            dn_list = dn_list.filter(id_dn__id_osebje__sifra=izdajatelj)
        if (pacient):
            dn_list = dn_list.filter(Q(id_pacient__ime__contains=pacient) | Q(id_pacient__priimek__contains=pacient))
        if (sestra and nadomestnaSestra and sestra == nadomestnaSestra):
            medicinska = Osebje.objects.get(sifra=sestra)
            dodeljenoOsebje = DodeljenoOsebje.objects.filter(
                Q(id_osebja=medicinska) | Q(id_nadomestna=medicinska)).values('id_obisk')
            obiski_tmp = obiski_tmp.filter(id__in=dodeljenoOsebje)
        else:
            if (sestra):
                medicinska = Osebje.objects.get(sifra=sestra)
                dodeljenoOsebje = DodeljenoOsebje.objects.filter(id_osebja=medicinska).values('id_obisk')
                obiski_tmp = obiski_tmp.filter(id__in=dodeljenoOsebje)

            if (nadomestnaSestra):
                medicinska = Osebje.objects.get(sifra=nadomestnaSestra)
                dodeljenoOsebje = DodeljenoOsebje.objects.filter(id_nadomestna=medicinska).values('id_obisk')
                obiski_tmp = obiski_tmp.filter(id__in=dodeljenoOsebje)

        if (odDejanski and doDejanski and not error):
            obiski_tmp = obiski_tmp.filter(datum_obiska__range=(odDejanski, doDejanski))
        if (odPredviden and doPredviden and not error):
            obiski_tmp = obiski_tmp.filter(predviden_datum__range=(odPredviden, doPredviden))
        if (vrsta):
            dn_list = dn_list.filter(id_dn__id_vrsta__id=vrsta)
        if (status):
            obiski_tmp = obiski_tmp.filter(status_obiska__naziv=status)

    for dn in dn_list:
        o = obiski_tmp.filter(id_dn=dn.id_dn)
        obiski_list = list(chain(obiski_list, o))
        p = dn.id_pacient
        for ob in o:
            pacient_list.append(p)

    for obisk in obiski_list:
        dodeljeno = DodeljenoOsebje.objects.get(id_obisk=obisk.id)
        medicinska = None
        nadomestnaSestra = '/'

        if dodeljeno.id_osebja != None:
            medicinska = dodeljeno.id_osebja
        if dodeljeno.id_nadomestna != None:
            nadomestnaSestra = dodeljeno.id_nadomestna

        sestra_list.append(medicinska)
        nadomestnaSestra_list.append(nadomestnaSestra)

    paginator = Paginator(obiski_list, 30)  # Show 30 contacts per page

    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        contacts = paginator.page(paginator.num_pages)
    context['obiski_list'] = obiski_list
    context['sestra_list'] = sestra_list
    context['nadomestnaSestra_list'] = nadomestnaSestra_list
    context['pacient_list'] = pacient_list
    context['loop_times'] = range(len(pacient_list))
    context['paginator'] = contacts
    return render(request, 'patronaza/izpisiObiske.html', context)

@login_required
def izpisi_obiske_pacient(request):
    context = {'ime': ''}
    oseba = None
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
        oseba = Osebje.objects.get(id_racuna=request.user)
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = "Pacient " + str(Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0])
    else:
        ime = request.user.username
    context['ime'] = ime
    context['oseba'] = oseba

    dn_list = Oskrba.objects.filter(id_pacient__lastnik_racuna=True)
    obiski_tmp = Obisk.objects.all()
    pacienti = Pacient.objects.filter(id_racuna=request.user)
    pacient1 = pacienti[0]
    pacient2 = None
    pacient3 = None
    if len(pacienti) == 2:
        pacient2 = pacienti[1]
    if len(pacienti) == 3:
        pacient2 = pacienti[1]
        pacient3 = pacienti[2]

    obiski_list = []
    pacient_list = []
    sestra_list = []
    nadomestnaSestra_list = []

    if len(pacienti) == 1:
        dn_list = dn_list.filter(Q(id_pacient__ime=pacient1.ime) & Q(id_pacient__priimek=pacient1.priimek))
    elif len(pacienti) == 2:
        dn_list = dn_list.filter((Q(id_pacient__ime=pacient1.ime) & Q(id_pacient__priimek=pacient1.priimek)) | (
        Q(id_pacient__ime=pacient2.ime) & Q(id_pacient__priimek=pacient2.priimek)))
    elif len(pacienti) == 3:
        dn_list = dn_list.filter((Q(id_pacient__ime=pacient1.ime) & Q(id_pacient__priimek=pacient1.priimek)) | (
        Q(id_pacient__ime=pacient2.ime) & Q(id_pacient__priimek=pacient2.priimek)) | (
                                 Q(id_pacient__ime=pacient3.ime) & Q(id_pacient__priimek=pacient3.priimek)))

    obiski_tmp = obiski_tmp.filter(status_obiska__naziv="opravljen")

    for dn in dn_list:
        o = obiski_tmp.filter(id_dn=dn.id_dn)
        obiski_list = list(chain(obiski_list, o))
        p = dn.id_pacient
        for ob in o:
            pacient_list.append(p)

    for obisk in obiski_list:
        dodeljeno = DodeljenoOsebje.objects.get(id_obisk=obisk.id)
        medicinska = None
        nadomestnaSestra = '/'

        if dodeljeno.id_osebja != None:
            medicinska = dodeljeno.id_osebja
        if dodeljeno.id_nadomestna != None:
            nadomestnaSestra = dodeljeno.id_nadomestna

        sestra_list.append(medicinska)
        nadomestnaSestra_list.append(nadomestnaSestra)

    paginator = Paginator(obiski_list, 30)  # Show 30 contacts per page

    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        contacts = paginator.page(paginator.num_pages)

    context['obiski_list'] = obiski_list
    context['sestra_list'] = sestra_list
    context['nadomestnaSestra_list'] = nadomestnaSestra_list
    context['pacient_list'] = pacient_list
    context['loop_times'] = range(len(pacient_list))
    context['paginator'] = contacts
    return render(request, 'patronaza/izpisiObiskePacient.html', context)

@login_required
def nadomescanje(request):
    context={'datum': False, 'vecji' :False, 'sestra1': False, 'sestra2': False, 'datumOd': False, 'datumDo': False, 'nadomestneSestre': None, 'danes': None}
    osebje = Osebje.objects.get(id_racuna=request.user)
    ime = "Vodja patronaze " + str(osebje)
    context['ime'] = ime
    sestre = Osebje.objects.filter(id_racuna__groups__name='Patronažna sestra')
    context['sestre'] = sestre
    context['nadomestniObiski'] = DodeljenoOsebje.objects.exclude(id_nadomestna=None).filter(id_obisk__status_obiska_id=1).order_by('id_osebja', 'id_obisk__predviden_datum')
    context['nadomestneSestre'] = context['nadomestniObiski'].order_by('id_osebja', '-id_obisk__predviden_datum').distinct('id_osebja')
    context['danes'] = date.today()
    if request.method == 'POST':
        if request.POST.get('preklic'):
            list_izbranih = request.POST.getlist('obisk')
            DodeljenoOsebje.objects.filter(id_obisk__id__in=list_izbranih).update(id_nadomestna=None)
        else:
            sestra1 = Osebje.objects.get(sifra = request.POST.get('sestra'))
            sestra2 = Osebje.objects.get(sifra = request.POST.get('nadomestnaSestra'))
            od = request.POST.get('od')
            do = request.POST.get('do')
            error = False
            context['sestra1'] = sestra1
            context['sestra2'] = sestra2
            context['datumOd'] = od
            context['datumDo'] = do
            context['error'] = error
            try:
                datetime.datetime.strptime(od, '%d.%m.%Y')
                datetime.datetime.strptime(do, '%d.%m.%Y')
            except:
                error = "Nepravilen format datuma. Pravilen format d.m.Y"
                context['error'] = error
                return render(request, 'patronaza/nadomescanja.html', context)
            if (not error):
                od = datetime.datetime.strptime(datetime.datetime.strptime(od, '%d.%m.%Y').strftime('%Y-%m-%d'),
                                                '%Y-%m-%d').date()
                do = datetime.datetime.strptime(datetime.datetime.strptime(do, '%d.%m.%Y').strftime('%Y-%m-%d'),
                                                '%Y-%m-%d').date()
            if(od < datetime.datetime.now().date() or do < datetime.datetime.now().date()):
                context['datum'] = True
                return render(request, 'patronaza/nadomescanja.html', context)
            if(od > do):
                context['vecji'] = True
                return render(request, 'patronaza/nadomescanja.html', context)
            dodeljeno = DodeljenoOsebje.objects.filter(Q(id_osebja=sestra1) | Q(id_nadomestna=sestra1))\
                .filter(id_obisk__status_obiska=1).filter(id_obisk__datum_obiska__range=(od, do)).update(id_nadomestna=sestra2)
            dodeljeno2 = DodeljenoOsebje.objects.filter(id_osebja=sestra2,id_nadomestna=sestra2)\
                .filter(id_obisk__status_obiska=1).filter(id_obisk__datum_obiska__range=(od, do)).update(id_nadomestna=None)
            return HttpResponseRedirect('/patronaza/domov')
    elif request.method == 'GET':
        for key in request.GET.keys():
            if key.startswith('preklic-'):
                id_sestre = key[8:]
                DodeljenoOsebje.objects.filter(id_osebja_id=id_sestre).update(id_nadomestna=None)


    return render(request, 'patronaza/nadomescanja.html', context)

@login_required
def delovni_nalog_podrobnosti(request,id):
    context={}
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    else:
        ime = request.user.username
    context['ime'] = ime
    dn = DelovniNalog.objects.get(pk=id)
    return render(request, 'patronaza/test.html', context)

@login_required
def osebjeAdd(request):
    context = {}
    ime = request.user.username
    context['ime'] = ime
    if request.method == 'POST':
        uForm = UporabniskiForm(request.POST, request.FILES)
        oForm = OsebjeForm(request.POST, request.FILES)
        uoForm = UporabniskiOkolisForm(request.POST, request.FILES)

        if uForm.is_valid() and oForm.is_valid():
            if (not uForm.password_regex()):
                context['regex'] = True
                context['uForm'] = uForm
                context['oForm'] = oForm
                context['uoForm'] = uoForm
                return render(request, "patronaza/osebjeAdd.html", context)

            u = User.objects.create_user(username=uForm.cleaned_data['email'], email=uForm.cleaned_data['email'],
                                         password=uForm.cleaned_data['password'], is_active=True)
            u.save()
            o = oForm.save(commit=False)
            o.id_racuna = u
            o.izbrisan = 0
            if uoForm.is_valid():
                o.okolis=uoForm.cleaned_data['okolis']
            o.save()
            uForm.cleaned_data['groups'].user_set.add(u)
            return HttpResponseRedirect(reverse('index'))
    else:
        uForm = UporabniskiForm()
        oForm = OsebjeForm()
        uoForm = UporabniskiOkolisForm()

    context['uForm'] = uForm
    context['oForm'] = oForm
    context['uoForm'] = uoForm

    return render(request, "patronaza/osebjeAdd.html", context)

@login_required
def planiranje_obiskov(request):
    context = {'ime': str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))}
    dan = request.GET.get("dan")
    mesec = request.GET.get("mesec")
    leto = request.GET.get("leto")

    try:
        datum = date(int(leto), int(mesec), int(dan))
        if datum < date.today():
            datum = date.today() + timedelta(days=1)
    except:
        datum = date.today() + timedelta(days=1)

    if request.method == 'POST':
        form = PlaniranjeObiskovForm(request.POST)
        obiski_query = form.fields['obiski'].queryset.filter(
            (Q(id_osebja__id_racuna=request.user) & Q(id_nadomestna__id_racuna=None)) |
                Q(id_nadomestna__id_racuna=request.user))
        if form.is_valid():
            id_list = request.POST.getlist('obisk')
            pobrisani = obiski_query.filter(id_obisk__izbran_datum=datum)
            for item in pobrisani:
                item.id_obisk.izbran_datum = None
                item.id_obisk.save()

            for id in id_list:
                obisk = obiski_query.get(id_obisk__id=id)
                obisk.id_obisk.izbran_datum = datum
                obisk.id_obisk.save()
                obisk.save()
    else:
        form = PlaniranjeObiskovForm()
        obiski_query = form.fields['obiski'].queryset.filter((Q(id_osebja__id_racuna=request.user) & Q(id_nadomestna__id_racuna=None)) | Q(id_nadomestna__id_racuna=request.user))

    context['objekti'] = obiski_query
    context['izbrani'] = obiski_query.filter(id_obisk__izbran_datum=datum)
    context['obvezni'] = obiski_query.filter(id_obisk__obvezen=0)
    context['datumPrikaza'] = datum
    context['planObiskovForm'] = form
    return render(request, 'patronaza/plan_obiskov.html', context)

@login_required
def posodabljane_pacienta(request):
    context = {'napaka': False}
    pacient = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    ur = request.user
    context['ime'] = "Pacient " + str(pacient)
    pacient.datum_rojstva = pacient.datum_rojstva.strftime('%d.%m.%Y')
    pacientForm = PacientForm(instance=pacient)
    emailForm = UporabniskiRacunEmailForm(instance=request.user)
    context['kontakt'] = KontaktnaOseba.objects.filter(pacient=pacient).exists()
    context['pacientForm'] = pacientForm
    context['emailForm'] = emailForm
    if request.method == 'POST':
        pform = PacientForm(request.POST,instance=pacient)
        eform = UporabniskiRacunEmailForm(request.POST,instance=ur)
        if pform.is_valid() and eform.is_valid():
            if (Pacient.objects.filter(st_kartice=pform.cleaned_data['st_kartice']).exists() and pform.cleaned_data['st_kartice'] != pacient.st_kartice):
                context['napaka'] = "Ta stevilka kartice že obstaja."
                return render(request, 'patronaza/registracija.html', context)
            elif (User.objects.filter(email=eform.cleaned_data['email']).exists() and eform.cleaned_data['email'] != ur.email):
                context['napaka'] = "Email že obstaja."
                return render(request, 'patronaza/registracija.html', context)
            if(not pform.date_valid()):
                context['napaka'] = "Napačna oblika datuma. Pravilna oblika %d.%m.%Y"
                print("date")
                return render(request, 'patronaza/posodabljanje_pacienta.html', context)
            if(not pform.telefon_regex()):
                context['napaka'] = "Ni telefonska številka"
                print("telefon")
                return render(request,'patronaza/posodabljanje_pacienta.html',context)
            pform.save()
            ur.email = eform.cleaned_data['email']
            ur.username = eform.cleaned_data['email']
            ur.save()
            context['pacientForm'] = pform
            context['emailForm'] = eform

    return render(request, 'patronaza/posodabljanje_pacienta.html', context)

@login_required
def uredi_kontakt(request):
    context = {}
    pacient = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = "Pacient " + str(pacient)
    kontaktnaOseba = None
    kontaktForm = KontaktForm()
    if KontaktnaOseba.objects.filter(pacient__id_racuna=request.user).exists():
        kontaktnaOseba = KontaktnaOseba.objects.get(pacient__id_racuna=request.user)
    if kontaktnaOseba:
        kontaktForm = KontaktForm(instance=kontaktnaOseba)
    context['kontaktForm'] = kontaktForm
    if request.method == 'POST':
        if kontaktnaOseba:
            kontaktForm = KontaktForm(request.POST,instance=kontaktnaOseba)
        else:
            kontaktForm = KontaktForm(request.POST)

        if kontaktForm.is_valid():
            if kontaktnaOseba:
                kontaktForm.save()
            else:
                kontakt = kontaktForm.save(commit=False)
                kontakt.pacient = pacient
                kontakt.save()
            context['kontaktForm'] = kontaktForm

    return render(request, 'patronaza/uredi_kontakt.html', context)
register = template.Library()
@register.filter(name='cut')
def cut(value, arg):
    return value.replace(arg, '')

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

@login_required
def meritve(request, obiskId):
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
        name = str(request.user.groups.all()[0].name) + ' ' + str(Osebje.objects.get(id_racuna=request.user))
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    else:
        ime = request.user.username

    #if this is a POST request we need to process the form data
    if request.method == 'POST':
        for key, value in request.POST.items():
            if(value != '' and RepresentsInt(key) and OstaliPodatki.objects.filter(id_obisk_id=obiskId, id_podatki_aktivnosti_id=key).exists()):
                op = OstaliPodatki.objects.get(id_obisk_id=obiskId, id_podatki_aktivnosti_id=key)
                op.vrednost = value;

                op.save()
            elif(value != '' and RepresentsInt(key)):
                if(key == '26' or key == '29' or key == '30'):
                    glavniObisk = Obisk.objects.get(id=obiskId)
                    obiski = Obisk.objects.filter(id_dn=glavniObisk.id_dn)
                    for obisk in obiski:
                        op = OstaliPodatki(id_obisk=obisk,
                                           id_podatki_aktivnosti_id=key,
                                           vrednost=value)
                        op.save()
                else:
                    op = OstaliPodatki(id_obisk_id=obiskId,
                                       id_podatki_aktivnosti_id=key,
                                       vrednost=value)
                    op.save()
        if request.POST.get('end'):
            obisk = Obisk.objects.get(pk=obiskId)
            status = StatusObiska.objects.get(pk=2)
            obisk.status_obiska = status
            print(obisk.status_obiska.id)
            obisk.save()
        return HttpResponseRedirect('/patronaza/domov')

    ostaliPodatki = OstaliPodatki.objects.filter(id_obisk = obiskId)
    izbraniObisk = Obisk.objects.get(id=obiskId)
    dn = izbraniObisk.id_dn

    vsiPodatki = PodatkiAktivnosti.objects.all()


    return render(request, 'patronaza/meritve.html', {
        'obisk': izbraniObisk,
        'ostaliPodatki': ostaliPodatki,
        'delovniNalog': dn,
        'vsiPodatki': vsiPodatki,
        'ime': name,
    })

def pridobiStevilko(request, obiskId, podatkiAktivnostId):
    op = OstaliPodatki.objects.filter(id_obisk_id=obiskId, id_podatki_aktivnosti_id=podatkiAktivnostId)

    if (op.exists()):
        vrednost = {
            'vrednost': op[0].vrednost,
        }
    else:
        vrednost = {
            'vrednost': 0,
        }

    data = simplejson.dumps(vrednost)
    return HttpResponse(data, content_type='application/json')

def pridobiDatum(request, obiskId, podatkiAktivnostId):
    op = OstaliPodatki.objects.filter(id_obisk_id=obiskId, id_podatki_aktivnosti_id=podatkiAktivnostId)

    if (op.exists()):
        vrednost = {
            'vrednost': op[0].vrednost,
        }
    else:
        vrednost = {
            'vrednost': None,
        }

    data = simplejson.dumps(vrednost)
    return HttpResponse(data, content_type='application/json')

def pridobiNiz(request, obiskId, podatkiAktivnostId):
    op = OstaliPodatki.objects.filter(id_obisk_id=obiskId, id_podatki_aktivnosti_id=podatkiAktivnostId)

    if (op.exists()):
        vrednost = {
            'vrednost': op[0].vrednost,
        }
    else:
        vrednost = {
            'vrednost': '',
        }

    data = simplejson.dumps(vrednost)
    return HttpResponse(data, content_type='application/json')