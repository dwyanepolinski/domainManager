# domainManager
Django webapp, used to create subdomains with diffrent PHP versions and Mysql databases

- Authentication via CAS server
- Subdomains are created for users in system (user is taken from ldap server)
- All root tasks (service restarting, saving new vhost.conf files etc..) performs dm_root_tasks.py script
- Normail user has ability to change PHP version on his www directory and add database
- Admin can add new domain, manage existing domains, manage php versions and services

# Usgae
To run this app you have to fill some important informations in settings.py file such as cas server address. Finally just make migrations and run server by manage.py script. If you configured app to save conf files in some root directory you have to add dm_root_tasks.py to sudo conf file e.g.

user_running_app	    ALL = NOPASSWD: /path/to/dm_root_tasks/script/dm_root_tasks.py

# Requirements
- python2.7
- Django==1.11.1
- django-cas-client==1.3.0
- python-ldap==2.4.41
