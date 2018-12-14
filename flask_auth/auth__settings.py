# This module defines Auth settings and their defaults.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

# This class mixes into the Auth class.
# Mixins allow for maintaining code and docs across several files.
class Auth__Settings(object):
	"""
	Flask-Auth settings and their defaults.

	.. This hack shows a header above the _next_ section
	.. code-block:: none

		Feature settings
	"""
	#: | Settings for registration

	#: | Allow users to login and register with an email address
	AUTH_ENABLE_EMAIL = True

	#: | Allow users to login and register with a username
	AUTH_ENABLE_USERNAME = True

	#: | Allow users to change their username.
	#: | Depends on AUTH_ENABLE_USERNAME=True.
	AUTH_ENABLE_CHANGE_USERNAME = True

	#: | Allow users to change their password.
	AUTH_ENABLE_CHANGE_PASSWORD = True

	#: | Require users to verify/confirm the account.
	AUTH_ENABLE_CONFIRM_ACCOUNT = True

	#: | If True, the app will look for a custom method to select
	#: | the desired email address to send the security driven emails
	#: | Override -> class CustomEmailManager(EmailManager)
	#: | and use customize() method in Auth
	AUTH_ENABLE_CUSTOM_SPECIFIC_EMAIL_FOR_TOKEN = False

	#: | Enable account verification/confirmation emails to be sent.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	#: | Depends on AUTH_ENABLE_CONFIRM_ACCOUNT=True.
	AUTH_ENABLE_CONFIRM_ACCOUNT_EMAIL = True

	#: | Allow users to reset their passwords.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_ENABLE_FORGOT_PASSWORD = True

	#: | Allow unregistered users to register.
	AUTH_ENABLE_REGISTER = True

	#: | Remember user sessions across browser restarts.
	#:
	#: .. This hack shows a header above the _next_ section
	#: .. code-block:: none
	#:
	#:     Generic settings and their defaults
	AUTH_ENABLE_REMEMBER_ME = True

	#: The application name displayed in email templates and page template footers.
	AUTH_APP_NAME = 'AUTH_APP_NAME'

	#: Automatic sign-in if the user session has not expired.
	AUTH_AUTO_LOGIN = True

	#: Automatic sign-in after a user verifies/confirms the account.
	AUTH_AUTO_LOGIN_AFTER_CONFIRM = True

	#: Automatic sign-in after a user registers.
	#: | Depends on AUTH_ENABLE_CONFIRM_ACCOUNT=False.
	AUTH_AUTO_LOGIN_AFTER_REGISTER = True

	#: Automatic sign-in after a user resets their password.
	AUTH_AUTO_LOGIN_AFTER_RESET_PASSWORD = True

	#: Automatic sign-in at the login form (if the user session has not expired).
	AUTH_AUTO_LOGIN_AT_LOGIN = True

	#: | Sender's email address.
	#: | Required for sending emails.
	#: | Derived from MAIL_DEFAULT_SENDER or DEFAULT_MAIL_SENDER when specified.
	AUTH_EMAIL_SENDER_EMAIL = ''

	#: | Sender's name.
	#: | Optional. Defaults to AUTH_APP_NAME setting.
	AUTH_EMAIL_SENDER_NAME = ''

	#: | The way Flask-User handles case insensitive searches.
	#: | Valid options are:
	#: | - 'ifind' (default): Use the case insensitive ifind_first_object()
	#: | - 'nocase_collation': username and email fields must be configured
	#: |     with an case insensitve collation (collation='NOCASE' in SQLAlchemy)
	#: |     so that a regular find_first_object() can be performed.
	AUTH_IFIND_MODE = 'ifind'

	#: | Send notification email after a password change.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_SEND_PASSWORD_CHANGED_EMAIL = True

	#: | Send wellcome notification email after a registration.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_SEND_WELLCOME_EMAIL = True

	#: | Send notification email after a username change.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_SEND_USERNAME_CHANGED_EMAIL = True

	#: | Send notification email after a email change.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_SEND_EMAIL_CHANGED_EMAIL = True

	#: | Ensure that users can login only with a confirmed account.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	#:
	#: This setting works in tandem with the ``@allow_unconfirmed_account``
	#: view decorator to allow users without confirmed account
	#: to access certain views.
	#:
	#: .. caution::
	#:
	#:     | Use ``AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT=True`` and
	#:         ``@allow_unconfirmed_account`` with caution,
	#:         as they relax security requirements.
	#:     | Make sure that decorated views **never call other views directly**.
	#:         Allways se ``redirect()`` to ensure proper view protection.

	AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT = False

	#: | Require users to retype their password.
	#: | Affects registration, change password and reset password forms.
	AUTH_REQUIRE_RETYPE_PASSWORD = True

	#: | Show 'Email does not exist' message instead of 'Incorrect Email or password'.
	#: | Depends on AUTH_ENABLE_EMAIL=True.
	AUTH_SHOW_EMAIL_DOES_NOT_EXIST = False

	#: | Show 'Username does not exist' message instead of 'Incorrect Username or password'.
	#: | Depends on AUTH_ENABLE_USERNAME=True.
	AUTH_SHOW_USERNAME_DOES_NOT_EXIST = False

	#: | User session token expiration in seconds.
	#: | Default is 1 hour (1*3600 seconds).
	#:
	#: .. This hack shows a header above the _next_ section
	#: .. code-block:: none
	#:
	#:     Password hash settings
	AUTH_USER_SESSION_EXPIRATION = 1*3600

	#: | Email confirmation token expiration in seconds.
	#: | Default is 2 days (2*24*3600 seconds).
	AUTH_CONFIRM_EMAIL_EXPIRATION = 2*24*3600

	#: | Reset password token expiration in seconds.
	#: | Default is 2 days (2*24*3600 seconds).
	AUTH_RESET_PASSWORD_EXPIRATION = 2*24*3600

	#: | List of accepted password hashes.
	#: | See `Passlib CryptContext docs on Constructor Keyword ``'schemes'`` <http://passlib.readthedocs.io/en/stable/lib/passlib.context.html?highlight=cryptcontext#constructor-keywords>`_
	#: | Example: ``['bcrypt', 'argon2']``
	#: |   Creates new hashes with 'bcrypt' and verifies existing hashes with 'bcrypt' and 'argon2'.
	AUTH_PASSLIB_CRYPTCONTEXT_SCHEMES = ['bcrypt']

	#: | Dictionary of CryptContext keywords and hash options.
	#: | See `Passlib CryptContext docs on Constructor Keywords <http://passlib.readthedocs.io/en/stable/lib/passlib.context.html?highlight=cryptcontext#constructor-keywords>`_
	#: | and `Passlib CryptContext docs on Algorithm Options <http://passlib.readthedocs.io/en/stable/lib/passlib.context.html?highlight=cryptcontext#algorithm-options>`_
	#: | Example: ``dict(bcrypt__rounds=12, argon2__time_cost=2, argon2__memory_cost=512)``
	#:
	#: .. This hack shows a header above the _next_ section
	#:     URL settings
	AUTH_PASSLIB_CRYPTCONTEXT_KEYWORDS = dict()