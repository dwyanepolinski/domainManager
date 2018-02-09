#!/usr/bin/env python2.7

from optparse import OptionParser
from os import remove, rename, system, path
from sys import exit
from subprocess import Popen
from imp import load_source

# Domain manager diectory path
dmp = '/home/john/repo/python/domainManager/'

try:
	settings = load_source('settings', dmp + 'domainManager/settings.py')
except:
	exit('Cannot import domainManager settings module, wrong path?')

# Important locations
www_hdir  = settings.WWW_USERS_PATH
tmp_fpm   = settings.BASE_DIR + '/tmp/fpm/'
tmp_vhost = settings.BASE_DIR + '/tmp/vhost/'
index     = settings.BASE_DIR + '/templates/domain/new/index.php'
certs     = settings.BASE_DIR + '/templates/domain/new/https.template'


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option('-p', dest='php-fpm', help='php-fpm file with full path')
	parser.add_option('-v', dest='vhosts', help='vhosts file with full path')
	parser.add_option('-t', dest='task', help='set task')
	parser.add_option('-s', dest='services', help='services to reset, syntax: sname1,sname2 ...')
	parser.add_option('-u', dest='user', help='username')

	(options, args) = parser.parse_args()
	options = vars(options)

	if options['task']:
		if options['php-fpm'] is None or options['vhosts'] is None:
			exit('Php-fpm and vhosts parameters required.')

	user_name = options['user']
	conf_name = options['php-fpm'].split('/')[-1]

	if options['task'] == 'https':
		conf = open(options['vhosts']).read()
		domain = conf[conf.find('ServerName'):][:conf[conf.find('ServerName'):].find('\n')].split()[1].replace('www.','')
		conf = conf.replace('RedirectMatch 307 ^/(.*) http', 'ServerAlias   %s\n  RedirectMatch 307 ^/(.*) https' % domain)
		ssl_position = conf.find('# SSLTAG')
		vhs_position = conf[:ssl_position].rfind('VirtualHost *:80')
		conf = onf[:vhs_position] + conf[vhs_position:ssl_position].replace('VirtualHost *:80', 'VirtualHost *:443') + conf[ssl_position:]
		new = conf.replace('# SSLTAG', open(certs).read())
		old = open(options['vhosts'], 'w')
		old.write(new)
		old.close()

	if options['task'] == 'http':
		conf = open(options['vhosts']).read()
		conf = conf.replace(conf[conf.find('ServerAlias'):conf.find('RedirectMatch 307 ^/(.*) https') + 30], 'RedirectMatch 307 ^/(.*) http')
		conf = conf.replace('<VirtualHost *:443>', '<VirtualHost *:80>')
		new = conf[:conf.find('# BEGINSSL')] + conf[conf.find('# ENDSSL'):].replace('# ENDSSL', '# SSLTAG')
		old = open(options['vhosts'], 'w')
		old.write(new)
		old.close()

	if options['task'] == 'create':
		rename(tmp_fpm + conf_name, options['php-fpm'])
		rename(tmp_vhost + conf_name, options['vhosts'])
		system('mkdir {0}{1} {0}{1}/WWW'.format(www_hdir, user_name))
		system('cp {0} {1}{2}/WWW/'.format(index, www_hdir, user_name))

	if options['task'] == 'remove':
		remove(options['php-fpm'])
		remove(options['vhosts'])
		system('rm -R {0}{1}'.format(www_hdir, user_name))

	if options['task'] == 'switch':
		rename(options['php-fpm'], options['vhosts'])
	
	if options['services']:
		services = options['services'].split(',')
		if 'httpd' in services:
			services.remove('httpd')
			if not options['task'] == 'switch':
				Popen(['sleep 10 && systemctl restart httpd'], shell=True)
		for service in services:
			system('systemctl stop %s' % service)
		for service in services:
			system('systemctl start %s' % service)
