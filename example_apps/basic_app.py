# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string, url_for
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from ..flask_auth import current_user, login_required, roles_required, Auth, AuthUserMixin


# Class-based application configuration
class ConfigClass(object):
	""" Flask application config """

	# Flask settings
	SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'
	SERVER_NAME = 'localhost:5000'

	# Flask-SQLAlchemy settings
	SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app2.sqlite'    # File-based SQL database
	SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

	AVAILABLE_LANGUAGES = ['en', 'es']
	AVAILABLE_LANGUAGES_TUPLE = [
		('en', 'English'),
		('es', 'Spanish')
	]

	# Flask-User settings
	AUTH_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
	AUTH_ENABLE_EMAIL = True        # Enable email authentication
	AUTH_ENABLE_USERNAME = True    # Disable username authentication
	AUTH_EMAIL_SENDER_NAME = AUTH_APP_NAME
	AUTH_EMAIL_SENDER_EMAIL = "noreply@example.com"


def create_app():
	""" Flask application factory """
	
	# Create Flask app load app.config
	app = Flask(__name__)
	app.config.from_object(__name__+'.ConfigClass')

	# Initialize Flask-BabelEx
	babel = Babel(app)

	# Initialize Flask-SQLAlchemy
	db = SQLAlchemy(app)

	# Define the User data-model.
	# NB: Make sure to add flask_auth AuthUserMixin !!!
	class User(db.Model, AuthUserMixin):
		__tablename__ = 'users'
		id = db.Column(db.Integer, primary_key=True)
		active = db.Column('is_active', db.Boolean(), nullable=False, default=True)

		# User authentication information. The collation='NOCASE' is required
		# to search case insensitively when AUTH_IFIND_MODE is 'nocase_collation'.
		username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
		email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
		verified = db.Column(db.Boolean(), nullable=False, default=False)
		verified_date = db.Column(db.DateTime())
		password = db.Column(db.String(255), nullable=False, default='')

		# User information
		first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, default='')
		last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, default='')

		# Define the relationship to Role via UserRoles
		roles = db.relationship('Role', secondary='user_roles')

	# Define the Role data-model
	class Role(db.Model):
		__tablename__ = 'roles'
		id = db.Column(db.Integer(), primary_key=True)
		name = db.Column(db.String(50), unique=True)

	# Define the UserRoles association table
	class UserRoles(db.Model):
		__tablename__ = 'user_roles'
		id = db.Column(db.Integer(), primary_key=True)
		user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
		role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

	# Setup Flask-User and specify the User data-model
	auth = Auth(app, db, User)

	# Create all database tables FRESH!
	db.session.commit()
	db.drop_all()
	db.create_all()
	db.session.commit()

	# Create 'member@example.com' user with no roles
	if not User.query.filter(User.email == 'member@example.com').first():
		user = User(
			username='prueba',
			email='member@example.com',
			verified_date=datetime.datetime.utcnow(),
			password=auth.password_manager.hash_password('Password1'),
		)
		db.session.add(user)
		db.session.commit()

	# Create 'admin@example.com' user with 'Admin' and 'Agent' roles
	if not User.query.filter(User.email == 'admin@example.com').first():
		user = User(
			username='prueba2',
			email='admin@example.com',
			verified_date=datetime.datetime.utcnow(),
			password=auth.password_manager.hash_password('Password1'),
		)
		user.roles.append(Role(name='Admin'))
		user.roles.append(Role(name='Agent'))
		db.session.add(user)
		db.session.commit()
	# The Home page is accessible to anyone
	@app.route('/')
	def home_page():
		return 'hello world'

	# The Members page is only accessible to authenticated users
	@app.route('/members/')
	@login_required    # Use of @login_required decorator
	def member_page():
		return render_template_string("""
				{% extends "auth/base.html" %}
				{% block content %}
					<h2>{%trans%}Members page{%endtrans%}</h2>
					<p><a href={{ url_for('auth.register') }}>{%trans%}Register{%endtrans%}</a></p>
					<p><a href={{ url_for('auth.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
					<p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
					<p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
					<p><a href={{ url_for('admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
					<p><a href={{ url_for('auth.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
				{% endblock %}
				""")

	# The Admin page requires an 'Admin' role.
	@app.route('/admin/')
	@roles_required('Admin')    # Use of @roles_required decorator
	def admin_page():
		return render_template_string("""
				{% extends "auth/base.html" %}
				{% block content %}
					<h2>{%trans%}Admin Page{%endtrans%}</h2>
					<p><a href={{ url_for('auth.register') }}>{%trans%}Register{%endtrans%}</a></p>
					<p><a href={{ url_for('auth.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
					<p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
					<p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
					<p><a href={{ url_for('admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
					<p><a href={{ url_for('auth.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
				{% endblock %}
				""")
	return app


# Start development web server
if __name__ == '__main__':
	app = create_app()
	app.run(port=8000, debug=True)
