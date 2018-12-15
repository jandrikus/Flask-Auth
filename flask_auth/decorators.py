"""
This module defines Flask-User decorators
such as @login_required, @roles_accepted and @roles_required and @confirmed_email_required.
"""

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from functools import wraps
from flask import current_app, g
from flask_login import current_user

def login_required(view_function):
	"""
	This decorator ensures that the current user is logged in.

	Example::

		@route('/member_page')
		@login_required
		def member_page():  # User must be logged in
			...

	If AUTH_ENABLE_EMAIL is True and AUTH_ENABLE_CONFIRM_ACCOUNT is True,
	this view decorator also ensures that the user has a confirmed account.

	| Calls unauthorized() when the user is not logged in
		or when the user has not confirmed the account.
	| Calls the decorated view otherwise.
	"""
	@wraps(view_function) # Tells debuggers that is is a function wrapper
	def decorator(*args, **kwargs):
		auth = current_app.auth
		allowed = False
		# User must be logged in
		if current_user.is_authenticated:
			# User must be verified (if required)
			if auth.AUTH_ENABLE_CONFIRM_ACCOUNT and current_user.verified:
				allowed=True
			# User can be not verified (if allowed)
			elif not auth.AUTH_ENABLE_CONFIRM_ACCOUNT:
				allowed=True
		if not allowed:
			# Redirect to unauthenticated page
			return auth.unauthenticated()
		# It's OK to call the view
		return view_function(*args, **kwargs)
	return decorator

def allow_unconfirmed_account(view_function):
	"""
	This decorator ensures that the user is logged in,
	but allows users with or without a confirmed account
	to access this particular view.

	It works in tandem with the ``AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT=True`` setting.

	.. caution::

		| Use ``AUTH_ALLOW_LOGIN_WITHOUT_CONFIRMED_ACCOUNT=True`` and
			``@allow_unconfirmed_account`` with caution,
			as they relax security requirements.
		| Make sure that decorated views **never call other views directly**.
			Always use ``redirect()`` to ensure proper view protection.


	Example::

		@route('/show_promotion')
		@allow_unconfirmed_account
		def show_promotion():   # Logged in, with or without
			...                 # confirmed account

	It can also precede the ``@roles_required`` and ``@roles_accepted`` view decorators::

		@route('/show_promotion')
		@allow_unconfirmed_account
		@roles_required('Visitor')
		def show_promotion():   # Logged in, with or without
			...                 # confirmed account

	| Calls unauthorized() when the user is not logged in.
	| Calls the decorated view otherwise.
	"""
	@wraps(view_function) # Tells debuggers that is is a function wrapper
	def decorator(*args, **kwargs):
		auth = current_app.auth
		allowed = False
		# User must be logged in (no need to check verified)
		if current_user.is_authenticated:
			allowed=True
		if not allowed:
			# Redirect to unauthenticated page
			return auth.unauthenticated()
		# It's OK to call the view
		return view_function(*args, **kwargs)
	return decorator

def roles_accepted(*role_names):
	"""
	| This decorator ensures that the current user is logged in,
	| and has *at least one* of the specified roles (OR operation).

	Example::

		@route('/edit_article')
		@roles_accepted('Writer', 'Editor')
		def edit_article():  # User must be 'Writer' OR 'Editor'
			...

	| Calls unauthenticated() when the user is not logged in
		or when user has not confirmed the account.
	| Calls unauthorized() when the user does not have the required roles.
	| Calls the decorated view otherwise.
	"""
	# convert the list to a list containing that list.
	# Because roles_required(a, b) requires A AND B
	# while roles_required([a, b]) requires A OR B
	def wrapper(view_function):

		@wraps(view_function) # Tells debuggers that is is a function wrapper
		def decorator(*args, **kwargs):
			auth = current_app.auth
			# User must be logged in with a confirmed account
			allowed = False
			# User must be logged in
			if current_user.is_authenticated:
				# User must be verified (if required)
				if auth.AUTH_ENABLE_CONFIRM_ACCOUNT and current_user.verified:
					allowed=True
				# User can be not verified (if allowed)
				elif not auth.AUTH_ENABLE_CONFIRM_ACCOUNT:
					allowed=True
			if not allowed:
				# Redirect to unauthenticated page
				return auth.unauthenticated()
			# User must have the required roles
			# NB: roles_required would call has_roles(*role_names): ('A', 'B') --> ('A', 'B')
			# But: roles_accepted must call has_roles(role_names):  ('A', 'B') --< (('A', 'B'),)
			if not current_user.has_roles(role_names):
				# Redirect to the unauthorized page
				return auth.unauthorized()
			# It's OK to call the view
			return view_function(*args, **kwargs)
		return decorator
	return wrapper

def roles_required(*role_names):
	"""
	| This decorator ensures that the current user is logged in,
	| and has *all* of the specified roles (AND operation).

	Example::

		@route('/escape')
		@roles_required('Special', 'Agent')
		def escape_capture():  # User must be 'Special' AND 'Agent'
			...

	| Calls unauthenticated() when the user is not logged in
		or when user has not confirmed the account.
	| Calls unauthorized() when the user does not have the required roles.
	| Calls the decorated view otherwise.
	"""
	def wrapper(view_function):

		@wraps(view_function)    # Tells debuggers that is is a function wrapper
		def decorator(*args, **kwargs):
			auth = current_app.auth
			# User must be logged in with a confirmed account
			allowed = False
			# User must be logged in
			if current_user.is_authenticated:
				# User must be verified (if required)
				if auth.AUTH_ENABLE_CONFIRM_ACCOUNT and current_user.verified:
					allowed=True
				# User can be not verified (if allowed)
				elif not auth.AUTH_ENABLE_CONFIRM_ACCOUNT:
					allowed=True
			if not allowed:
				# Redirect to unauthenticated page
				return auth.unauthenticated()
			# User must have the required roles
			if not current_user.has_roles(*role_names):
				# Redirect to the unauthorized page
				return auth.unauthorized()
			# It's OK to call the view
			return view_function(*args, **kwargs)
		return decorator
	return wrapper