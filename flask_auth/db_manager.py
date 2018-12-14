# This module implements the DBManager for Flask-Auth.

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from .db_adapters import PynamoDbAdapter, DynamoDbAdapter, MongoDbAdapter, SQLDbAdapter
from . import current_user, ConfigError

class DBManager(object):
	"""Manage DB objects."""

	def __init__(self, app, db, UserClass, RoleClass=None):
		"""Initialize the appropriate DbAdapter, based on the ``db`` parameter type.

		Args:
			app(Flask): The Flask application instance.
			db: The Object-Database Mapper instance.
			UserClass: The User class.
			RoleClass: For testing purposes only.
		"""
		self.app = app
		self.db = db
		self.UserClass = UserClass
		self.RoleClass = RoleClass

		self.auth = app.auth
		self.db_adapter = None

		# Check if db is a SQLAlchemy instance
		if self.db_adapter is None:
			try:
				from flask_sqlalchemy import SQLAlchemy

				if isinstance(db, SQLAlchemy):
					self.db_adapter = SQLDbAdapter(app, db)
			except ImportError:
				pass  # Ignore ImportErrors

		# Check if db is a MongoEngine instance
		if self.db_adapter is None:
			try:
				from flask_mongoengine import MongoEngine

				if isinstance(db, MongoEngine):
					self.db_adapter = MongoDbAdapter(app, db)
			except ImportError:
				pass  # Ignore ImportErrors

		# Check if db is a Flywheel instance
		if self.db_adapter is None: # pragma: no cover
			try:
				from flask_flywheel import Flywheel

				if isinstance(db, Flywheel):
					self.db_adapter = DynamoDbAdapter(app, db)
			except ImportError:
				pass  # Ignore ImportErrors

		# Check if the UserClass is a Pynamo Model
		if self.db_adapter is None:
			try:
				from pynamodb.models import Model

				if issubclass(UserClass, Model):
					self.db_adapter = PynamoDbAdapter(app)
			except ImportError:
				pass # Ignore ImportErrors

		# Check self.db_adapter
		if self.db_adapter is None:
			raise ConfigError(
				'No Flask-SQLAlchemy, Flask-MongoEngine or Flask-Flywheel installed and no Pynamo Model in use.'\
				' You must install one of these Flask extensions.')


	def add_user_role(self, user, role_name):
		# Associate a role name with a user.

		# For SQL: user.roles is list of pointers to Role objects
		if isinstance(self.db_adapter, SQLDbAdapter):
			# user.roles is a list of Role IDs
			# Get or add role
			role = self.db_adapter.find_first_object(self.RoleClass, name=role_name)
			if not role:
				role = self.RoleClass(name=role_name)
				self.db_adapter.add_object(role)
			user.roles.append(role)

		# For others: user.roles is a list of role names
		else:
			# user.roles is a list of role names
			user.roles.append(role_name)

	def add_user(self, **kwargs):
		# Add a User object, with properties specified in ``**kwargs``.
		user = self.UserClass(**kwargs)
		if hasattr(user, 'active'):
			user.active = True
		self.db_adapter.add_object(user)
		return user

	def commit(self):
		# Commit session-based objects to the database.
		self.db_adapter.commit()

	def delete_object(self, object):
		# Delete an object.
		self.db_adapter.delete_object(object)

	def get_user_by_id(self, user_id):
		# Retrieve the User object by ID.
		return self.db_adapter.get_object(self.UserClass, id=user_id)

	def find_user_by_username(self, username):
		# Find a User object by username.
		return self.db_adapter.ifind_first_object(self.UserClass, username=username)

	def find_user_by_email(self, email):
		# Retrieve the User object by email address.
		return self.db_adapter.ifind_first_object(self.UserClass, email=email)

	def get_user_roles(self, user):
		"""
		Retrieve a list of user role names.

		.. note::

			Database management methods.
		"""
		# For SQL: user.roles is list of pointers to Role objects
		if isinstance(self.db_adapter, SQLDbAdapter):
			# user.roles is a list of Role IDs
			user_roles = [role.name for role in user.roles]
		# For others: user.roles is a list of role names
		else:
			# user.roles is a list of role names
			user_roles = user.roles
		return user_roles

	def save_object(self, object):
		# Save an object to the database.
		self.db_adapter.save_object(object)

	def save_user(self, user):
		# Save the User object.
		self.db_adapter.save_object(user)

	def user_has_confirmed_account(self, user):
		"""
		| Returns True if user has a confirmed account.
		| Returns False otherwise.
		"""
		if not self.auth.AUTH_ENABLE_EMAIL: return True
		if not self.auth.AUTH_ENABLE_CONFIRM_ACCOUNT: return True
		# Handle single contact email per user
		return True if user.verified else False

	# Database management methods
	# ---------------------------

	def create_all_tables(self):
		"""Create database tables for all known database data-models."""
		return self.db_adapter.create_all_tables()

	def drop_all_tables(self):
		"""
		Drop all tables.

		.. warning:: ALL DATA WILL BE LOST. Use only for automated testing.
		"""
		return self.db_adapter.drop_all_tables()

