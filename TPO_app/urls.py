# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^logout/$', login_required(views.logout), name='logout'),
    url(r'^$', views.login, name='login'),
    url(r'^changePassword/$', login_required(views.change_password), name='change_password'),
    url(r'^domov$', views.index, name='index'),
    url(r'^registracija/$', views.registracija, name='registracija'),
    url(r'^kontakt/(?P<id>.+)$', views.kontakt, name='kontakt'),
    url(r'^aktivacija/(?P<ur_id>.+)/(?P<date>.+)$', views.aktivacija, name='aktivacija'),
    url(r'^pregled_skrbnistev/$', views.pregled_skrbnistev, name='pregled_skrbnistev'),
    url(r'^dodaj_skrbnistvo/$', views.dodaj_skrbnistvo, name='dodaj_skrbnistvo'),
    url(r'^delovniNalogi/$', views.izpisi_delavne_naloge, name='izpisi_delavne_naloge'),
    url(r'^delovenNalog/(?P<id>[0-9]+)$', views.delovni_nalog_podrobnosti, name='delovni_nalog_podrobnosti'),
    url(r'^delovniNalog/$', views.delovniNalog, name='delovniNalog'),
    url(r'^osebjeAdd/', views.osebjeAdd, name='osebjeAdd'),
]