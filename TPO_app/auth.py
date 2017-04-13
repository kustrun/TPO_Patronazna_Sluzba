from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import CrnaLista

class EmailBackend(object):
	def authenticate(self, username=None, password=None, **kwargs):
		UserModel = get_user_model()
		try:
			user = UserModel.objects.get(email=username)
		except UserModel.DoesNotExist:
			return None
		else:
			if getattr(user, 'is_active', False) and  user.check_password(password):
				return user
		return None
	
	def get_user(self, user_id):
		UserModel = get_user_model()
		try:
			return UserModel.objects.get(pk=user_id)
		except UserModel.DoesNotExist:
			return None
		
class BlackListBackend(object):	
	def add_ip_to_user(self, ip, user):
		try:
			ip_user = CrnaLista.objects.get(ip=ip, id_ur=user)
		except CrnaLista.DoesNotExist:
			ip_user = CrnaLista.objects.create(ip=ip, poiskusi=0, datum_zaklepanja=datetime(1970, 1, 1, 0, 0, 0, 0), id_ur=user)
			ip_user.save()
		except:
			return None
			
	def add_get_ip_user(self, ip):
		try:
			ip_user = CrnaLista.objects.get(ip=ip, id_ur=None)
		except CrnaLista.DoesNotExist:
			ip_user = CrnaLista.objects.create(ip=ip, poiskusi=0, datum_zaklepanja=datetime(1970, 1, 1, 0, 0, 0, 0))
			ip_user.save()
			return ip_user
		else:
			return ip_user
	
	def get_ip_lockup_time_remaining(self, ip_user):
		return ((ip_user.datum_zaklepanja + timedelta(hours=settings.LOGIN_LOCKUP_TIME)) - datetime.now()).total_seconds()
	
	def get_ip_lockup_time(self, ip_user):
		return (datetime.now() - ip_user.datum_zaklepanja).total_seconds()
	
	def failed_login(self, ip):
		ip_user = self.add_get_ip_user(ip=ip)
		
		if (self.get_ip_lockup_time(ip_user)/3600) >= settings.LOGIN_LOCKUP_TIME:
			ip_user.poiskusi = 0
		
		ip_user.poiskusi += 1
		ip_user.datum_zaklepanja = datetime.now()
		ip_user.save()
		
	def login_allowed(self, ip):
		ip_user = self.add_get_ip_user(ip=ip)
		return (self.get_ip_lockup_time(ip_user)/3600) >= settings.LOGIN_LOCKUP_TIME or ip_user.poiskusi <= settings.MAX_LOGIN_ATTEMPTS
	
	def reset_all(self):
		for ip_user in CrnaLista.objects.all():
			ip_user.poiskusi = 0
			ip_user.save()
			
	def lockup_to_string(self, ip):
		ip_user = self.add_get_ip_user(ip=ip)
		lockup_time = self.get_ip_lockup_time_remaining(ip_user)
		time_string = ""
		
		hours= int(lockup_time/3600)
		lockup_time -= hours*3600
		minutes = int(lockup_time/60)
		lockup_time -= minutes*60
		seconds = int(lockup_time)

		if hours > 0:
			time_string += str(hours)
			time_string += " ur "
		if minutes > 0:
			time_string += str(minutes)
			time_string += " minut "

		time_string += str(seconds)
		time_string += " sekund"

		return time_string