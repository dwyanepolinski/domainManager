# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.db import connection
from decorators import sessionInit, postOnly, admin
from functions import getDataDict, ldapf, genPassword, dropDb
from models import Domain, Admin, Php, Vhosts, Service
from os import system, path
from traceback import format_exc
from json import loads

# Absolute path to dm_root_tasks.py
abs = settings.BASE_DIR + '/'

# Views here

@sessionInit
def userView(request):
	''' Returns view for user, depending on the user type (admin or regular user) '''

	domain = getDataDict(Domain.objects.filter(email=request.user).first())
	varColl = {'email': request.user, 'domain': domain, 'phps': Php.objects.all()}
	if domain:
		varColl.update({'domainName': domain['Nazwa domeny'], 'db_name': domain['Nazwa domeny'].split('.')[0], 'db': domain['Baza danych']})
	template = 'admin/panel.html' if request.session['is_admin'] else 'user/panel.html'
	return render(request, template, varColl)


@admin
@postOnly
def domainBrowser(request):
	''' Ajax view, returns domain search results '''

	domainToFind = request.POST.get('variable1')
	if domainToFind:
		searchResult = Domain.objects.filter(name__icontains=domainToFind)
	else:
		searchResult = Domain.objects.all()
	varColl = {'searchResult': searchResult.order_by('name')}
	template = 'domain/search.html'
	return render(request, template, varColl)


@admin
@postOnly
def domainDetails(request):
	''' Ajax view, returns details for domain passed in POST variable1 '''

	detailsFor = request.POST.get('variable1')
	data = getDataDict(Domain.objects.filter(name=detailsFor).first())
	editables = ['Opis', 'Numer kontaktowy', 'Komentarz']
	varColl = {'data': data,
			   'name': data['Nazwa domeny'],
			   'phps': Php.objects.all(),
			   'db_name': detailsFor.split('.')[0],
			   'db': data['Baza danych'],
			   'https': data['HTTPS'],
			   'editable': editables} if data else {'data': data}
	template = 'domain/details.html'
	return render(request, template, varColl)


@postOnly
def switchPHP(request):
	''' This function switches PHP version for domain passed in POST variable1 '''

	domainName = request.POST.get('variable1')
	toPhpv = request.POST.get('variable2')
	toPhpv = toPhpv.split()[1] if toPhpv else None
	domain = Domain.objects.filter(name=domainName).first()
	if domain:
		if domain.phpv == toPhpv:
			return HttpResponse('Ta wersja PHP (%s) jest aktualnie ustawiona.' % toPhpv)
		oldPhpv = domain.phpv
		fromPhpFpmPath = Php.objects.filter(version=domain.phpv).first().fpmPath
		toPhpFpmPath = Php.objects.filter(version=toPhpv).first().fpmPath
		services = Service.objects.all()
		servicesList = [service.name for service in services]
		system('sudo %sdm_root_tasks.py -p %s%s.conf -v %s%s.conf -t switch -s %s' % (abs, fromPhpFpmPath, domainName.split('.')[0], toPhpFpmPath, domainName.split('.')[0], ','.join(servicesList)))
		domain.phpv = toPhpv
		domain.save()
		return HttpResponse('Pomyślnie zmieniono dla "%s" PHP (%s -> %s).' % (domainName, oldPhpv, toPhpv))
	return HttpResponse('Wystąpił błąd podczas zmiany wersji PHP.')


@admin
@postOnly
def deleteDomain(request):
	''' This function deletes domain '''

	domainName = request.POST.get('variable1')
	domain = Domain.objects.filter(name=domainName).first()
	if domain:
		if domain.db:
			error = dropDb(domainName.split('.')[0])
			if error:
				return HttpResponse('Błąd w trakcie usuwania domeny, %s' % error)
		phpConf = Php.objects.filter(version=domain.phpv).first().fpmPath
		vhostConf = Vhosts.objects.first().path
		owner = domain.email.split('@')[0]
		domain.delete()
		services = Service.objects.all()
		servicesList = [service.name for service in services]
		system('sudo %sdm_root_tasks.py -p %s%s.conf -v %s%s.conf -t remove -s %s -u %s' % (abs, phpConf, domainName.split('.')[0], vhostConf, domainName.split('.')[0], ','.join(servicesList), owner))
		return HttpResponse('Pomyślnie usunięto domenę "%s".' % domainName)
	return HttpResponse('Błąd podczas usuwania domeny "%s".' % domainName)


@admin
@postOnly
def editDomain(request):
	''' This function edit domain object properties.
		variable1 - domain, variable2 - property, variavle3 - value '''

	domainName = request.POST.get('variable1')
	attrName = request.POST.get('variable2')
	attrValue = request.POST.get('variable3')
	if attrName not in ['number', 'comment', 'description']:
		return HttpResponse('Jedyne pola edytowalne to numer kontaktowy, komentarz i opis!')
	domain = Domain.objects.filter(name=domainName).first()
	if domain:
		attrValue = attrValue.strip()
		if attrValue == getattr(domain, attrName):
			return HttpResponse('Wartość jest aktualnie ustawiona.')
		setattr(domain, attrName, attrValue)
		domain.save()
		keys = {'comment': 'Komentarz', 'description': 'Opis', 'number': 'Numer kontaktowy', 'phpv': 'Wersja PHP', 'email': 'Właściciel', 'name': 'Nazwa domeny'}
		return HttpResponse('Zapisano dla "%s" (%s -> "%s")' % (domainName, keys[attrName], attrValue))
	return HttpResponse('Błąd edycji pola domeny.')


@admin
@postOnly
def getLdapData(request):
	''' This function generates form to create domain, fills form with LDAP data '''

	userName = request.POST.get('variable1')
	if userName:
		userName = userName.split('@')[0] if '@' in userName else userName
	ldapData = ldapf(userName)
	if isinstance(ldapData, basestring):
		template = 'domain/ldap.html'
		varColl = {'msg': ldapData, 'type': 'danger'}
	else:
		phps = Php.objects.all()
		ldapData['name'] = ldapData['comment'] = ''
		ldapData['homedir'] = '/www/%s' % userName
		data = {}
		keys = {'comment': 'Komentarz', 'description': 'Opis', 'number': 'Numer kontaktowy', 'email': 'Właściciel', 'name': 'Nazwa domeny', 'homedir': 'Katalog domeny'}
		for k, v in keys.iteritems():
			data[v] = ldapData[k]
		template = 'domain/add.html'
		varColl = {'data': data, 'phps': phps}
	return render(request, template, varColl)


@admin
@postOnly
def createDomain(request):
	''' This function creates new domain '''

	domain = request.POST.get('variable1')
	if domain:
		domainInfo = {}
		msg = ''
		keys = {'Nazwa domeny': 'name', 'Właściciel': 'email', 'Numer kontaktowy': 'number', 'Opis': 'description', 'Komentarz': 'comment', 'Wersja PHP': 'phpv', 'Katalog domeny': 'homedir'}
		for k, v in loads(domain.encode('utf-8')).iteritems():
			domainInfo[keys[v['key']]] = v['val']
		domainInfo['name'] = domainInfo['name'].lower()
		
		# Error handling
		if len(domainInfo['name'].split())-1:
			msg = 'Nazwa domeny musi być pojedyńczym słowem (somedomain.pl).'
		if '.pl' not in domainInfo['name']:
			msg = 'Zła składnia nazwy domeny (np. somedomain.pl).'
		if Domain.objects.filter(name=domainInfo['name']):
			msg = 'Domena już istnieje.'
		if Domain.objects.filter(email=domainInfo['email']).count():
			msg = 'Konto ma już utworzoną domenę "%s".' % Domain.objects.filter(email=domainInfo['email']).first().name
		
		# If no message = if no erros reported yet
		if not msg:
			newDomain = Domain()
			domainInfo['phpv'] = domainInfo['phpv'].split()[1]
			for key in domainInfo:
				if key != 'homedir':
					setattr(newDomain, key, domainInfo[key].strip())
			name = domainInfo['name'].split('.')[0]
			try:
				# vhosts.c/domena.conf
				vhostConf = render_to_string('domain/new/vhost.template', {'name': name, 'fullname': domainInfo['name'], 'user': domainInfo['email'].split('@')[0]})
				vhostPath = Vhosts.objects.first().path
				vhostFile = open('%s%s.conf' % (abs + 'tmp/vhost/', name), 'w')
				vhostFile.write(vhostConf)
				vhostFile.close()
				# php-fpm.d/domena.conf
				fpmConf = render_to_string('domain/new/fpm.template', {'name': name, 'user': domainInfo['email'].split('@')[0]})
				fpmPath = Php.objects.filter(version=domainInfo['phpv']).first().fpmPath
				fpmFile = open('%s%s.conf' % (abs + 'tmp/fpm/', name), 'w')
				fpmFile.write(fpmConf)
				fpmFile.close()
				# reset services
				services = Service.objects.all()
				servicesList = [service.name for service in services]
				system('sudo %sdm_root_tasks.py -p %s.conf -v %s.conf -s %s -t create -u %s' % (abs, fpmPath + name, vhostPath + name, ','.join(servicesList), domainInfo['email'].split('@')[0]))
				newDomain.save()
				msg = 'Pomyślnie utworzono domenę "%s".' % domainInfo['name']
				msgType = 'success'
			except:
				msg = 'Wystąpił błąd w trakcie utworzenia domeny.'
				print format_exc()
				msgType = 'danger'
		else:
			msgType = 'danger'
	else:
		msgType = 'danger'
	template = 'domain/ldap.html'
	varColl = {'msg': msg, 'type': msgType}
	return render(request, template, varColl)


@admin
@postOnly
def phpSettingsList(request):
	''' This function fills PHP settings page and supports settings panel '''

	phpv = request.POST.get('variable1')
	newPath = request.POST.get('variable2')
	msg = ''
	if newPath:
		newPath = newPath + '/' if newPath[-1] != '/' else newPath
	if not phpv:
		msg = 'Tutaj możesz zarządzać dostępnymi wersjami PHP dla tej strony.'
	else:
		task = request.POST.get('variable3')
		if task == 'createnew':
			# Error handling
			if Php.objects.filter(version=phpv):
				msg = 'Ta wersja PHP (%s) już istnieje.' % phpv
			elif phpv and not path.exists(newPath):
				msg = 'Podana ścieżka nie istnieje, nie zapisano.'
			else:
				php = Php(version=phpv, fpmPath=newPath)
				php.save()
				msg = 'Pomyślnie dodano nową wersję PHP (%s).' % phpv 
		elif task == 'remove':
			Php.objects.filter(version=phpv).delete()
			msg = 'Pomyślnie usunięto wersję PHP (%s).' % phpv
		else:
			php = Php.objects.filter(version=phpv).first()
			if not php:
				msg = 'Tutaj możesz zarządzać dostępnymi wersjami PHP dla tej strony.'
			else:
				if getattr(php, 'fpmPath') == newPath:
					msg = 'Podana wartość jest aktualna.'
				else:
					setattr(php, 'fpmPath', newPath)
					php.save()
					msg = 'Zapisano nową ścieżkę dla PHP %s.' % phpv
	template = 'admin/settings/php.html'
	varColl = {'data': Php.objects.all(), 'msg': msg}
	return render(request, template, varColl)


@admin
@postOnly
def vhostSettings(request):
	''' This function returns vhosts directory path, supports editing '''

	vhostsPath = request.POST.get('variable1')
	xpath = ''
	if vhostsPath:
		vhostsPath = vhostsPath + '/' if vhostsPath[-1] != '/' else vhostsPath
		if not path.exists(vhostsPath):
			msg = 'Podana ścieżka nie istnieje.'
		else:
			vhosts = Vhosts.objects.first()
			if not vhosts:
				vhosts = Vhosts()
			vhosts.path = vhostsPath
			vhosts.save()
			msg = 'Pomyślnie zapisano nową ścieżkę.'
	else:
		msg = 'Tutaj możesz edytowac ścieżkę do katalogu vhosts.d (miejsce konfiguracji wirtualnych domen).'
	if Vhosts.objects.first():
		xpath = Vhosts.objects.first().path
	template = 'admin/settings/vhost.html'
	varColl = {'msg': msg, 'path': xpath}
	return render(request, template, varColl)


@admin
@postOnly
def serviceSettingsList(request):
	''' This function works same as  phpSettingsList, but for services '''

	serviceName = request.POST.get('variable1')
	if not serviceName:
		msg = 'Tutaj możesz zarządzać usługami, które są resetowane po dodaniu domeny (lub aktualizacji PHP).'
	else:
		task = request.POST.get('variable2')
		if task == 'createnew':
			if Service.objects.filter(name=serviceName):
				msg = 'Usługa "%s" już istnieje.' % serviceName
			else:
				service = Service(name=serviceName)
				service.save()
				msg = 'Pomyślnie dodano usługę "%s".' % serviceName
		if task == 'remove':
			Service.objects.filter(name=serviceName).delete()
			msg = 'Pomyślnie usunięto usługę "%s".' % serviceName
	template = 'admin/settings/services.html'
	varColl = {'services': Service.objects.all(), 'msg': msg}
	return render(request, template, varColl)


@admin
@postOnly
def addDatabase(request):
	''' Ajax function to create database, database users and setting priveleges '''

	dbName = request.POST.get('variable1')
	dbFullName = dbName
	if not dbName:
		return HttpResponse('Błędna nazwa bazy.')
	dbName = dbName.split('.')[0]
	passwords = [genPassword() for _ in xrange(3)]
	with connection.cursor() as cursor:
		try:
			cursor.execute('CREATE DATABASE %s' % dbName)
		except:
			return HttpResponse('Wystąpił błąd mysql w trakcie tworzenia bazy. Baza istnieje.')
		for i, user_type in enumerate(['user', 'update', 'admin']):
			set_passwd = True
			while set_passwd:
				try:
					cursor.execute("CREATE USER '%s_%s'@'%%' IDENTIFIED BY '%s'" % (dbName, user_type, passwords[i]))
					set_passwd = False
				except:
					passwords[i] = genPassword()
		try:
			cursor.execute("GRANT SELECT ON %s.* TO '%s_user1'" % (dbName, dbName))	
			cursor.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON %s.* TO '%s_user2'" % (dbName, dbName))	
			cursor.execute("GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,CREATE VIEW,INDEX,ALTER,DROP,LOCK TABLES ON %s.* TO '%s_user3'" % (dbName, dbName))	
		except:
			error = format_exc()
			error = 'ErrorNo: ' + error.split('\n')[-2].split('(')[1:][0][:-1]
			return HttpResponse('Wystąpił błąd mysql w trakcie tworzenia bazy. %s' % error)
	domain = Domain.objects.filter(name=dbFullName).first()
	domain.db = ''.join(passwords)
	domain.save()
	return HttpResponse('Pomyślnie utworzono bazę danych.')


@admin
@postOnly
def deleteDatabase(request):
	''' Ajax function, deletes database '''

	dbName = request.POST.get('variable1')
	dbFullName = dbName
	if not dbName:
		return HttpResponse('Błędna nazwa bazy danych.')
	dbName = dbName.split('.')[0]
	error = dropDb(dbName)
	if error:
		return HttpResponse('Wystąpił błąd mysql w trakcie usuwania bazy. %s' % error)
	domain = Domain.objects.filter(name = dbFullName).first()
	domain.db = ''
	domain.save()
	return HttpResponse('Pomyślnie usunięto bazę danych.')


@admin
@postOnly
def addHttps(request):
	domain = request.POST.get('variable1')
	vhost = Vhosts.objects.first()
	if vhost:
		system('sudo %sdm_root_tasks.py -v %s%s.conf -t https -s %s -p n' % (abs, vhost.path, domain.split('.')[0], 'httpd'))
		msg = 'Pomyślnie ustawiono HTTPS.'
	else:
		msg = 'Brak konfiguracji folderu vhosts.d.'
	return HttpResponse(msg)


@admin
@postOnly
def deleteHttps(request):
	domain = request.POST.get('variable1')
	
	vhost = Vhosts.objects.first()
	if vhost:
		system('sudo %sdm_root_tasks.py -v %s%s.conf -t http -s %s -p n' % (abs, vhost.path, domain.split('.')[0], 'httpd'))
		msg = 'Pomyślnie wyłączono HTTPS.'
	else:
		msg = 'Brak konfiguracji folderu vhosts.d.'
	return HttpResponse(msg)
