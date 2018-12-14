# This module implements Auth utility methods.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from urllib.parse import urlsplit, urlunsplit

from flask_login import current_user

# This class mixes into the Auth class.
# Mixins allow for maintaining code and docs across several files.
class Auth__Utils(object):
	"""Flask-Auth utility methods."""

	def username_is_available(self, new_username):
		"""
		Check if ``new_username`` is still available.

		| Returns True if ``new_username`` does not exist.
		| Return False otherwise.
		"""
		return self.db_manager.find_user_by_username(new_username) == None

	def email_is_available(self, new_email):
		"""
		Check if ``new_email`` is available.

		| Returns True if ``new_email`` does not exist.
		| Returns False otherwise.
		"""
		return self.db_manager.find_user_by_email(new_email) == None

	def generate_token(self, *args):
		"""Convenience method that calls self.token_manager.generate_token(\*args)."""
		return self.token_manager.generate_token(*args)

	def verify_token(self, token, expiration_in_seconds=None):
		"""Convenience method that calls self.token_manager.verify_token(token, expiration_in_seconds)."""
		return self.token_manager.verify_token(token, expiration_in_seconds)

	def make_safe_url(self, url):
		"""Makes a URL safe by removing optional hostname and port.

		Example:

			| ``make_safe_url('https://hostname:80/path1/path2?q1=v1&q2=v2#fragment')``
			| returns ``'/path1/path2?q1=v1&q2=v2#fragment'``

		Override this method if you need to allow a list of safe hostnames.
		"""

		# Split the URL into scheme, netloc, path, query and fragment
		parts = list(urlsplit(url))

		# Clear scheme and netloc and rebuild URL
		parts[0] = ''   # Empty scheme
		parts[1] = ''   # Empty netloc (hostname:port)
		safe_url = urlunsplit(parts)
		return safe_url

	def prepare_domain_translations(self):
		"""Set domain_translations for current request context."""
		from .translation_utils import domain_translations
		if domain_translations:
			domain_translations.as_default()
