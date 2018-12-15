# This file defines and validates Flask-User forms. Forms are based on the WTForms module.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from flask import current_app
from flask_login import current_user

from flask_wtf import FlaskForm

from wtforms import BooleanField, HiddenField, PasswordField, SubmitField, StringField, SelectField
from wtforms import validators, ValidationError

from .translation_utils import lazy_gettext as _l # map _l() to lazy_gettext()

# ****************
# ** Validators **
# ****************

def password_validator(form, field):
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
	is_valid = password_length >= 8 and lowers and uppers and digits
	if not is_valid:
		raise ValidationError(
			_l('Password must have at least 8 characters with one lowercase letter, one uppercase letter and one number'))

def username_validator(form, field):
	"""
	Ensure that Usernames contains at least 3 alphanumeric characters.
	Override this method to customize the username validator.
	"""
	username = field.data
	if len(username) < 3:
		raise ValidationError(
			_l('Username must be at least 3 characters long'))
	valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._'
	chars = list(username)
	for char in chars:
		if char not in valid_chars:
			raise ValidationError(
				_l("Username may only contain letters, numbers, '-', '.' and '_'"))

def unique_username_validator(form, field):
	""" Ensure that Username is unique. This validator may NOT be customized."""
	if not current_app.auth.username_is_available(field.data):
		raise ValidationError(_l('This Username is already in use. Please try another one.'))

def unique_email_validator(form, field):
	""" Email must be unique. This validator may NOT be customized."""
	if not current_app.auth.email_is_available(field.data):
		raise ValidationError(_l('This Email is already in use. Please try another one.'))

def used_username_validator(form, field):
	""" Ensure that Username is used. This validator may NOT be customized."""
	if current_app.auth.username_is_available(field.data):
		raise ValidationError(_l('This Username does not exist.'))

def used_email_validator(form, field):
	""" Email must be used. This validator may NOT be customized."""
	if current_app.auth.email_is_available(field.data):
		raise ValidationError(_l('This Email does not exist.'))

# ***********
# ** Forms **
# ***********

class ChangeEmailForm(FlaskForm):
	"""Change email address form."""
	email = StringField(_l('Email'), validators=[
		validators.DataRequired(_l('Email is required')),
		validators.Email(_l('Invalid Email')),
		unique_email_validator])
	submit = SubmitField(_l('Change Email'))

class ChangePasswordForm(FlaskForm):
	"""Change password form."""
	old_password = PasswordField(_l('Old Password'), validators=[
		validators.DataRequired(_l('Old Password is required')),
		])
	new_password = PasswordField(_l('New Password'), validators=[
		validators.DataRequired(_l('New Password is required')),
		password_validator,
		])
	retype_password = PasswordField(_l('Retype New Password'), validators=[
		validators.EqualTo('new_password', message=_l('New Password and Retype Password did not match'))
		])
	submit = SubmitField(_l('Change password'))

	def validate(self):
		# Use feature config to remove unused form fields
		if not current_app.auth.AUTH_REQUIRE_RETYPE_PASSWORD:
			delattr(self, 'retype_password')

		# Validate field-validators
		if not super(ChangePasswordForm, self).validate(): return False

		# Verify current_user and current_password
		if not current_user or not current_app.auth.password_manager.verify_password(self.old_password.data, current_user.password):
			self.old_password.errors.append(_l('Old Password is incorrect'))
			return False

		# All is well
		return True

class ChangeUsernameForm(FlaskForm):
	"""Change username form."""
	new_username = StringField(_l('New Username'), validators=[
		validators.DataRequired(_l('Username is required')),
		username_validator,
		unique_username_validator,
	])
	password = PasswordField(_l('Password'), validators=[
		validators.DataRequired(_l('Password is required')),
	])
	submit = SubmitField(_l('Change username'))

	def validate(self):
		# Validate field-validators
		if not super(ChangeUsernameForm, self).validate(): return False

		# Verify current_user and current_password
		if not current_user or not current_app.auth.password_manager.verify_password(self.password.data, current_user.password):
			self.password.errors.append(_l('Password is incorrect'))
			return False

		# All is well
		return True

class LoginForm(FlaskForm):
	"""Login form."""
	next = HiddenField()         # for login.html
	reg_next = HiddenField()     # for login_or_register.html

	username = StringField(_l('Username'), validators=[
		validators.DataRequired(_l('Username is required')),
	])
	email = StringField(_l('Email'), validators=[
		validators.DataRequired(_l('Email is required')),
		validators.Email(_l('Invalid Email'))
	])
	password = PasswordField(_l('Password'), validators=[
		validators.DataRequired(_l('Password is required')),
	])
	remember_me = BooleanField(_l('Remember me'))

	submit = SubmitField(_l('Sign in'))

	def __init__(self, *args, **kwargs):
		super(LoginForm, self).__init__(*args, **kwargs)
		if current_app.auth.AUTH_ENABLE_LOGIN_BY_USERNAME and current_app.auth.AUTH_ENABLE_LOGIN_BY_EMAIL:
			# Renamed 'Username' label to 'Username or Email'
			self.username.label.text = _l('Username or Email')

	def validate(self):
		# Remove fields depending on configuration
		auth = current_app.auth
		if not auth.AUTH_ENABLE_LOGIN_BY_USERNAME:
			delattr(self, 'username')
		if not auth.AUTH_ENABLE_LOGIN_BY_EMAIL:
			delattr(self, 'email')

		# Validate field-validators
		if not super(LoginForm, self).validate():
			return False

		# Find user by username and/or email
		user = None
		if auth.AUTH_ENABLE_LOGIN_BY_USERNAME:
			# Find user by username
			user = auth.db_manager.find_user_by_username(self.username.data)
			# Find user by email address (username field)
			if not user and auth.AUTH_ENABLE_LOGIN_BY_EMAIL:
				user = auth.db_manager.find_user_by_email(self.username.data)

		else:
			# Find user by email address (email field)
			user = auth.db_manager.find_user_by_email(self.email.data)

		# Handle successful authentication
		if user and auth.password_manager.verify_password(self.password.data, user.password):
			return True   # Successful authentication

		# Handle unsuccessful authentication
		# Email, Username or Email/Username depending on settings
		if auth.AUTH_ENABLE_LOGIN_BY_USERNAME and auth.AUTH_ENABLE_LOGIN_BY_EMAIL:
			username_or_email_field = self.username
			username_or_email_text = (_l('Username/Email'))
			show_does_not_exist = auth.AUTH_SHOW_EMAIL_DOES_NOT_EXIST or auth.AUTH_SHOW_USERNAME_DOES_NOT_EXIST
		elif auth.AUTH_ENABLE_LOGIN_BY_USERNAME:
			username_or_email_field = self.username
			username_or_email_text = (_l('Username'))
			show_does_not_exist = auth.AUTH_SHOW_USERNAME_DOES_NOT_EXIST
		else:
			username_or_email_field = self.email
			username_or_email_text = (_l('Email'))
			show_does_not_exist = auth.AUTH_SHOW_EMAIL_DOES_NOT_EXIST

		# Show 'username/email does not exist' or 'incorrect password' error message
		if show_does_not_exist:
			if not user:
				message = _l('%(username_or_email)s does not exist', username_or_email=username_or_email_text)
				username_or_email_field.errors.append(message)
			else:
				self.password.errors.append(_l('Incorrect Password'))

		# Always show 'incorrect username/email or password' error message for additional security
		else:
			message = _l('Incorrect %(username_or_email)s and/or Password', username_or_email=username_or_email_text)
			username_or_email_field.errors.append(message)
			self.password.errors.append(message)

		return False  # Unsuccessful authentication

class RegisterForm(FlaskForm):
	"""Register new user form."""
	username = StringField(_l('Username'), validators=[
		validators.DataRequired(_l('Username is required')),
		username_validator,
		validators.Length(max=63),
		unique_username_validator
	])
	first_name = StringField(_l('First name'), validators=[
		validators.InputRequired(),
		validators.Length(max=63)
	])
	last_name = StringField(_l('Last name(s)'), validators=[
		validators.InputRequired(),
		validators.Length(max=127)
	])
	email = StringField(_l('Email'), validators=[
		validators.DataRequired(_l('Email is required')),
		validators.Email(_l('Invalid Email')),
		validators.Length(max=255),
		unique_email_validator
	])
	language = SelectField(_l('Language'), choices = current_app.config['AVAILABLE_LANGUAGES_TUPLE'], validators=[
		validators.InputRequired(),
		validators.AnyOf(current_app.config['AVAILABLE_LANGUAGES'], message = _l('The language %(language)s is not supported yet'))
	])
	password = PasswordField(_l('Password'), validators=[
		validators.DataRequired(_l('Password is required')),
		password_validator,
		validators.Length(max=255)
	])
	retype_password = PasswordField(_l('Retype Password'), validators=[
		validators.EqualTo('password', message=_l('Both passwords do not match'))
	])
	submit = SubmitField(_l('Register'))

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
	username = StringField(_l('Username'), validators=[
		validators.DataRequired(_l('Username is required')),
		used_username_validator
	])
	email = StringField(_l('Your email address'), validators=[
		validators.DataRequired(_l('Email address is required')),
		validators.Email(_l('Invalid Email address')),
		used_email_validator
	])
	submit = SubmitField(_l('Send reset password email'))

	def validate(self):
		# remove certain form fields depending on user manager config
		auth =  current_app.auth
		if not auth.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME:
			delattr(self, 'username')
		if not auth.AUTH_ENABLE_FORGOT_PASSWORD_BY_EMAIL:
			delattr(self, 'email')
		
		if not super(ForgotPasswordForm, self).validate():
			return False
		# All is well
		return True

class ResetPasswordForm(FlaskForm):
	"""Reset password form."""
	new_password = PasswordField(_l('New Password'), validators=[
		validators.DataRequired(_l('New Password is required')),
		password_validator,
		])
	retype_password = PasswordField(_l('Retype New Password'), validators=[
		validators.EqualTo('new_password', message=_l('New Password and Retype Password did not match'))])
	next = HiddenField()
	submit = SubmitField(_l('Change password'))

	def validate(self):
		# Use feature config to remove unused form fields
		if not current_app.auth.AUTH_REQUIRE_RETYPE_PASSWORD:
			delattr(self, 'retype_password')

		# Validate field-validators
		if not super(ResetPasswordForm, self).validate(): return False
		# All is well
		return True