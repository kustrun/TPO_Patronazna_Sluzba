from django.shortcuts import render
from django import forms
from django.forms import formset_factory
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from .forms import *
from .models import *
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
    else:
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    osebje = DelovniNalogOsebjeForm(initial={'sifra': 12345, 'ime': 'Domen', 'priimek': 'Balantič'})
    vrstaObiska = DelovniNalogVrstaObiskaForm()
    tipObiska = DelovniNalogTipObiskaForm()
    delovniNalog = DelovniNalogForm()

    # Create the formset, specifying the form and formset we want to use.
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
        zdravilaFormSet =  ZdravilaFormSet(request.POST, prefix='zdravila')
        barvaEpruvetFormSet = BarvaEpruvetFormSet(request.POST, prefix='barva')

        # check whether it's valid:
        if osebje.is_valid() and tipObiska.is_valid() and vrstaObiska.is_valid() and delovniNalog.is_valid() and zdravilaFormSet.is_valid() and barvaEpruvetFormSet.is_valid():

            #SHRANI DELOVNI NALOG
            dn = delovniNalog.save(commit=False)
            dn.id_osebje = Osebje.objects.get(šifra=osebje.data['sifra'], ime=osebje.data['ime'], priimek=osebje.data['priimek'])
            dn.id_vrsta = VrstaObiska.objects.get(id=vrstaObiska.data['vrstaObiska'], tip=TipObiska.objects.get(id=tipObiska.data['tip']))
            dn.vrsta_storitve=VrstaStoritve.objects.get(naziv="obisk") #zakaj se uporablja to polje?
            dn.status_dn=StatusDn.objects.get(naziv="aktiven")

            dn.save()

            #USTVARI USTREZNE OBISKE
            datum = dn.datum_prvega_obiska
            if datum.weekday() == 5:
                datum = datum + timedelta(days=2)
            elif datum.weekday() == 6:
                datum = datum + timedelta(days=1)

            for i in range(0, dn.st_obiskov):
                ob = Obisk(id_dn=dn,
                           zaporedna_st_obiska=(i+1),
                           status_obiska=StatusObiska.objects.get(naziv="aktiven"),
                           #status obiska popravi na obvezen, neobvezen
                           datum_obiska=datum,
                           predviden_datum=datum,
                           podrobnosti_obiska= ("%d. obisk" % (i+1)),
                           izbran_datum=datum,
                           cena=0.00)

                ob.save()

                #obisk dodeli medicinski sestri
                #TO DO: medicinsko sestro izberi na podlagi okrožja
                do = DodeljenoOsebje(
                    id_obisk=ob,
                    id_osebja=Osebje.objects.get(id=2),
                    je_zadolzena=0
                )

                do.save()

                #povecaj datum za naslednji obisk
                datum = datum + timedelta(days=(int(dn.cas_med_dvema) + 1))

                if datum.weekday() == 5:
                    datum = datum + timedelta(days=2)
                elif datum.weekday() == 6:
                    datum = datum + timedelta(days=1)

                # SHRANI APLIKACIJO INJEKCIJ
                for zdravila in zdravilaFormSet:
                    ij = Injekcije(
                        id_obisk=ob,
                        id_zdravilo = Zdravila.objects.get(naziv=zdravila.cleaned_data.get('naziv')),
                        st_injekcij = int(zdravila.cleaned_data.get('st_injekcij'))
                    )

                    ij.save()

                # SHRANI ODVZEM KRVI
                for barva in barvaEpruvetFormSet:
                    ok = OdvzemKrvi(
                        id_obisk=ob,
                        barva = BarvaEpruvete.objects.get(barva=barva.cleaned_data.get('barva')),
                        st_epruvet = int(barva.cleaned_data.get('st_epruvet'))
                    )

                    ok.save()


            return HttpResponseRedirect('/')



    return render(request, 'patronaza/delovniNalog.html', {
        'osebje': osebje,
        'tipObiska': tipObiska,
        'vrstaObiska': vrstaObiska,
        'delovniNalog': delovniNalog,
        'zdravilaFormSet': zdravilaFormSet,
        'barvaEpruvetFormSet': barvaEpruvetFormSet,
        'ime': ime,
        }
      )


@login_required
def index(request):
    context = {}
    ime = ''
    if(Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
    else:
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna = True)[0]
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
                    error = "Napacen email ali geslo"
                    ip_user = BlackListBackend().failed_login(ip=ip)
                    form = LoginForm()
        else:
            form = LoginForm()
            error = "Blokirani ste zaradi 3x zapored napacno vnesenih podatkov\nPreostali cas: " + BlackListBackend().lockup_to_string(
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


def change_password(request):
    context = {'passwordChangeForm': PasswordChangeForm()}

    if request.method == 'POST':
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
    return render(request, 'patronaza/change_password.html', context)

def registracija(request):
    context = {'uporabniskiRacunForm' : UporabniskiRacunForm(),'pacientForm' : PacientForm(),'regex' : False, 'match' : False}
    if request.method == 'POST':
        uform = UporabniskiRacunForm(request.POST)
        pform = PacientForm(request.POST)
        print(uform.errors,pform.errors)
        if uform.is_valid() and pform.is_valid():
            if(not uform.password_regex()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['kontaktForm'] = KontaktForm(prefix='kontakt')
                context['regex'] = True
                return render(request, 'patronaza/registracija.html', context)
            if(not uform.password_match()):
                context['uporabniskiRacunForm'] = uform
                context['pacientForm'] = pform
                context['kontaktForm'] = KontaktForm(prefix='kontakt')
                context['match'] = True
                return render(request, 'patronaza/registracija.html', context)
            u = User.objects.create_user(username=uform.cleaned_data['email'], password=uform.cleaned_data['password'], email=uform.cleaned_data['email'],
                                         is_superuser='f', is_staff='f', is_active='f')
            u.save()

            instance = pform.save(commit=False)
            instance.id_racuna = u
            instance.lastnik_racuna = True
            instance.id_okolis = Okolis.objects.get(pk=1)
            instance.save()

            g = Group.objects.get(name='Pacient')
            g.user_set.add(u)

            hashids = Hashids(salt="salt1234")
            ciphertext = hashids.encode(u.id)
            time = datetime.datetime.now().time()
            date = datetime.datetime.now().date()
            sendString = "http://localhost:8000/patronaza/aktivacija/" + ciphertext + "/" + str(date)+"*"+str(time)
            posli_email(sendString,str(u.email))
            return HttpResponseRedirect(reverse('kontakt',kwargs={'id':instance.id}))
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
        pacijenti.append(SkrbnistvoForm(instance=r))
    context['pacijenti'] = pacijenti
    return render(request, 'patronaza/pregled.html', context)

@login_required
def dodaj_skrbnistvo(request):
    context = {'skrbnistvoForm': SkrbnistvoForm()}
    ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = ime
    if(request.method == 'POST'):
        sform = SkrbnistvoForm(request.POST)
        if sform.is_valid():
            instance = sform.save(commit=False)
            instance.id_racuna = request.user
            instance.lastnik_racuna = False
            instance.id_okolis = Okolis.objects.get(pk=1)
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
        sendString = "http://localhost:8000/patronaza/aktivacija/" + ur_id + "/" + str(date) + "*" + str(time)
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
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
    else:
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = ime
    obiski = VrstaObiska.objects.all()
    dn_list = DelovniNalog.objects.all()
    context['obiski'] = obiski
    if request.method == 'POST':
        izdajatelj = request.POST.get('izdajatelj',False)
        sestra = request.POST.get('sestra', False)
        nadomestnaSestra = request.POST.get('nadomestnaSestra',False)
        pacient = request.POST.get('pacient',False)
        od = request.POST.get('od',False)
        do = request.POST.get('do',False)
        vrsta = request.POST.get('vrsta',False)
        print([izdajatelj,sestra,nadomestnaSestra,pacient,od,do,vrsta])
        '''
        if(request.POST.get('izdajatelj',False)):
            osebje = Osebje.objects.get(šifra=request.POST.get('izdajatelj',False))
            dn_list = dn_list.filter(id_osebje=osebje)
        if(request.POST.get('izdajatelj',False)):
            osebje = Osebje.objects.get(šifra = request.POST.get('sestra', False))
            dn_list = dn_list.filter(id_osebje=osebje)
        if(request.POST.get('nadomestnaSestra',False)):
            osebje = Osebje.objects.get(šifra=request.POST.get('nadomestnaSestra',False))
            dn_list = dn_list.filter(id_osebje=osebje)
            '''
    order = request.GET.get('order', '-id_osebje')

    paginator = Paginator(dn_list, 10)
    page = request.GET.get('page')
    try:
        delovniNalog = paginator.page(page)
    except PageNotAnInteger:
        delovniNalog = paginator.page(1)
    except EmptyPage:
        delovniNalog = paginator.page(paginator.num_pages)
    context['delavniNalogi'] = delovniNalog
    return render(request, 'patronaza/izpisiDelavneNaloge.html', context)
@login_required
def delovni_nalog_podrobnosti(request,id):
    context={}
    ime = ''
    if (Osebje.objects.filter(id_racuna=request.user).exists()):
        ime = Osebje.objects.get(id_racuna=request.user)
    else:
        ime = Pacient.objects.filter(id_racuna=request.user).filter(lastnik_racuna=True)[0]
    context['ime'] = ime
    dn = DelovniNalog.objects.get(pk=id)
    return render(request, 'patronaza/test.html', context)