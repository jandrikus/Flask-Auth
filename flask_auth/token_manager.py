"""
This module implements the TokenManager for Flask-Auth.
It uses jwt to generate and verify tokens.
"""

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

import base64
import string
import jwt
from time import time
from json import decoder

from . import ConfigError

class TokenManager(object):
	"""Generate and verify timestamped, signed and encrypted tokens. """
	def __init__(self, app):
		"""
		Check config settings
		Args:
			app(Flask): The Flask application instance.
		"""
		self.app = app
		self.auth = app.auth

		# Use the applications's SECRET_KEY if flask_secret_key is not specified.
		flask_secret_key = app.config.get('SECRET_KEY', None)
		if not flask_secret_key:
			raise ConfigError('Config setting SECRET_KEY is missing.')
		# Print a warning if SECRET_KEY is too short
		key = flask_secret_key.encode()
		if len(key)<32:
			print('WARNING: Flask-User TokenManager: SECRET_KEY is shorter than 32 bytes.')

	def generate_reset_password_token(self, user):
		return jwt.encode(
			{'reset_password': user.id, 'exp': time() + self.auth.AUTH_RESET_PASSWORD_EXPIRATION},
			self.app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

	def verify_reset_password_token(self, token):
		try:
			id = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
		except:
			return
		return self.auth.db_manager.get_user_by_id(id)

	def generate_confirm_account_token(self, user):
		return jwt.encode({'verify_account': user.id, 'exp': time() + self.auth.AUTH_CONFIRM_ACCOUNT_EXPIRATION}, self.app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

	def verify_confirm_account_token(self, token):
		try:
			id = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])['verify_account']
		except:
			return
		return self.auth.db_manager.get_user_by_id(id)