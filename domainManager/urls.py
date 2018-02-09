"""domainManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from dmnManager import views
from django_cas import views as cas

urlpatterns = [
    url(r'^$', views.userView, name='Index'),
    url(r'^search/$', views.domainBrowser, name='Browser'),
    url(r'^details/$', views.domainDetails, name='Details'),
    url(r'^php/$', views.switchPHP, name='PHP'),
    url(r'^delete/$', views.deleteDomain, name='Delete'),
    url(r'^edit/$', views.editDomain, name='Edit'),
    url(r'^ldap/$', views.getLdapData, name='Ldap'),
    url(r'^add/$', views.createDomain, name='Create'),
    url(r'^settings/php/$', views.phpSettingsList, name='PHPlist'),
    url(r'^settings/php/add/$', views.phpSettingsList, name='PHPadd'),
    url(r'^settings/php/del/$', views.phpSettingsList, name='PHPdel'),
    url(r'^settings/vhosts/$', views.vhostSettings, name='VhostsList'),
    url(r'^settings/services/$', views.serviceSettingsList, name='ServicesList'),
    url(r'^settings/services/add/$', views.serviceSettingsList, name='ServicesAdd'),
    url(r'^settings/services/del/$', views.serviceSettingsList, name='ServicesDel'),
    # DB
    url(r'^settings/db/add/$', views.addDatabase, name='DBadd'),
    url(r'^settings/db/del/$', views.deleteDatabase, name='BDdel'),
    # HTTPS
    url(r'^settings/https/add/$', views.addHttps, name='HTTPSadd'),
    url(r'^settings/https/del/$', views.deleteHttps, name='HTTPSdel'),
    # CAS
    url(r'^login/$', cas.login, name='login'),
    url(r'^logout/$', cas.logout, name='logout'),
]
