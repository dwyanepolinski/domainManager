# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Domain(models.Model):
	name = models.CharField(max_length=100)
	email = models.CharField(max_length=50)
	number = models.CharField(max_length=50)
	description = models.CharField(max_length=200)
	comment = models.CharField(max_length=50)
	phpv = models.CharField(max_length=50)
	db = models.CharField(max_length=36)

	def __str__(self):
		return self.name

class Admin(models.Model):
	email = models.CharField(max_length=50)

	def __str__(self):
		return self.email

class Php(models.Model):
	version = models.CharField(max_length=10)
	fpmPath = models.CharField(max_length=500)

	def __str__(self):
		return self.version

class Vhosts(models.Model):
	path = models.CharField(max_length=500)

	def __str__(self):
		return self.path

class Service(models.Model):
	name = models.CharField(max_length=200)

	def __str__(self):
		return self.name
