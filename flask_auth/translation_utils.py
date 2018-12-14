"""
This module implements utility functions to offer translations.
It uses Flask-BabelEx to manage domain specific translation files.
"""

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

import os
from flask import request
from flask_login import current_user

_translations_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'translations')

# Load Flask-User translations, if Flask-BabelEx has been installed
try:
	from flask_babelex import Domain
	# Retrieve Flask-User translations from the flask_user/translations directory
	domain_translations = Domain(_translations_dir, domain='flask_auth')
except ImportError:
	domain_translations = None

def gettext(string, **variables):
	return domain_translations.gettext(string, **variables) if domain_translations else string % variables

def lazy_gettext(string, **variables):
	return domain_translations.lazy_gettext(string, **variables) if domain_translations else string % variables

def get_language_codes():
	language_codes = []
	for folder in os.listdir(_translations_dir):
		locale_dir = os.path.join(_translations_dir, folder, 'LC_MESSAGES')
		if not os.path.isdir(locale_dir):
			continue
		language_codes.append(folder)
	return language_codes

def init_translations(babel):
	if babel:
		babel._default_domain = domain_translations
		# Install a language selector if one has not yet been installed
		if babel.locale_selector_func is None:
			# Define a language selector
			def get_locale():
				# if a user is logged in, use the locale from the user settings
				if current_user.is_authenticated:
					return current_user.language
				# otherwise try to guess the language from the user accept
				# header the browser transmits.
				# Retrieve a list of available language codes
				available_language_codes = get_language_codes()
				language_code = request.accept_languages.best_match(available_language_codes)
				return language_code
			# Install the language selector
			babel.locale_selector_func = get_locale