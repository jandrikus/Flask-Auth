"""
This module implements the EmailManager for Flask-Auth.
It uses Jinja2 to render email subject and email message.
It uses the EmailAdapter interface to send emails.
"""

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from flask import render_template, url_for

from . import ConfigError
from .translation_utils import gettext as _ # map _() to gettext()
from .email_helper import send_email

# Auth is implemented across several source code files.
# Mixins are used to aggregate all member functions into the Auth class.
class EmailManager(object):
	""" Send emails """

	def __init__(self, app):
		"""
		Args:
			app(Flask): The Flask application instance.
		"""
		self.auth = app.auth

		# Ensure that AUTH_EMAIL_SENDER_EMAIL is set
		if not self.auth.AUTH_EMAIL_SENDER_EMAIL:
			raise ConfigError('Config setting AUTH_EMAIL_SENDER_EMAIL is missing.')

		# Simplistic email address verification
		if '@' not in self.auth.AUTH_EMAIL_SENDER_EMAIL:
			raise ConfigError('Config setting AUTH_EMAIL_SENDER_EMAIL is not a valid email address.')

	def specific_email(self, user):
		raise NotImplementedError

	def send_password_changed_email(self, user):
		# Send the 'password has changed' notification email.

		# Verify config settings
		if not self.auth.AUTH_SEND_PASSWORD_CHANGED_EMAIL: return

		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Render email from templates and send it
		return self._render_and_send_email(
			email,
			user,
			_('Your password has been changed'),
			'password_changed',
		)

	def send_username_changed_email(self, user):
		# Send the 'username has changed' notification email.

		# Verify config settings
		if not self.auth.AUTH_SEND_USERNAME_CHANGED_EMAIL: return

		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Render email from templates and send it
		return self._render_and_send_email(
			email,
			user,
			_('Your username has been changed'),
			'username_changed',
		)

	def send_email_changed_email(self, user, old_email):
		# Send the 'email has changed' notification email.

		# Verify config settings
		if not self.auth.AUTH_SEND_EMAIL_CHANGED_EMAIL: return

		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Render email from templates and send it to both old and new(or specific) emails
		has_error_new_email = self._render_and_send_email(
			email,
			user,
			_('Your email has been changed'),
			'email_changed',
		)
		has_error_old_email = self._render_and_send_email(
			old_email,
			user,
			_('Your email has been changed'),
			'email_changed',
		)
		return has_error_new_email or has_error_old_email

	def send_reset_password_email(self, user):
		# Send the 'reset password' email.

		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Generate a reset_password_link
		token = self.auth.token_manager.generate_reset_password_token(user)
		reset_password_link = url_for('auth.reset_password', token=token, _external=True)

		# Render email from templates and send it
		return self._render_and_send_email(
			email,
			user,
			_('Reset Password'),
			'reset_password',
			reset_password_link=reset_password_link,
		)

	def send_confirm_account_email(self, user):
		# Send the 'account confirmation' email.
		
		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Generate a confirm_account_link
		token = self.auth.token_manager.generate_confirm_account_token(user)
		confirm_account_link = url_for('auth.confirm_account', token=token, _external=True)

		# Render email from templates and send it
		return self._render_and_send_email(
			email,
			user,
			_('Account Confirmation'),
			'confirm_account',
			confirm_account_link=confirm_account_link,
		)

	def send_wellcome_email(self, user):
		# Send the 'wellcome' notification email.

		# The confirm_email email is sent to a specific email or user.email
		if self.auth.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.specific_email(user)
		else:
			email = user.email

		# Render email from templates and send it
		return self._render_and_send_email(
			email,
			user,
			_('Wellcome to %(app_name)s', app_name=self.auth.AUTH_APP_NAME),
			'welcome',
		)

	def _render_and_send_email(self, email, user, subject, template_filename, **kwargs):
		# Add some variables to the template context
		kwargs['app_name'] = self.auth.AUTH_APP_NAME
		kwargs['email'] = email
		kwargs['user'] = user
		kwargs['auth'] = self.auth

		# Render HTML message
		html_text = render_template(f'auth/email/{template_filename}.html', **kwargs)
		# Render text message
		plain_text = render_template(f'auth/email/{template_filename}.txt', **kwargs)

		# Send email via email_helper
		return send_email(subject=subject, receiver=(user.fullname, email), plain_text=plain_text, html_text=html_text)