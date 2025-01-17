"""Configuration for developing the remote project feature in TARGET mode"""

from .local import *  # noqa

import socket
import os


# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# Uses django-environ to accept uri format
# See: https://django-environ.readthedocs.io/en/latest/#supported-types
DATABASES['default']['NAME'] = 'sodar_core_target'
DATABASES['default']['ATOMIC_REQUESTS'] = False


# General site settings
# ------------------------------------------------------------------------------

SITE_TITLE = 'SODAR Core Target Dev Site'
SITE_SUBTITLE = env.str('SITE_SUBTITLE', 'Beta')
SITE_INSTANCE_TITLE = env.str(
    'SITE_INSTANCE_TITLE', 'SODAR Core Target Example'
)


# Local App Settings
# ------------------------------------------------------------------------------

PROJECTROLES_SITE_MODE = 'TARGET'

# Username of default admin for when regular users cannot be assigned to a task
PROJECTROLES_DEFAULT_ADMIN = 'admin_target'

# Allowing local users by default when developing target site locally
PROJECTROLES_ALLOW_LOCAL_USERS = True
