# This module implements the main Auth class for Flask-Auth.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

import datetime

from flask import abort, Blueprint, current_app, Flask, session
from flask_login import LoginManager
from wtforms import ValidationError

from . import ConfigError
from .db_manager import DBManager
from .email_manager import EmailManager
from .password_manager import PasswordManager
from .token_manager import TokenManager
from .translation_utils import lazy_gettext as _l # map _l() to lazy_gettext()
from .auth__settings import Auth__Settings
from .auth__utils import Auth__Utils
from .auth__views import Auth__Views

# The Auth is implemented across several source code files.
# Mixins are used to aggregate all member functions into the one Auth class for ease of customization.
class Auth(Auth__Settings, Auth__Utils, Auth__Views):
	"""
	Customizable User Authentication and Management.
	"""

	def __init__(self, app, db, UserClass, **kwargs):
		"""
		Args:
			app(Flask): The Flask application instance.
			db: An Object-Database Mapper instance such as SQLAlchemy or MongoEngine.
			UserClass: The User class (*not* an instance!).

		Example:
			``auth = Auth(app, db, User)``

		.. This hack shows a header above the _next_ section
		.. code-block:: none

			Customizable Auth methods
		"""
		self.app = app
		if app:
			self.init_app(app, db, UserClass, **kwargs)

	def init_app(
		self, app, db, UserClass,
		AnonymousUser=None,
		RoleClass=None, # Only used for testing
		):

		# See http://flask.pocoo.org/docs/0.12/extensiondev/#the-extension-code
		# Perform Class type checking
		if not isinstance(app, Flask):
			raise TypeError("flask_user.Auth.init_app(): Parameter 'app' is an instance of class '%s' "
							"instead of a subclass of class 'flask.Flask'."
							% app.__class__.__name__)

		# Bind Flask-User to app
		app.auth = self

		# Remember database
		# ------------------------
		self.db = db

		# Load app config settings
		# ------------------------
		# For each 'Auth.AUTH_...' property: load settings from the app config.
		for attrib_name in dir(self):
			if attrib_name[0:5] == 'AUTH_':
				default_value = getattr(Auth, attrib_name)
				setattr(self, attrib_name, app.config.get(attrib_name, default_value))

		# If AUTH_EMAIL_SENDER_NAME is not set, default it to AUTH_APP_NAME
		if not self.AUTH_EMAIL_SENDER_NAME:
			self.AUTH_EMAIL_SENDER_NAME = self.AUTH_APP_NAME

		# Configure Flask session behavior
		# --------------------------------
		if self.AUTH_USER_SESSION_EXPIRATION:
			app.permanent_session_lifetime = datetime.timedelta(seconds=self.AUTH_USER_SESSION_EXPIRATION)
			@app.before_request
			def advance_session_timeout():
				session.permanent = True    # Timeout after app.permanent_session_lifetime period
				session.modified = True     # Advance session timeout each time a user visits a page

		# Configure Flask-Login
		# --------------------
		# Setup default LoginManager using Flask-Login
		self.login_manager = LoginManager(app)
		self.login_manager.login_view = 'auth.login'
		self.custom_anon = False
		if AnonymousUser:
			self.custom_anon = True
			self.login_manager.anonymous_user = AnonymousUser
		# Flask-Login calls this function to retrieve a User record by token.
		@self.login_manager.user_loader
		def load_user(id):
			if self.custom_anon and not int(id):
				return AnonymousUser()
			return self.db_manager.get_user_by_id(int(id))

		# Configure Flask-BabelEx
		# -----------------------
		self.babel = app.extensions.get('babel', None)
		from .translation_utils import init_translations
		init_translations(self.babel)

		# Configure Jinja2
		# ----------------
		# If the application has not initialized BabelEx,
		# we must provide a NULL translation to Jinja2
		if not hasattr(app.jinja_env, 'install_gettext_callables'):
			app.jinja_env.add_extension('jinja2.ext.i18n')
			app.jinja_env.install_null_translations()

		# Define a context processor to provide custom variable and functions available to Jinja2 templates
		def flask_user_context_processor():
			return dict(
				auth=current_app.auth,
			)

		# Register context processor with Jinja2
		app.context_processor(flask_user_context_processor)

		# Create a dummy Blueprint to add the app/templates/auth dir to the template search path
		self.blueprint = Blueprint('auth', __name__, static_folder='static', template_folder='templates')
		# Configure URLs to route to their corresponding view method in blueprint.
		self._add_url_routes()
		app.register_blueprint(self.blueprint, url_prefix='/auth')

		# Set default form classes
		# ------------------------
		with app.app_context():
			from . import forms
			self.ChangeEmailFormClass = forms.ChangeEmailForm
			self.ChangePasswordFormClass = forms.ChangePasswordForm
			self.ChangeUsernameFormClass = forms.ChangeUsernameForm
			self.ForgotPasswordFormClass = forms.ForgotPasswordForm
			self.LoginFormClass = forms.LoginForm
			self.RegisterFormClass = forms.RegisterForm
			self.ResetPasswordFormClass = forms.ResetPasswordForm

		# Set default managers
		# --------------------
		# Setup DBManager
		self.db_manager = DBManager(app, db, UserClass, RoleClass)

		# Setup PasswordManager
		self.password_manager = PasswordManager(app)

		# Setup EmailManager
		self.email_manager = EmailManager(app)

		# Setup TokenManager
		self.token_manager = TokenManager(app)

		# Allow developers to customize Auth
		self.customize(app)

		# Make sure the settings are valid -- raise ConfigError if not
		self._check_settings(app)

	def customize(self, app):
		""" Override this method to customize properties.

		Example::

			# Customize Flask-User
			class CustomAuth(Auth):

				def customize(self, app):

					# Add custom managers and email mailers here
					self.email_manager = CustomEmailManager(app)
					self.password_manager = CustomPasswordManager(app)
					self.token_manager = CustomTokenManager(app)

			# Setup Flask-User
			auth = CustomAuth(app, db, User)
		"""

	# ***** Private methods *****

	def _check_settings(self, app):
		"""Verify required settings. Produce a helpful error messages for incorrect settings."""

		# Check for invalid settings
		# --------------------------

		# Check that AUTH_EMAIL_SENDER_EMAIL is set True
		if not self.AUTH_EMAIL_SENDER_EMAIL:
			raise ConfigError(
				'AUTH_EMAIL_SENDER_EMAIL is missing.'\
				' specify AUTH_EMAIL_SENDER_EMAIL (and AUTH_EMAIL_SENDER_NAME).')

		# Disable settings that rely on a feature setting that's not enabled
		# ------------------------------------------------------------------

		# AUTH_ENABLE_REGISTER=True must have AUTH_ENABLE_USERNAME=True or AUTH_ENABLE_EMAIL=True.
		if not self.AUTH_ENABLE_USERNAME and not self.AUTH_ENABLE_EMAIL:
			self.AUTH_ENABLE_REGISTER = False

		if not self.AUTH_ENABLE_REGISTER:
			self.AUTH_AUTO_LOGIN_AFTER_REGISTER = False

		# Settings that depend on AUTH_ENABLE_EMAIL=True
		if not self.AUTH_ENABLE_EMAIL:
			self.AUTH_ENABLE_LOGIN_BY_EMAIL = False
			self.AUTH_ENABLE_CHANGE_EMAIL = False
			self.AUTH_SHOW_EMAIL_DOES_NOT_EXIST = False

		# Settings that depend on AUTH_ENABLE_USERNAME=True
		if not self.AUTH_ENABLE_USERNAME:
			self.AUTH_ENABLE_LOGIN_BY_USERNAME = False
			self.AUTH_ENABLE_CHANGE_USERNAME = False
			self.AUTH_SHOW_USERNAME_DOES_NOT_EXIST = False

		if not self.AUTH_ENABLE_CHANGE_USERNAME:
			self.AUTH_SEND_USERNAME_CHANGED_EMAIL = False

		if not self.AUTH_ENABLE_CHANGE_EMAIL:
			self.AUTH_SEND_EMAIL_CHANGED_EMAIL = False

		if not self.AUTH_ENABLE_CHANGE_PASSWORD:
			self.AUTH_SEND_PASSWORD_CHANGED_EMAIL = False

		if not self.AUTH_ENABLE_CONFIRM_ACCOUNT:
			self.AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT = False
			self.AUTH_AUTO_LOGIN_AFTER_CONFIRM = False
			
		if not self.AUTH_ENABLE_FORGOT_PASSWORD:
			self.AUTH_ENABLE_FORGOT_PASSWORD_BY_USERNAME = False
			self.AUTH_ENABLE_FORGOT_PASSWORD_BY_EMAIL = False
			self.AUTH_AUTO_LOGIN_AFTER_RESET_PASSWORD = False

	def _add_url_routes(self):
		"""
		Configure a list of URLs to route to their corresponding view method.."""
		# Because methods contain an extra ``self`` parameter, URL routes are mapped
		# to stub functions, which simply call the corresponding method.

		# For testing purposes, we map all available URLs to stubs, but the stubs
		# contain config checks to return 404 when a feature is disabled.

		# Define the stubs
		# ----------------
		def change_password_stub():
			if not self.AUTH_ENABLE_CHANGE_PASSWORD: abort(404)
			return self.change_password()
		def change_username_stub():
			if not self.AUTH_ENABLE_CHANGE_USERNAME: abort(404)
			return self.change_username()
		def change_email_stub():
			if not self.AUTH_ENABLE_CHANGE_EMAIL: abort(404)
			return self.change_email()
		def forgot_password_stub():
			if not self.AUTH_ENABLE_FORGOT_PASSWORD: abort(404)
			return self.forgot_password()
		def reset_password_stub(token):
			if not self.AUTH_ENABLE_FORGOT_PASSWORD: abort(404)
			return self.reset_password(token)
		def login_stub():
			return self.login()
		def logout_stub():
			return self.logout()
		def register_stub():
			if not self.AUTH_ENABLE_REGISTER: abort(404)
			return self.register()
		def account_verification_stub():
			if not self.AUTH_ENABLE_CONFIRM_ACCOUNT: abort(404)
			return self.account_verification()
		def resend_account_verification_stub():
			if not self.AUTH_ENABLE_CONFIRM_ACCOUNT: abort(404)
			return self.resend_account_verification()
		def confirm_account_stub(token):
			if not self.AUTH_ENABLE_CONFIRM_ACCOUNT: abort(404)
			return self.confirm_account(token)
		def unauthenticated_stub():
			return self.unauthenticated()
		def unauthorized_stub():
			return self.unauthorized()
		# Add the URL routes
		# ------------------
		self.blueprint.add_url_rule('change_password/', 'change_password', change_password_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('change_username/', 'change_username', change_username_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('change_email/', 'change_email', change_email_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('forgot_password/', 'forgot_password', forgot_password_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('reset_password/<token>', 'reset_password', reset_password_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('login/', 'login', login_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('logout/', 'logout', logout_stub, methods=['GET'])
		self.blueprint.add_url_rule('register', 'register', register_stub, methods=['GET', 'POST'])
		self.blueprint.add_url_rule('register/account_verification', 'account_verification', account_verification_stub, methods=['GET'])
		self.blueprint.add_url_rule('register/resend_account_verification', 'resend_account_verification', resend_account_verification_stub, methods=['GET'])
		self.blueprint.add_url_rule('register/confirm_account/<token>', 'confirm_account', confirm_account_stub, methods=['GET'])
		self.blueprint.add_url_rule('unauthenticated/', 'unauthenticated', unauthenticated_stub, methods=['GET'])
		self.blueprint.add_url_rule('unauthorized/', 'unauthorized', unauthorized_stub, methods=['GET'])