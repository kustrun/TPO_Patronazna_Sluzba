# -*- coding: utf-8 -*-

from django.shortcuts import render
from django import forms
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
from datetime import timedelta
from .auth import EmailBackend, BlackListBackend

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
                        params={'pacient': pacient},
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
def delovniNalog(request, delovniNalogId=0):
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
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

    if delovniNalogId != 0:
        delovniNalogDB = DelovniNalog.objects.get(id=delovniNalogId)
        obiskDB = Obisk.objects.filter(id_dn=delovniNalogDB)[0]
        dodeljenoOsebjeDB = DodeljenoOsebje.objects.get(id_obisk=obiskDB)
        osebjeDB = dodeljenoOsebjeDB.id_osebja
        vrstaObiskaDB = delovniNalogDB.id_vrsta
        tipObiskaDB = vrstaObiskaDB.tip
        injekcijeDB = Injekcije.objects.filter(id_obisk=obiskDB)
        odvzemKrviDB = OdvzemKrvi.objects.filter(id_obisk=obiskDB)
        pacientiDB = Oskrba.objects.filter(id_dn=delovniNalogDB)

        osebje.fields["sifraVnos"].initial = osebjeDB.sifra
        osebje.fields["ime"].initial = osebjeDB.ime
        osebje.fields["priimek"].initial = osebjeDB.priimek

        delovniNalog.fields["datum_prvega_obiska"].initial = delovniNalogDB.datum_prvega_obiska
        delovniNalog.fields["tip_prvega_obiska"].initial = 'obvezen'
        delovniNalog.fields["st_obiskov"].initial = delovniNalogDB.st_obiskov
        delovniNalog.fields["cas_med_dvema"].initial = delovniNalogDB.cas_med_dvema
        delovniNalog.fields["casovno_obdobje"].initial = delovniNalogDB.casovno_obdobje

        tipObiska.fields["tip"].initial = tipObiskaDB.tip

        vrstaObiska.fields["vrstaObiska"].initial = vrstaObiskaDB.naziv

        pacientiLen = len(pacientiDB)
        IzberiPacientaFormSet = formset_factory(DelovniNalogPacientForm, formset=BasePacientaFormSet, extra=pacientiLen)
        izberiPacientaFormSet = IzberiPacientaFormSet(prefix='izberiPacienta')

        for i in range(0, pacientiLen):
            izberiPacientaFormSet[i].fields["ime"].initial = pacientiDB[i].id_pacient.st_kartice + ": " + pacientiDB[
                i].id_pacient.ime + " " + pacientiDB[i].id_pacient.priimek

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
            dn.id_vrsta = VrstaObiska.objects.get(naziv=vrstaObiska.data['vrstaObiska'],
                                                  tip=TipObiska.objects.get(tip=tipObiska.data['tip']))
            dn.vrsta_storitve = VrstaStoritve.objects.get(naziv="obisk")  # zakaj se uporablja to polje?
            dn.status_dn = StatusDn.objects.get(naziv="aktiven")

            dn.save()

            # SHRANI OSKRBO PACIENTA
            pacientovOkolis = None
            for pacient in izberiPacientaFormSet:
                pacientSplit = str(pacient.cleaned_data.get('ime')).split(":")

                trenutniPacient = Pacient.objects.get(st_kartice=pacientSplit[0])
                pacientovOkolis = trenutniPacient.id_okolis

                os = Oskrba(
                    id_dn=dn,
                    id_pacient=trenutniPacient
                )

                os.save()

            '''print([x.user for x in (AuthUserGroups.objects.filter(group=AuthGroup.objects.get(name='Patronažna sestra')))])

            vsePatronazneSestre = Osebje.objects.filter(id_racuna2__in=[x.user for x in (
            AuthUserGroups.objects.filter(group=AuthGroup.objects.get(name='Patronažna sestra')))],
                                                        okolis=pacientovOkolis)

            print(vsePatronazneSestre)

            min = 10000
            izbranaPS = None
            for patronaznaSestra in vsePatronazneSestre:
                obiski = DodeljenoOsebje.objects.filter(id_osebja=patronaznaSestra,
                                                        id_obisk__in=[x for x in (Obisk.objects.filter(
                                                            id_dn__in=[y for y in DelovniNalog.objects.filter(
                                                                status_dn=StatusDn.objects.get(naziv="aktiven"))]))],
                                                        je_zadolzena=0)

                if (int(len(obiski)) < min):
                    min = len(obiski)
                    izbranaPS = patronaznaSestra
            '''

            # USTVARI USTREZNE OBISKE
            datum = dn.datum_prvega_obiska
            if datum.weekday() == 5:
                datum = datum + timedelta(days=2)
            elif datum.weekday() == 6:
                datum = datum + timedelta(days=1)

            for i in range(0, dn.st_obiskov):
                ob = Obisk(id_dn=dn,
                           zaporedna_st_obiska=(i + 1),
                           status_obiska=StatusObiska.objects.get(naziv="aktiven"),
                           # status obiska popravi na obvezen, neobvezen
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
                    id_osebja=Osebje.objects.get(sifra=ime.sifra),
                    je_zadolzena=0
                )

                print(Osebje.objects.get(id=15))

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
        'ime': ime
    })


@login_required
def index(request):
    context = {}
    ime = ''
    if(Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
    elif(Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna = True)[0]
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
            sendString = "https://patronaza.herokuapp.com/patronaza/aktivacija/" + ciphertext + "/" + str(date)+"*"+str(time)
            posli_email(sendString,str(u.email))
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
    ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = ime
    ur = request.user
    result = Pacient.objects.filter(id_racuna=ur).filter(lastnik_racuna = False)
    pacijenti = []
    for r in result:
        r.datum_rojstva = r.datum_rojstva.strftime('%d.%m.%Y')
        pacijenti.append(SkrbnistvoForm(instance=r))
    context['pacijenti'] = pacijenti
    return render(request, 'patronaza/pregled.html', context)

@login_required
def dodaj_skrbnistvo(request):
    context = {'skrbnistvoForm': SkrbnistvoForm(),'date':False, 'telefon':False}
    ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = ime
    if(request.method == 'POST'):
        sform = SkrbnistvoForm(request.POST)
        if sform.is_valid():
            if (Pacient.objects.filter(st_kartice=sform.cleaned_data['st_kartice']).exists()):
                context['kartica'] = True
                return render(request, 'patronaza/registracija.html', context)
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
    return render(request, 'patronaza/dodajSkrbnistvo.html', context)

def aktivacija(request,ur_id,date):
    context = {'potekla':False}
    hashids = Hashids(salt="salt1234")
    id = hashids.decode(ur_id)
    ur = User.objects.get(pk=int(id[0]))
    if request.method == 'POST':
        time = datetime.datetime.now().time()
        date = datetime.datetime.now().date()
        sendString = "https://patronaza.herokuapp.com/patronaza/aktivacija/" + ur_id + "/" + str(date) + "*" + str(time)
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
    context={'ime':''}
    oseba = None
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
        oseba = Osebje.objects.get(id_racuna=request.user)
    elif (Pacient.objects.filter(id_racuna=request.user).exists()):
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    else:
        ime = request.user.username
    context['ime'] = ime
    context['oseba'] = oseba
    obiski = VrstaObiska.objects.all()
    dn_list = Oskrba.objects.all()
    dodeljeno = DodeljenoOsebje.objects.all()
    context['obiski'] = obiski
    if request.method == 'POST':
        izdajatelj = request.POST.get('izdajatelj',False)
        sestra = request.POST.get('sestra', False)
        nadomestnaSestra = request.POST.get('nadomestnaSestra',False)
        pacient = request.POST.get('pacient',False)
        od = request.POST.get('od',False)
        do = request.POST.get('do',False)
        vrsta = request.POST.get('vrsta',False)
        if(izdajatelj):
            dn_list = dn_list.filter(id_dn__id_osebje__sifra=izdajatelj)
        if(pacient):
            dn_list = dn_list.filter(Q(id_pacient__ime__contains=pacient) | Q(id_pacient__priimek__contains=pacient))
        if(sestra):
            dodeljeno = dodeljeno.filter(id_osebja__sifra=sestra).filter(je_zadolzena=0)
        if(nadomestnaSestra):
            dodeljeno = dodeljeno.filter(id_osebja__sifra=nadomestnaSestra).filter(je_zadolzena=1)
        if(od and do):
            dn_list = dn_list.filter(id_dn__datum_prvega_obiska__range=(od,do))
        if(vrsta):
            dn_list = dn_list.filter(id_dn__id_vrsta__id=vrsta)
    hash = {}
    for d in dn_list:
        if(dodeljeno.filter(je_zadolzena=1).filter(id_obisk__id_dn=d.id_dn).exists()):
            hash[d] = [dodeljeno.filter(je_zadolzena=1).filter(id_obisk__id_dn=d.id_dn)[0].id_osebja,dodeljeno.filter(je_zadolzena=0).filter(id_obisk__id_dn=d.id_dn)[0].id_osebja]
        elif(dodeljeno.filter(je_zadolzena=0).filter(id_obisk__id_dn=d.id_dn).exists()):
            hash[d] = [dodeljeno.filter(je_zadolzena=0).filter(id_obisk__id_dn=d.id_dn)[0].id_osebja,'/']


    context['delavniNalogi'] = dn_list
    context['hash'] = hash
    return render(request, 'patronaza/izpisiDelavneNaloge.html', context)
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

        if uForm.is_valid() and oForm.is_valid():
            if (not uForm.password_regex()):
                context['regex'] = True
                context['uForm'] = uForm
                context['oForm'] = oForm
                return render(request, "patronaza/osebjeAdd.html", context)

            u = User.objects.create_user(username=uForm.cleaned_data['email'], email=uForm.cleaned_data['email'],
                                         password=uForm.cleaned_data['password'], is_active=True)
            u.save()
            o = oForm.save(commit=False)
            o.id_racuna = u
            o.izbrisan = 0
            o.save()
            uForm.cleaned_data['groups'].user_set.add(u)
            return HttpResponseRedirect(reverse('index'))
    else:
        uForm = UporabniskiForm()
        oForm = OsebjeForm()

    context['uForm'] = uForm
    context['oForm'] = oForm

    return render(request, "patronaza/osebjeAdd.html", context)
