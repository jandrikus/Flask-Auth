""" This file creates event notification signals for Flask-User.
	Signals are based on Flask.signals which are based on the blinker signals.
"""

# Author: Alejandro Alvarez <jandrikus@gmail.com>
# Copyright (c) 2019 Alejandro Alvarez

from flask.signals import Namespace

_signals = Namespace() # Place Flask-User signals in our own namespace

# *******************
# ** Flask Signals **
# *******************
# Flask signals are based on blinker. Neither Flask nor Flask-User installs blinker
# If you plan to use signals, please install blinker with 'pip install blinker'
# See http://flask.pocoo.org/docs/signals/

# Sent when a user changed their password
auth_changed_password = _signals.signal('auth.auth_changed_password')

# Sent when a user changed their username
auth_changed_username = _signals.signal('auth.auth_changed_username')

# Sent when a user changed their email
auth_changed_email = _signals.signal('auth.auth_changed_email')

# Sent when a user confirmed the account
auth_confirmed_account = _signals.signal('auth.auth_confirmed_account')

# Sent when a user gets the welcome message
auth_welcome = _signals.signal('auth.auth_welcome')

# Sent when a user submitted a password reset request
auth_forgot_password = _signals.signal('auth.auth_forgot_password')

# Sent when a user logged in
auth_logged_in = _signals.signal('auth.auth_logged_in')

# Sent when a user logged out
auth_logged_out = _signals.signal('auth.auth_logged_out')

# Sent when a user registered a new account
auth_registered = _signals.signal('auth.auth_registered')

# Signal sent just after a password was reset
auth_reset_password = _signals.signal('auth.auth_reset_password')