from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from models import Admin


def postOnly(f):
	''' Allow only POST request '''

	def wrapper(request):
		if request.method != 'POST':
			return HttpResponseForbidden()
		return f(request)
	return wrapper


def admin(f):
	''' Allow only admin users '''

	def wrapper(request):
		if not request.session['is_admin']:
			return HttpResponseForbidden()
		return f(request)
	return wrapper


def sessionInit(f):
	''' Initialize session (force login, check if is an admin) '''
	
	def wrapper(request):
		request.session['is_admin'] = bool(Admin.objects.filter(email=request.user))
		if not request.user.is_authenticated:
			return redirect('login')
		return f(request)
	return wrapper