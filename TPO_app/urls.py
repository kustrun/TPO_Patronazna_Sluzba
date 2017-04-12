from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
	url(r'^logout/$', login_required(views.logout), name='logout'),
	url(r'^login/$', views.login, name='login'),
	url(r'^changePassword/$', login_required(views.change_password), name='change_password'),
]