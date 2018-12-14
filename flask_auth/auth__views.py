# This module implements Auth view methods.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from datetime import datetime
from urllib.parse import quote, unquote

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from .decorators import login_required, allow_unconfirmed_account
from . import signals
from .translation_utils import gettext as _  # map _() to gettext()


# This class mixes into the Auth class.
# Mixins allow for maintaining code and docs across several files.
class Auth__Views(object):
	"""Flask-User views."""
	@login_required
	def change_password(self):
		# Prompt for old password and new password and change the user's password.
		# Initialize form
		form = self.ChangePasswordFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Update user's password with new hashed password
			new_password = form.new_password.data
			self.password_manager.set_password(new_password, current_user)
			self.db_manager.save_user(current_user)
			self.db_manager.commit()
			# Send password_changed email
			if self.AUTH_ENABLE_EMAIL and self.AUTH_SEND_PASSWORD_CHANGED_EMAIL:
				self.email_manager.send_password_changed_email(current_user)
			# Send changed_password signal
			signals.user_changed_password.send(current_app._get_current_object(), user=current_user)
			# Flash a system message
			flash(_('Your password has been changed successfully.'), 'success')
			# Redirect to 'next' URL
			safe_next_url = self._get_safe_next_url('next', 'auth.login')
			return redirect(safe_next_url)
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/change_password.html', form=form)
	
	@login_required
	def change_username(self):
		# Prompt for new username and password and change the user's username.
		# Initialize form
		form = self.ChangeUsernameFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Change username
			new_username = form.new_username.data
			current_user.username=new_username
			self.db_manager.save_object(current_user)
			self.db_manager.commit()
			# Send username_changed email
			self.email_manager.send_username_changed_email(current_user)
			# Send changed_username signal
			signals.user_changed_username.send(current_app._get_current_object(), user=current_user)
			# Flash a system message
			flash(_("Your username has been changed to '%(username)s'.", username=new_username), 'success')
			# Redirect to 'next' URL
			safe_next_url = self._get_safe_next_url('next', 'auth.login')
			return redirect(safe_next_url)
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/change_username.html', form=form)

	def confirm_account(self, token):
		# Verify account confirmation token and activate the user account.
		# Verify token
		user = self.token_manager.verify_confirm_account_token(token)
		if not user:
			flash(_('Invalid confirmation token.'), 'error')
			return redirect(url_for('auth.login'))
		user.verified = True
		# Save object
		self.db_manager.save_object(user)
		self.db_manager.commit()
		# Send wellcome email
		if self.AUTH_ENABLE_EMAIL and self.AUTH_SEND_WELLCOME_EMAIL:
			self.email_manager.send_wellcome_email(current_user)
		# Send welcome signal
		signals.auth_welcome.send(current_app._get_current_object(), user=user)
		# Flash a system message
		flash(_('Welcome to %(app_name)s', app_name=self.AUTH_APP_NAME), 'success')
		# Auto-login after confirm or redirect to login page
		safe_next_url = self._get_safe_next_url('next', 'auth.login')
		if self.AUTH_AUTO_LOGIN_AFTER_CONFIRM:
			return self._do_login_user(user, safe_next_url)  # auto-login
		else:
			return redirect(url_for('auth.login') + '?next=' + quote(safe_next_url))  # redirect to login page

	def forgot_password(self):
		# Prompt for email and send reset password email.
		# Initialize form
		form = self.ForgotPasswordFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Get User by username and by email
			username = form.username.data
			email = form.email.data
			user_by_username = self.db_manager.find_user_by_username(username)
			user_by_email = self.db_manager.find_user_by_email(email)
			# Ensure both match the same user
			if user_by_username == user_by_email:
				# Send reset_password email
				self.email_manager.send_reset_password_email(user_by_username)
				# Send forgot_password signal
				signals.auth_forgot_password.send(current_app._get_current_object(), user=user_by_username)
				# Flash a system message
				flash(_("A reset password email has been sent to '%(email)s'. Open that email and follow the instructions to reset your password.", email=email), 'success')
				# Redirect to the login page
				return redirect(self._endpoint_url('auth.forgot_password'))
			else:
				# Flash a system message
				flash(_("The given information does not match"), 'error')
				# Redirect to the login page
				return redirect(self._endpoint_url('auth.login'))
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/forgot_password.html', form=form)

	@login_required
	def change_email(self):
		form = self.ChangeEmailFormClass()
		# Process valid POST request
		if request.method == 'POST' and form.validate():
			# Change user's email
			old_email = form.old_email.data
			new_email = form.email.data
			user = self.db_manager.find_user_by_email(old_email)
			if not user or user != current_user:
				# The current user is not the same who changes the email for
				 return redirect(url_for('auth.login'))
			user.email = new_email
			self.db_manager.save_user(current_user)
			self.db_manager.commit()
			return redirect(url_for('auth.change_email'))
		# Process GET or invalid POST request
		self.prepare_domain_translations()
		return render_template('auth/change_email.html', form=form)

	def login(self):
		# Prepare and process the login form.
		# Authenticate username/email and login authenticated users.
		safe_next_url = self._get_safe_next_url('next')
		# Immediately redirect already logged in users
		if current_user.is_authenticated and self.AUTH_AUTO_LOGIN_AT_LOGIN:
			return redirect(safe_next_url)
		# Initialize form
		form = self.LoginFormClass(request.form)  # for login.html
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Retrieve User
			user = None
			if self.AUTH_ENABLE_USERNAME:
				# Find user record by username
				user = self.db_manager.find_user_by_username(form.username.data)
				# Find user record by email (with form.username)
				if not user and self.AUTH_ENABLE_EMAIL:
					user = self.db_manager.find_user_by_email(form.username.data)
			else:
				# Find user by email (with form.email)
				user = self.db_manager.find_user_by_email(form.email.data)
			if user:
				# Log user in
				return self._do_login_user(user, safe_next_url, form.remember_me.data)
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/login.html', form=form)

	def logout(self):
		# Process the logout link.
		# Sign the user out.
		# Send user_logged_out signal
		signals.user_logged_out.send(current_app._get_current_object(), user=current_user)
		# Use Flask-Login to sign out user
		logout_user()
		# Flash a system message
		flash(_('You have signed out successfully.'), 'success')
		# Redirect to logout_next endpoint or '/'
		safe_next_url = self._get_safe_next_url('next')
		return redirect(safe_next_url)

	def register(self):
		# Display registration form and create new User.
		# Initialize form
		form = self.RegisterFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			user = self.db_manager.add_user()
			form.populate_obj(user)
			# Update user's password with hashed password
			self.password_manager.set_password(user.password, user)
			# Create new user
			self.db_manager.save_user(user)
			self.db_manager.commit()
			# Send 'confirm_account' email and delete new User object if send fails
			if self.AUTH_SEND_CONFIRM_ACCOUNT_EMAIL:
				try:
					# Send 'confirm email' or 'registered' email
					self._send_confirm_account_email(user, self.AUTH_ENABLE_CONFIRM_ACCOUNT)
				except Exception as e:
					# delete new User object if send  fails
					self.db_manager.delete_object(user)
					self.db_manager.commit()
					raise
			# Send 'welcome' email and delete new User object if send fails
			else:
				# Send wellcome email
				if self.AUTH_ENABLE_EMAIL and self.AUTH_SEND_WELLCOME_EMAIL:
					self.email_manager.send_wellcome_email(current_user)
				# Send welcome signal
				signals.user_welcome.send(current_app._get_current_object(), user=user)
			# Redirect if AUTH_ENABLE_CONFIRM_ACCOUNT is set
			if self.AUTH_ENABLE_CONFIRM_ACCOUNT:
				return redirect(url_for('auth.account_verification'))
			# Auto-login after register or redirect to login page
			if self.AUTH_AUTO_LOGIN_AFTER_REGISTER:
				return self._do_login_user(user, '/') # auto-login
			else:
				return redirect(url_for('auth.login')) # redirect to login page
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/register.html', form=form)

	@allow_unconfirmed_account
	def account_verification(self):
		self.prepare_domain_translations()
		return render_template('auth/account_verification.html')

	@allow_unconfirmed_account
	def resend_account_verification(self):
		# Re-send account verification email.
		# Send confirm_account email
		self._send_confirm_account_email(current_user, self.AUTH_ENABLE_CONFIRM_ACCOUNT)
		# Redirect
		self.prepare_domain_translations()
		return render_template('auth/account_verification.html', resent=True)

	def reset_password(self, token):
		# Verify the password reset token, Prompt for new password, and set the user's password.
		if current_user.is_authenticated:
			logout_user()
		# Verify token
		user = self.token_manager.verify_reset_password_token(token)
		if not user:
			flash(_('Your reset password token is invalid.'), 'error')
			return redirect(self._endpoint_url('auth.login'))
		# Initialize form
		form = self.ResetPasswordFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Update user's password with new hashed password
			new_password = form.new_password.data
			self.password_manager.set_password(new_password, user)
			self.db_manager.save_user(user)
			self.db_manager.commit()
			# Send 'password_changed' email
			if self.AUTH_ENABLE_EMAIL and self.AUTH_SEND_PASSWORD_CHANGED_EMAIL:
				self.email_manager.send_password_changed_email(user)
			# Send reset_password signal
			signals.user_reset_password.send(current_app._get_current_object(), user=user)
			# Flash a system message
			flash(_("Your password has been reset successfully."), 'success')
			# Auto-login after reset password or redirect to login page
			safe_next_url = self._get_safe_next_url('next')
			if self.AUTH_AUTO_LOGIN_AFTER_RESET_PASSWORD:
				return self._do_login_user(user, safe_next_url)  # auto-login
			else:
				return redirect(url_for('auth.login', next=quote(safe_next_url)))  # redirect to login page
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/reset_password.html', form=form)

	def unauthenticated(self):
		# Prepare a Flash message and redirect to AUTH_UNAUTHENTICATED_ENDPOINT
		# Prepare Flash message
		flash(_("You must be signed in to access '%(url)s'.", url=request.url), 'error')
		# Redirect to AUTH_UNAUTHENTICATED_ENDPOINT
		safe_next_url = self.make_safe_url(url=request.url)
		return redirect(self._endpoint_url('auth.unauthenticated', next=quote(safe_next_url)))

	def unauthorized(self):
		# Prepare a Flash message and redirect to AUTH_UNAUTHORIZED_ENDPOINT
		# Prepare Flash message
		url = request.script_root + request.path
		flash(_("You do not have permission to access '%(url)s'.", url=url), 'error')
		# Redirect to AUTH_UNAUTHORIZED_ENDPOINT
		return redirect(self._endpoint_url('auth.unauthorized'))

	def _send_confirm_account_email(self, user, request_email_confirmation, specific_email=''):
		if self.AUTH_ENABLE_EMAIL and self.AUTH_SEND_REGISTERED_EMAIL:
			# Send 'registered' email, with or without a confirmation request
			self.email_manager.send_confirm_account_email(user, specific_email=specific_email)
			# Flash a system message
			if request_email_confirmation:
				email = specific_email if specific_email else user.email
				flash(_('A confirmation email has been sent to %(email)s with instructions to complete your registration.', email=email), 'success')
			else:
				flash(_('You have registered successfully.'), 'success')

	def _do_login_user(self, user, safe_next_url, remember_me=False):
		# User must have been authenticated
		if not user: return self.unauthenticated()
		# Check if user account has been disabled
		if not user.active:
			flash(_('Your account has not been enabled.'), 'error')
			return redirect(url_for('user.login'))
		# Check if user has a confirmed account
		if self.AUTH_ENABLE_EMAIL and self.AUTH_ENABLE_CONFIRM_ACCOUNT and not self.AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT and not user.verified:
			url = url_for('auth.resend_account_confirmation')
			flash(_('Your email address has not yet been confirmed. Check your email Inbox and Spam folders for the confirmation email or <a href="%(url)s">Re-send confirmation email</a>.', url=url), 'error')
			return redirect(url_for('auth.login'))
		# Use Flask-Login to sign in user
		login_user(user, remember=remember_me)
		# Send user_logged_in signal
		signals.user_logged_in.send(current_app._get_current_object(), user=user)
		# Flash a system message
		flash(_('You have signed in successfully.'), 'success')
		# Redirect to 'next' URL
		return redirect(safe_next_url)

	# Returns safe URL from query param ``param_name`` if query param exists.
	# Returns url_for(default_endpoint) otherwise.
	def _get_safe_next_url(self, param_name, default_endpoint=''):
		# Returns safe URL from query param ``param_name`` if query param exists.
		if param_name in request.args:
			safe_next_url = current_app.auth.make_safe_url(unquote(request.args[param_name]))
		# Returns url_for(default_endpoint) otherwise.
		else:
			safe_next_url = self._endpoint_url(default_endpoint)
		return safe_next_url

	def _endpoint_url(self, endpoint=''):
		return url_for(endpoint) if endpoint else '/'