# This module implements Auth view methods.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from datetime import datetime
from urllib.parse import quote, unquote

from flask import current_app, flash, redirect, render_template, request, url_for, abort
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
			# Update user's password with new password
			new_password = form.new_password.data
			self.password_manager.set_password(new_password, current_user)
			self.db_manager.save_user(current_user)
			self.db_manager.commit()
			# Send password_changed email
			self.email_manager.send_password_changed_email(current_user)
			# Send changed_password signal
			signals.auth_changed_password.send(current_app._get_current_object(), user=current_user)
			# Flash a system message
			flash(_('Your password has been changed successfully.'), 'success')
			# Redirect to 'next' URL
			safe_next_url = self._get_safe_next_url('next')
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
			signals.auth_changed_username.send(current_app._get_current_object(), user=current_user)
			# Flash a system message
			flash(_("Your username has been changed to '%(username)s'.", username=new_username), 'success')
			# Redirect to 'next' URL
			safe_next_url = self._get_safe_next_url('next')
			return redirect(safe_next_url)
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/change_username.html', form=form)

	@login_required
	def change_email(self):
		form = self.ChangeEmailFormClass()
		# Process valid POST request
		if request.method == 'POST' and form.validate():
			# Change current user's email
			old_email = current_user.email
			current_user.email = form.email.data
			self.db_manager.save_user(current_user)
			self.db_manager.commit()
			# Send email_changed email (for old and new)
			self.email_manager.send_email_changed_email(current_user, old_email)
			# Send changed_email signal
			signals.auth_changed_email.send(current_app._get_current_object(), user=current_user)
			# Flash a system message
			flash(_("Your email has been changed from %(old_email)s to '%(new_email)s'.", old_email=old_email, new_email=current_user.email), 'success')
			# Redirect to 'next' URL
			safe_next_url = self._get_safe_next_url('next')
			return redirect(safe_next_url)
		# Process GET or invalid POST request
		self.prepare_domain_translations()
		return render_template('auth/change_email.html', form=form)

	def forgot_password(self):
		# Prompt for username and/or email (depending settings) and send reset password email.
		if current_user.is_authenticated:
			logout_user()
		# Initialize form
		form = self.ForgotPasswordFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Get User by username and/or by email
			if self.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME:
				user_by_username = self.db_manager.find_user_by_username(form.username.data)
			if self.AUTH_ENABLE_FORGOT_PASSWORD_BY_EMAIL:
				user_by_email = self.db_manager.find_user_by_email(form.email.data)
			# Ensure both match the same user
			if self.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME and self.AUTH_ENABLE_FORGOT_PASSWORD_BY_EMAIL:
				user = user_by_username if user_by_username == user_by_email else None
			elif self.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME:
				user = user_by_username
			elif self.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME:
				user = user_by_email
			if user:
				# Send reset_password email
				self.email_manager.send_reset_password_email(user)
				# Send forgot_password signal
				signals.auth_forgot_password.send(current_app._get_current_object(), user=user)
				# The confirm_email email is sent to a specific email or user.email
				if self.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
					email = self.db_manager.specific_email(user)
				else:
					email = user.email
				# Flash a system message
				flash(_("A reset password email has been sent to '%(email)s'. Open that email and follow the instructions to reset your password.", email=email), 'success')
			else:
				# Flash a system message
				flash(_("The given information does not match"), 'error')
			# Redirect to the login page
			return redirect(self._endpoint_url('auth.login'))
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/forgot_password.html', form=form)

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
			# Update user's password with new password
			new_password = form.new_password.data
			self.password_manager.set_password(new_password, user)
			self.db_manager.save_user(user)
			self.db_manager.commit()
			# Send 'password_changed' email
			self.email_manager.send_password_changed_email(user)
			# Send reset_password signal
			signals.auth_reset_password.send(current_app._get_current_object(), user=user)
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
		return render_template('auth/reset_password.html', form=form, token = token)

	def login(self):
		# Prepare and process the login form.
		# Authenticate username/email and login authenticated users.
		safe_next_url = self._get_safe_next_url('next', self.AUTH_ENDPOINT_AFTER_LOGIN)
		# Immediately redirect already logged in users
		if current_user.is_authenticated and self.AUTH_AUTO_LOGIN_AT_LOGIN:
			return redirect(safe_next_url)
		# Initialize form
		form = self.LoginFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			# Retrieve User
			user = None
			print('hehee2')
			if self.AUTH_ENABLE_LOGIN_BY_USERNAME:
				# Find user record by username
				user = self.db_manager.find_user_by_username(form.username.data)
				# Find user record by email (with form.username)
				if not user and self.AUTH_ENABLE_LOGIN_BY_EMAIL:
					user = self.db_manager.find_user_by_email(form.username.data)
			else:
				# Find user by email (with form.email)
				user = self.db_manager.find_user_by_email(form.email.data)
			print('hehee')
			if user:
				# Check if user has a confirmed account (if required)
				if self.AUTH_ENABLE_CONFIRM_ACCOUNT and not self.AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT and not user.verified:
					url = url_for('auth.resend_account_verification')
					flash(_('Your account has not yet been confirmed. Check your email Inbox and Spam folders for the confirmation email or <a href="%(url)s">Re-send confirmation email</a>.', url=url), 'error')
					return redirect(url_for('auth.account_verification'))
				# Log user in
				print('here')
				return self._do_login_user(user, safe_next_url, form.remember_me.data)
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/login.html', form=form, safe_next_url=safe_next_url)

	def logout(self):
		# Process the logout link.
		# Sign the user out.
		# Send auth_logged_out signal
		signals.auth_logged_out.send(current_app._get_current_object(), user=current_user)
		# Use Flask-Login to sign out user
		logout_user()
		# Flash a system message
		flash(_('You have signed out successfully.'), 'success')
		# Redirect to logout_next endpoint or '/'
		safe_next_url = self._get_safe_next_url('next')
		return redirect(safe_next_url)

	def register(self):
		# Display registration form and create new User.
		if current_user.is_authenticated:
			return redirect(self._endpoint_url())
		# Initialize form
		form = self.RegisterFormClass(request.form)
		# Process valid POST
		if request.method == 'POST' and form.validate():
			user = self.db_manager.add_user()
			form.populate_obj(user)
			# Set user's password
			self.password_manager.set_password(user.password, user)
			# Create new user
			self.db_manager.save_user(user)
			self.db_manager.commit()
			# (if required) Send 'confirm_account' email and delete new User object if send fails
			if self.AUTH_ENABLE_CONFIRM_ACCOUNT:
				# Send 'confirm email' email
				has_error = self.email_manager.send_confirm_account_email(user)
				if has_error:
					# delete new User object if send fails
					self.db_manager.delete_object(user)
					self.db_manager.commit()
					return has_error # an html template with an error message
				# The confirm_email email is sent to a specific email or user.email
				if self.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
					email = self.db_manager.specific_email(user)
				else:
					email = user.email
				# Flash a system message
				flash(_('A confirmation email has been sent to %(email)s with instructions to complete your registration.', email=email), 'success')
				return self._do_login_user(user, url_for('auth.account_verification'))
			# Send 'welcome' email and delete new User object if send fails
			else:
				# Send wellcome email
				if self.AUTH_SEND_WELLCOME_EMAIL:
					has_error = self.email_manager.send_wellcome_email(current_user)
					if has_error:
						# delete new User object if send fails
						self.db_manager.delete_object(user)
						self.db_manager.commit()
						return has_error # an html template with an error message
					# Send welcome signal
					signals.auth_welcome.send(current_app._get_current_object(), user=user)
				# Flash a system message
				flash(_('You have registered successfully.'), 'success')
			# Auto-login after register or redirect to login page
			safe_next_url = self._get_safe_next_url('next')
			if self.AUTH_AUTO_LOGIN_AFTER_REGISTER:
				return self._do_login_user(user, safe_next_url) # auto-login
			else:
				return redirect(url_for('auth.login', next=quote(safe_next_url))) # redirect to login page
		# Render form
		self.prepare_domain_translations()
		return render_template('auth/register.html', form=form)

	@allow_unconfirmed_account
	def account_verification(self):
		if current_user.verified:
			return redirect(self._endpoint_url())
		# The confirm_email email is sent to a specific email or current_user.email
		if self.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.db_manager.specific_email(current_user)
		else:
			email = current_user.email
		self.prepare_domain_translations()
		return render_template('auth/account_verification.html', email=email)

	@allow_unconfirmed_account
	def resend_account_verification(self):
		# Re-send account verification email.
		if current_user.verified:
			return redirect(self._endpoint_url())
		# Send confirm_account email
		has_error = self.email_manager.send_confirm_account_email(current_user)
		if has_error:
			return has_error # an html template with an error message
		# The confirm_email email is sent to a specific email or current_user.email
		if self.AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL:
			email = self.db_manager.specific_email(current_user)
		else:
			email = current_user.email
		# Flash a system message
		flash(_('A confirmation email has been sent again to %(email)s with instructions to complete your registration.', email=email), 'success')
		# Render
		self.prepare_domain_translations()
		return render_template('auth/account_verification.html', email=email, resent=True)

	def confirm_account(self, token):
		# Verify account confirmation token and activate the user account.
		# Verify token
		user = self.token_manager.verify_confirm_account_token(token)
		if not user:
			flash(_('Invalid confirmation token.'), 'error')
			return redirect(url_for('auth.login'))
		if user.verified:
			return redirect(self._endpoint_url())
		user.verified = True
		user.verified_date = datetime.utcnow()
		# Save object
		self.db_manager.save_object(user)
		self.db_manager.commit()
		# Send wellcome email
		if self.AUTH_SEND_WELLCOME_EMAIL:
			self.email_manager.send_wellcome_email(current_user)
		# Send welcome signal
		signals.auth_welcome.send(current_app._get_current_object(), user=user)
		# Flash a system message
		flash(_('Welcome to %(app_name)s', app_name=self.AUTH_APP_NAME), 'success')
		# Auto-login after confirm or redirect to login page
		safe_next_url = self._get_safe_next_url('next')
		if self.AUTH_AUTO_LOGIN_AFTER_CONFIRM:
			return self._do_login_user(user, safe_next_url) # auto-login
		else:
			return redirect(url_for('auth.login', next=quote(safe_next_url))) # redirect to login page

	def unauthenticated(self):
		# Prepare Flash message
		flash(_("You must be signed in to access '%(url)s'.", url=request.url), 'error')
		# Redirect to 401 error page
		return abort(401)

	def unauthorized(self):
		# Prepare Flash message
		url = request.script_root + request.path
		flash(_("You do not have permission to access '%(url)s'.", url=url), 'error')
		# Redirect to 403 error page
		return abort(403)

	def _do_login_user(self, user, safe_next_url='', remember_me=False):
		# User must have been authenticated
		if not user: return self.unauthenticated()
		# Check if user account has been disabled
		if user.disabled:
			flash(_('Your account has been disabled.'), 'error')
			return redirect(url_for('user.login'))
		# Use Flask-Login to sign in user
		login_user(user, remember=remember_me)
		# Update last_seen_date
		user.last_seen_date = datetime.utcnow()
		self.db_manager.save_object(user)
		self.db_manager.commit()
		# Send user_logged_in signal
		signals.auth_logged_in.send(current_app._get_current_object(), user=user)
		# Flash a system message
		flash(_('You have signed in successfully.'), 'success')
		# Redirect to 'next' URL
		return redirect(safe_next_url or url_for(self.AUTH_ENDPOINT_AFTER_LOGIN))

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