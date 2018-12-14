__title__       = 'Flask-Auth'
__description__ = 'Customizable User Authentication, User Management, and more.'
__version__     = '0.1'
__url__         = 'https://github.com/jandrikus/Flask-Auth'
__author__      = 'Alejandro Alvarez'
__author_email__= 'jandrikus@gmail.com'
__maintainer__  = 'Alejandro Alvarez'
__license__     = 'MIT'
__copyright__   = '(c) 2019 Alejandro Alvarez'

# Define Flask-User Exceptions early on
class ConfigError(Exception):
	pass

class EmailError(Exception):
	pass


# Export Flask-Login's current user
from flask_login import current_user # pass through Flask-Login's current_user

from .user_mixin import AuthUserMixin
from .auth import Auth
from .email_manager import EmailManager
from .password_manager import PasswordManager
from .token_manager import TokenManager

# Export Flask-User decorators
from .decorators import *

# Export Flask-User signals
from .signals import *
