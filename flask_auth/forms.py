# This file defines and validates Flask-User forms. Forms are based on the WTForms module.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from flask import current_app
from flask_login import current_user

from flask_wtf import FlaskForm

from wtforms import BooleanField, HiddenField, PasswordField, SubmitField, StringField, SelectField
from wtforms import validators, ValidationError

from .translation_utils import lazy_gettext as _ # map _() to lazy_gettext()

# ****************
# ** Validators **
# ****************

def password_validator(self, form, field):
	"""
	Ensure that passwords have at least 6 characters with one lowercase letter, one uppercase letter and one number.
	Override this method to customize the password validator.
	"""
	# Convert string to list of characters
	password = list(field.data)
	password_length = len(password)
	# Count lowercase, uppercase and numbers
	lowers = uppers = digits = 0
	for ch in password:
		if ch.islower(): lowers += 1
		if ch.isupper(): uppers += 1
		if ch.isdigit(): digits += 1
	# Password must have one lowercase letter, one uppercase letter and one digit
	is_valid = password_length >= 6 and lowers and uppers and digits
	if not is_valid:
		raise ValidationError(
			_('Password must have at least 6 characters with one lowercase letter, one uppercase letter and one number'))

def username_validator(self, form, field):
	"""
	Ensure that Usernames contains at least 3 alphanumeric characters.
	Override this method to customize the username validator.
	"""
	username = field.data
	if len(username) < 3:
		raise ValidationError(
			_('Username must be at least 3 characters long'))
	valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._'
	chars = list(username)
	for char in chars:
		if char not in valid_chars:
			raise ValidationError(
				_("Username may only contain letters, numbers, '-', '.' and '_'"))

def unique_username_validator(form, field):
	""" Ensure that Username is unique. This validator may NOT be customized."""
	if not current_app.auth.username_is_available(field.data):
		raise ValidationError(_('This Username is already in use. Please try another one.'))

def unique_email_validator(form, field):
	""" Email must be unique. This validator may NOT be customized."""
	if not current_app.auth.email_is_available(field.data):
		raise ValidationError(_('This Email is already in use. Please try another one.'))

def used_username_validator(form, field):
	""" Ensure that Username is used. This validator may NOT be customized."""
	if current_app.auth.username_is_available(field.data):
		raise ValidationError(_('This Username does not exist.'))

def used_email_validator(form, field):
	""" Email must be used. This validator may NOT be customized."""
	if current_app.auth.email_is_available(field.data):
		raise ValidationError(_('This Email does not exist.'))

# ***********
# ** Forms **
# ***********

class ChangeEmailForm(FlaskForm):
	"""Change email address form."""
	old_email = StringField(_('Old Email'), validators=[
		validators.DataRequired(_('Old Email is required')),
		validators.Email(_('Invalid Email'))])
	email = StringField(_('Email'), validators=[
		validators.DataRequired(_('Email is required')),
		validators.Email(_('Invalid Email')),
		unique_email_validator])
	submit = SubmitField(_('Add Email'))

class ChangePasswordForm(FlaskForm):
	"""Change password form."""
	old_password = PasswordField(_('Old Password'), validators=[
		validators.DataRequired(_('Old Password is required')),
		])
	new_password = PasswordField(_('New Password'), validators=[
		validators.DataRequired(_('New Password is required')),
		password_validator,
		])
	retype_password = PasswordField(_('Retype New Password'), validators=[
		validators.EqualTo('new_password', message=_('New Password and Retype Password did not match'))
		])
	submit = SubmitField(_('Change password'))

	def validate(self):
		# Use feature config to remove unused form fields
		if not current_app.auth.AUTH_REQUIRE_RETYPE_PASSWORD:
			delattr(self, 'retype_password')

		# Validate field-validators
		if not super(ChangePasswordForm, self).validate(): return False

		# Verify current_user and current_password
		if not current_user or not auth.password_manager.verify_password(self.old_password.data, current_user.password):
			self.old_password.errors.append(_('Old Password is incorrect'))
			return False

		# All is well
		return True

class ChangeUsernameForm(FlaskForm):
	"""Change username form."""
	new_username = StringField(_('New Username'), validators=[
		validators.DataRequired(_('Username is required')),
		username_validator,
		unique_username_validator,
	])
	password = PasswordField(_('Password'), validators=[
		validators.DataRequired(_('Password is required')),
	])
	submit = SubmitField(_('Change username'))

	def validate(self):
		# Validate field-validators
		if not super(ChangeUsernameForm, self).validate(): return False

		# Verify current_user and current_password
		if not current_user or not auth.password_manager.verify_password(self.password.data, current_user.password):
			self.password.errors.append(_('Password is incorrect'))
			return False

		# All is well
		return True

class LoginForm(FlaskForm):
	"""Login form."""
	next = HiddenField()         # for login.html
	reg_next = HiddenField()     # for login_or_register.html

	username = StringField(_('Username'), validators=[
		validators.DataRequired(_('Username is required')),
	])
	email = StringField(_('Email'), validators=[
		validators.DataRequired(_('Email is required')),
		validators.Email(_('Invalid Email'))
	])
	password = PasswordField(_('Password'), validators=[
		validators.DataRequired(_('Password is required')),
	])
	remember_me = BooleanField(_('Remember me'))

	submit = SubmitField(_('Sign in'))

	def __init__(self, *args, **kwargs):
		super(LoginForm, self).__init__(*args, **kwargs)
		if current_app.auth.AUTH_ENABLE_USERNAME and current_app.auth.AUTH_ENABLE_EMAIL:
			# Renamed 'Username' label to 'Username or Email'
			self.username.label.text = _('Username or Email')

	def validate(self):
		# Remove fields depending on configuration
		auth = current_app.auth
		if auth.AUTH_ENABLE_USERNAME:
			delattr(self, 'email')
		else:
			delattr(self, 'username')

		# Validate field-validators
		if not super(LoginForm, self).validate():
			return False

		# Find user by username and/or email
		user = None
		if auth.AUTH_ENABLE_USERNAME:
			# Find user by username
			user = auth.db_manager.find_user_by_username(self.username.data)

			# Find user by email address (username field)
			if not user and auth.AUTH_ENABLE_EMAIL:
				user = auth.db_manager.find_user_by_email(self.username.data)

		else:
			# Find user by email address (email field)
			user = auth.db_manager.find_user_by_email(self.email.data)

		# Handle successful authentication
		if user and auth.password_manager.verify_password(self.password.data, user.password):
			return True   # Successful authentication

		# Handle unsuccessful authentication
		# Email, Username or Email/Username depending on settings
		if auth.AUTH_ENABLE_USERNAME and auth.AUTH_ENABLE_EMAIL:
			username_or_email_field = self.username
			username_or_email_text = (_('Username/Email'))
			show_does_not_exist = auth.AUTH_SHOW_EMAIL_DOES_NOT_EXIST or auth.AUTH_SHOW_USERNAME_DOES_NOT_EXIST
		elif auth.AUTH_ENABLE_USERNAME:
			username_or_email_field = self.username
			username_or_email_text = (_('Username'))
			show_does_not_exist = auth.AUTH_SHOW_USERNAME_DOES_NOT_EXIST
		else:
			username_or_email_field = self.email
			username_or_email_text = (_('Email'))
			show_does_not_exist = auth.AUTH_SHOW_EMAIL_DOES_NOT_EXIST

		# Show 'username/email does not exist' or 'incorrect password' error message
		if show_does_not_exist:
			if not user:
				message = _('%(username_or_email)s does not exist', username_or_email=username_or_email_text)
				username_or_email_field.errors.append(message)
			else:
				self.password.errors.append(_('Incorrect Password'))

		# Always show 'incorrect username/email or password' error message for additional security
		else:
			message = _('Incorrect %(username_or_email)s and/or Password', username_or_email=username_or_email_text)
			username_or_email_field.errors.append(message)
			self.password.errors.append(message)

		return False  # Unsuccessful authentication

class RegisterForm(FlaskForm):
	"""Register new user form."""
	password_validator_added = False

	username = StringField(_('Username'), validators=[
		validators.DataRequired(_('Username is required')),
		username_validator,
		validators.Length(max=64, message=_('Username must be at most %(max)d characters long')),
		unique_username_validator
	])
	first_name = StringField(_('First name'), validators=[
		validators.InputRequired(),
		validators.Length(max=64, message=_('First name must be at most %(max)d characters long'))
	])
	last_name = StringField(_('Last name(s)'), validators=[
		validators.InputRequired(),
		validators.Length(max=128, message=_('Last name(s) must be at most %(max)d characters long'))
	])
	email = StringField(_('Email'), validators=[
		validators.DataRequired(_('Email is required')),
		validators.Email(_('Invalid Email')),
		validators.Length(max=128, message=_('Email must be at most %(max)d characters long')),
		unique_email_validator
	])
	language = SelectField(_('Language'), choices = current_app.config['AVAILABLE_LANGUAGES_TUPLE'], validators=[
		validators.InputRequired(),
		validators.AnyOf(current_app.config['AVAILABLE_LANGUAGES'], message = _('The language %(language)s is not supported yet'))
	])
	password = PasswordField(_('Password'), validators=[
		validators.DataRequired(_('Password is required')),
		password_validator,
		validators.Length(min=8, message=_('Password must be at least %(min)d characters long')),
		validators.Length(max=128, message=_('Password must be at most %(max)d characters long'))
	])
	retype_password = PasswordField(_('Retype Password'), validators=[
		validators.EqualTo('password', message=_('Both passwords do not match'))
	])
	submit = SubmitField(_('Register'))

	def validate(self):
		# remove certain form fields depending on user manager config
		auth =  current_app.auth
		if not auth.AUTH_ENABLE_USERNAME:
			delattr(self, 'username')
		if not auth.AUTH_ENABLE_EMAIL:
			delattr(self, 'email')
		if not auth.AUTH_REQUIRE_RETYPE_PASSWORD:
			delattr(self, 'retype_password')

		if not super(RegisterForm, self).validate():
			return False
		# All is well
		return True

class ForgotPasswordForm(FlaskForm):
	"""Forgot password form."""
	username = StringField(_('Username'), validators=[
		validators.DataRequired(_('Username is required')),
		used_username_validator
	])
	email = StringField(_('Your email address'), validators=[
		validators.DataRequired(_('Email address is required')),
		validators.Email(_('Invalid Email address')),
		used_email_validator
	])
	submit = SubmitField(_('Send reset password email'))

	def validate(self):
		# remove certain form fields depending on user manager config
		auth =  current_app.auth
		if not auth.AUTH_ENABLE_USERNAME:
			delattr(self, 'username')
		if not auth.AUTH_ENABLE_EMAIL:
			delattr(self, 'email')
		
		if not super(ForgotPasswordForm, self).validate():
			return False
		# All is well
		return True

class ResetPasswordForm(FlaskForm):
	"""Reset password form."""
	new_password = PasswordField(_('New Password'), validators=[
		validators.DataRequired(_('New Password is required')),
		password_validator,
		])
	retype_password = PasswordField(_('Retype New Password'), validators=[
		validators.EqualTo('new_password', message=_('New Password and Retype Password did not match'))])
	next = HiddenField()
	submit = SubmitField(_('Change password'))

	def validate(self):
		# Use feature config to remove unused form fields
		if not current_app.auth.AUTH_REQUIRE_RETYPE_PASSWORD:
			delattr(self, 'retype_password')

		# Validate field-validators
		if not super(ResetPasswordForm, self).validate(): return False
		# All is well
		return True