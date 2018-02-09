# -*- coding: utf-8 -*-
from django.db import connection
from models import Vhosts
from string import digits, ascii_lowercase, ascii_uppercase
from random import choice, sample
from traceback import format_exc
import ldap


def getDataDict(domain):
	''' Generate dict for domain object informations ({'key_pl': value}) '''

	data = {}
	if domain:
		db = None
		try:
			with connection.cursor() as cursor:
				cursor.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s', [domain.name.split('.')[0]])
				db = cursor.fetchone()
		except:
			print 'Wystąpił błąd w trakcie zbierania informacji o bazie danych'
		values = domain.__dict__
		keys = {'Nazwa domeny': 'name', 'Właściciel': 'email', 'Numer kontaktowy': 'number', 'Opis': 'description', 'Komentarz': 'comment', 'Wersja PHP': 'phpv', 'Baza danych': 'db'}
		for k, v in keys.iteritems():
			data[k] = values[v]
		if data['Baza danych']:
			data['Baza danych'] = [data['Baza danych'][i:i + 12] for i in xrange(0, 36, 12)]
		data['HTTPS'] = False
		try:
			path = Vhosts.objects.first().path
			if 'SSLEngine on' in open(path + data['Nazwa domeny'].split('.')[0] + '.conf').read():
				data['HTTPS'] = True
		except:
			print 'Wystąpił błąd w trakcie zbierania informacji o https'
	return data


def ldapf(user):
	''' Get user data from LDAP '''

	ldap_conf = {
		'host': 'ldap.somedomain.pl',
		'port': 999,
		'basedn': 'xxx',
		'password': 'yyy',
		'binddn': 'zzz'
	}
	result = {}
	try:
		l = ldap.open(ldap_conf['host'], ldap_conf['port'])
		l.set_option(ldap.OPT_REFERRALS, 0)
		l.simple_bind_s(ldap_conf['binddn'], ldap_conf['password'])
	except:
		return 'Brak połączenia z serwerem LDAP.'
	ldap_result = l.search_s(ldap_conf['basedn'], ldap.SCOPE_SUBTREE, 'uid=' + user)
	l.unbind()
	if ldap_result:
		ldap_result = ldap_result[0][1]
		result['description'] = '%s %s' % (ldap_result['givenName'][0].decode('utf-8'), ldap_result['sn'][0].decode('utf-8'))
		result['number'] = '' if 'telephoneNumber' not in ldap_result else ldap_result['telephoneNumber'][0]
	if result:
		result['email'] = '%s@somedomain.pl' % user
	return result if result else 'Brak takiego konta w bazie.'


def genPassword():
	''' Password gnerator for new database Users '''
	upper_lower = ''.join(choice(ascii_uppercase + ascii_lowercase) for _ in xrange(6))
	digts = ''.join(choice(digits) for _ in xrange(4))
	special = ''.join(choice('-_%#') for _ in xrange(2))
	pattern = upper_lower + digts + special
	return ''.join(sample(pattern, len(pattern)))


def dropDb(dbName):
	''' Delete MySql database (by name) '''
	error = ''
	try:
		with connection.cursor() as mysql:
			mysql.execute('DROP USER %s_user1' % dbName)
			mysql.execute('DROP USER %s_user2' % dbName)
			mysql.execute('DROP USER %s_user3' % dbName)
			mysql.execute('DROP DATABASE %s' % dbName)
	except:
		error = format_exc()
		error = 'ErrorNo: ' + error.split('\n')[-2].split('(')[1:][0][:-1]
	return False if not error else error