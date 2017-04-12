# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User

class Aktivnosti(models.Model):
    sifra = models.CharField(max_length=32)
    aktivnost = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'aktivnosti'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'

    def __str__(self):
        return self.name


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(blank=True, null=True, max_length=30)
    last_name = models.CharField(blank=True, null=True, max_length=30)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=datetime.now())

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BarvaEpruvete(models.Model):
    barva = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'barva_epruvete'


class CrnaLista(models.Model):
    ip = models.TextField()  # This field type is a guess.
    poiskusi = models.IntegerField()
    datum_zaklepanja = models.DateField()
    id_ur = models.ForeignKey('AuthUser', models.DO_NOTHING, db_column='id_ur')

    class Meta:
        managed = False
        db_table = 'crna_lista'


class DelovniNalog(models.Model):
    id_osebje = models.ForeignKey('Osebje', models.DO_NOTHING, db_column='id_osebje')
    id_vrsta = models.ForeignKey('VrstaObiska', models.DO_NOTHING, db_column='id_vrsta')
    datum_prvega_obiska = models.DateField()
    st_obiskov = models.IntegerField()
    cas_med_dvema = models.IntegerField()
    casovno_obdobje = models.DateField()
    status_dn = models.ForeignKey('StatusDn', models.DO_NOTHING, db_column='status_dn')
    vrsta_storitve = models.ForeignKey('VrstaStoritve', models.DO_NOTHING, db_column='vrsta_storitve', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delovni_nalog'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DodeljenoOsebje(models.Model):
    id_osebja = models.ForeignKey('Osebje', models.DO_NOTHING, db_column='id_osebja')
    id_obisk = models.ForeignKey('Obisk', models.DO_NOTHING, db_column='id_obisk')
    je_zadolzena = models.IntegerField()
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'dodeljeno_osebje'


class Injekcije(models.Model):
    id_obisk = models.ForeignKey('Obisk', models.DO_NOTHING, db_column='id_obisk')
    id_zdravilo = models.ForeignKey('Zdravila', models.DO_NOTHING, db_column='id_zdravilo')
    st_injekcij = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'injekcije'


class IzvajalecZd(models.Model):
    šifra = models.CharField(unique=True, max_length=5)
    naziv = models.CharField(max_length=64)
    naslov = models.CharField(max_length=64)
    posta = models.ForeignKey('Posta', models.DO_NOTHING, db_column='posta', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'izvajalec_zd'

    def __str__(self):
        return self.šifra


class KontaktnaOseba(models.Model):
    ime = models.CharField(max_length=64)
    priimek = models.CharField(max_length=64)
    naslov = models.CharField(max_length=128)
    posta = models.ForeignKey('Posta', models.DO_NOTHING, db_column='posta')
    telefon = models.CharField(max_length=64)
    razmerje = models.ForeignKey('SorodstvenaVez', models.DO_NOTHING, related_name='razmerje',
                                         db_column='razmerje')
    pacient = models.ForeignKey('Pacient', models.DO_NOTHING, db_column='pacient')
    class Meta:
        managed = False
        db_table = 'kontaktna_oseba'


class Ljudje(models.Model):
    ime = models.CharField(max_length=30)
    priimek = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'ljudje'


class Material(models.Model):
    sifra = models.CharField(max_length=20, blank=True, null=True)
    naziv = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'material'


class MaterialDn(models.Model):
    id_dn = models.ForeignKey(DelovniNalog, models.DO_NOTHING, db_column='id_dn')
    id_material = models.ForeignKey(Material, models.DO_NOTHING, db_column='id_material', blank=True, null=True)
    kolicina = models.IntegerField()
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'material_dn'


class NamenObiska(models.Model):
    naziv = models.CharField(max_length=64, blank=True, null=True)
    id_vrsta = models.ForeignKey('VrstaObiska', models.DO_NOTHING, db_column='id_vrsta')

    class Meta:
        managed = False
        db_table = 'namen_obiska'


class Obisk(models.Model):
    id_dn = models.ForeignKey(DelovniNalog, models.DO_NOTHING, db_column='id_dn')
    zaporedna_st_obiska = models.IntegerField()
    status_obiska = models.ForeignKey('StatusObiska', models.DO_NOTHING, db_column='status_obiska')
    datum_obiska = models.DateField(blank=True, null=True)
    predviden_datum = models.DateField(blank=True, null=True)
    podrobnosti_obiska = models.TextField(blank=True, null=True)
    izbran_datum = models.DateField(blank=True, null=True)
    cena = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obisk'


class OdvzemKrvi(models.Model):
    id_obisk = models.ForeignKey(Obisk, models.DO_NOTHING, db_column='id_obisk', blank=True, null=True)
    barva = models.ForeignKey(BarvaEpruvete, models.DO_NOTHING, db_column='barva')
    st_epruvet = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'odvzem_krvi'


class Okolis(models.Model):
    šifra = models.CharField(max_length=32)
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'okolis'

    def __str__(self):
        return self.šifra


class Osebje(models.Model):
    id_racuna = models.OneToOneField(User, models.DO_NOTHING, db_column='id_racuna')
    šifra = models.CharField(unique=True, max_length=5)
    ime = models.CharField(max_length=64)
    priimek = models.CharField(max_length=64)
    telefon = models.CharField(max_length=32)
    id_zd = models.ForeignKey(IzvajalecZd, models.DO_NOTHING, db_column='id_zd')
    izbrisan = models.IntegerField()
    okolis = models.ForeignKey(Okolis, models.DO_NOTHING, db_column='okolis', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osebje'

    def __str__(self):
        return self.ime + ' ' + self.priimek


class Oskrba(models.Model):
    id_dn = models.ForeignKey(DelovniNalog, models.DO_NOTHING, db_column='id_dn')
    id_pacient = models.ForeignKey('Pacient', models.DO_NOTHING, db_column='id_pacient')

    class Meta:
        managed = False
        db_table = 'oskrba'


class OstaliPodatki(models.Model):
    id_vrsta_podatka = models.ForeignKey('VrstaPodatka', models.DO_NOTHING, db_column='id_vrsta_podatka')
    id_aktivnosti = models.ForeignKey(Aktivnosti, models.DO_NOTHING, db_column='id_aktivnosti')
    id_obisk = models.ForeignKey(Obisk, models.DO_NOTHING, db_column='id_obisk')
    obvezen = models.IntegerField()
    vrednost = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'ostali_podatki'



class Pacient(models.Model):
    id_racuna = models.ForeignKey(User, models.DO_NOTHING, db_column='id_racuna')
    st_kartice = models.CharField(max_length=32)
    ime = models.CharField(max_length=64)
    priimek = models.CharField(max_length=64)
    telefon = models.CharField(max_length=64)
    datum_rojstva = models.DateField()
    naslov = models.CharField(max_length=128)
    id_posta = models.ForeignKey('Posta', models.DO_NOTHING, db_column='id_posta')
    id_okolis = models.ForeignKey(Okolis, models.DO_NOTHING, db_column='id_okolis')
    lastnik_racuna = models.BooleanField(default=False)
    spol = models.CharField(max_length=6)
    razmerje_ur = models.ForeignKey('SorodstvenaVez', models.DO_NOTHING, related_name='razmerje_ur',
                                 db_column='razmerje_ur')

    class Meta:
        managed = False
        db_table = 'pacient'

    def __str__(self):
        return self.ime + ' ' + self.priimek


class Posta(models.Model):
    st_poste = models.IntegerField(primary_key=True)
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'posta'

    def __str__(self):
        return str(self.st_poste)


class SorodstvenaVez(models.Model):
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'sorodstvena_vez'

    def __str__(self):
        return self.naziv


class StatusDn(models.Model):
    naziv = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'status_dn'


class StatusObiska(models.Model):
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'status_obiska'


class StatusUr(models.Model):
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'status_ur'


class TipObiska(models.Model):
    tip = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tip_obiska'

class VrstaObiska(models.Model):
    naziv = models.CharField(max_length=32, blank=True, null=True)
    tip = models.ForeignKey(TipObiska, models.DO_NOTHING, db_column='tip', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vrsta_obiska'

    def __str__(self):
        return self.naziv


class VrstaPodatka(models.Model):
    naziv = models.CharField(max_length=64)
    podatkovni_tip = models.CharField(max_length=20)
    enote = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'vrsta_podatka'


class VrstaStoritve(models.Model):
    sifra = models.CharField(max_length=10)
    naziv = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'vrsta_storitve'

    def __str__(self):
        return self.naziv


class Zdravila(models.Model):
    naziv = models.CharField(max_length=64)
    cena = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'zdravila'
