.. _breaking_changes:


Breaking Changes
^^^^^^^^^^^^^^^^

This document details breaking changes from previous SODAR Core releases. It is
recommended to review these notes whenever upgrading from an older SODAR Core
version. For a complete list of changes in the current release, see the
``CHANGELOG.rst`` file.


v0.6.2 (2019-06-21)
===================

System Prerequisites
--------------------

The minimum version requirement for Django has been bumped to 1.11.21.

Template Tag for Django Settings Access Renamed
-----------------------------------------------

The ``get_setting()`` template tag in ``projectroles_common_tags`` has been
renamed into ``get_django_setting()``. In this version the old tag still works,
but this deprecation protection will be removed in the next release. Please
update any references to this tag in your templates.


v0.6.1 (2019-06-05)
===================

App Settings Deprecation Protection Removed
-------------------------------------------

The deprecation protection set up in the previous release has been removed.
Project app plugins are now expected to declare ``app_settings`` in the format
introduced in v0.6.0.


v0.6.0 (2019-05-10)
===================

App Settings (Formerly Project Settings)
----------------------------------------

The former Project Settings module has been completely overhauled in this
version and requries changes to your app plugins.

The ``projectroles.project_settings`` module has been renamed into
``projectroles.app_settings``. Please update your dependencies accordingly.

Settings must now be defined in ``app_settings``. The format is identical to
the previous ``project_settings`` dictionary, except that a ``scope`` field is
expected for each settings. Currently valid values are "PROJECT" and "USER". It
is recommended to use the related constants from ``SODAR_CONSTANTS``
instead of hard coded strings.

Example of settings:

.. code-block:: python

    #: Project and user settings
    app_settings = {
        'project_bool_setting': {
            'scope': 'PROJECT',
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example project setting',
        },
        'user_str_setting': {
            'scope': 'USER',
            'type': 'STRING',
            'label': 'String example',
            'default': '',
            'description': 'Example user setting',
        },
    }

.. warning::

    Deprecation protection is place in this version for retrieving settings from
    ``project_settings`` if it has not been changed into ``app_settings`` in
    your project apps. This protection **will be removed** in the next SODAR
    Core release.


v0.5.1 (2019-04-16)
===================

Site App Templates
------------------

Templates for **site apps** should extend ``projectroles/base.html``. In earlier
versions the documentation erroneously stated ``projectroles/project_base.html``
as the base template to use. Extending that document does work in this version
as long as you override the given template blocks. However, it is not
recommended and may break in the future.

Sodarcache App Changes
----------------------

The following potentially breaking changes have been made to the sodarcache app.

App configuration naming has been changed to
``sodarcache.apps.SodarcacheConfig``. Please update ``config/settings/base.py``
accordingly.

The field ``user`` has been made optional in models and the API.

An optional ``user`` argument has been added to
``ProjectAppPlugin.update_cache()``. Correspondingly, the similar argument in
``ProjectCacheAPI.set_cache_item()`` has been made optional. Please update your
plugin implementations and function calls accordingly.

The ``updatecache`` management command has been renamed to ``synccache``.

Helper get_app_names() Fixed
-----------------------------

The ``projectroles.utils.get_app_names()`` function will now return nested app
names properly instead of omitting everything beyond the topmost module.

Default Admin Setting Deprecation Removed
-----------------------------------------

The ``PROJECTROLES_ADMIN_OWNER`` setting no longer works. Use
``PROJECTROLES_DEFAULT_ADMIN`` instead.


v0.5.0 (2019-04-03)
===================

Default Admin Setting Renamed
-----------------------------

The setting ``PROJECTROLES_ADMIN_OWNER`` has been renamed into
``PROJECTROLES_DEFAULT_ADMIN`` to better reflect its uses. Please rename this
settings variable on your site configuration to prevent issues.

.. note::

    In this release, the old settings value is still accepted in remote project
    management to avoid sudden crashes. This deprecation will be removed in the
    next release.

Bootstrap 4.3.1 Upgrade
-----------------------

The Bootstrap and Popper dependencies have been updated to the latest versions.
Please test your site to make sure this does not result in compatibility issues.
The known issue of HTML content not showing in popovers has already been fixed
in ``projectroles.js``.

Default Templates Modified
--------------------------

The default templates ``base_site.html`` and ``login.html`` have been modified
in this version. If you override them with your own altered versions, please
review the difference and update your templates as appropriate.


v0.4.5 (2019-03-06)
===================

System Prerequisites
--------------------

The minimum version requirement for Django has been bumped to 1.11.20.

User Autocomplete Widget Support
--------------------------------

Due to the use of autocomplete widgets for users, the following apps must be
added into ``THIRD_PARTY_APPS`` in ``config/settings/base.py``, regardless of
whether you intend to use them in your own apps:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'dal',
        'dal_select2',
    ]

Project.get_delegate() Helper Renamed
-------------------------------------

As the limit for delegates per project is now arbitrary, the
``Project.get_delegate()`` helper function has been replaced by
``Project.get_delegates()``. The new function returns a ``QuerySet``.

Bootstrap 4 Crispy Forms Overrides Removed
------------------------------------------

Deprecated site-wide Bootstrap 4 theme overrides for ``django-crispy-forms``
were removed from the example site and are no longer supported. These
workarounds were located in ``{SITE_NAME}/templates/bootstrap4/``. Unless
specifically required forms on your site, it is recommended to remove the files
from your project.

.. note::

    If you choose to keep the files or similar workarounds in your site, you
    are responsible of maintaining them and ensuring SODAR compatibility. Such
    site-wide template overrides are outside of the scope for SODAR Core
    components. Leaving the existing files in without maintenance may cause
    undesireable effects in the future.

Database File Upload Widget
---------------------------

Within SODAR Core apps, the only known issue caused by removal of the
aforementioned Bootstrap 4 form overrides in the file upload widget of the
``django-db-file-upload`` package. If you are using the file upload package in
your own SODAR apps and have removed the site-wide Crispy overrides, you can fix
this particular widget by adding the following snippet into your form template.
Make sure to replace ``{FIELD_NAME}`` with the name of your form field.

.. code-block:: django

    {% block css %}
      {{ block.super }}
      {# Workaround for django-db-file-storage Bootstrap4 issue (#164) #}
      <style type="text/css">
        div#div_id_{FIELD_NAME} div p.invalid-feedback {
        display: block;
      }
      </style>
    {% endblock css %}

Alternatively, you can create a common override in your project-wide CSS file.


v0.4.4 (2019-02-19)
===================

Textarea Height in Forms
------------------------

Due to this feature breaking the layout of certain third party components,
textarea height in forms is no longer adjusted automatically. An exception to
this are Pagedown-specific markdown fields.

To adjust the height of a textarea field in your forms, the easiest way is to
modify the widget of the related field in the ``__init__()`` function of your
form as follows:

.. code-block:: python

    self.fields['field_name'].widget.attrs['rows'] = 4


v0.4.3 (2019-01-31)
===================

SODAR Constants
---------------

``PROJECT_TYPE_CHOICES`` has been removed from ``SODAR_CONSTANTS``, as it can
vary depending on implemented ``DISPLAY_NAMES``. If needed, the currently
applicable form structure can be imported from ``projectroles.forms``.


v0.4.2 (2019-01-25)
===================

System Prerequisites
--------------------

The following minimum version requirements have been upgraded in this release:

- Django 1.11.18+
- Bootstrap 4.2.1
- JQuery 3.3.1
- Numerous required Python packages (see ``requirements/*.txt``)

Please go through your site requirements and update dependencies accordingly.
For project stability, it is still recommended to use exact version numbers for
Python requirements in your SODAR Core based site.

If you are overriding the ``projectroles/base_site.html`` in your site, make
sure to update Javascript and CSS includes accordingly.

.. note::

    Even though the recommended Python version from Django 1.11.17+ is 3.7, we
    only support Python 3.6 for this release. The reason is that some
    dependencies still exhibit problems with the most recent Python release at
    the time of writing.

ProjectAccessMixin
------------------

The ``_get_project()`` function in ``ProjectAccessMixin`` has been renamed into
``get_project()``. Arguments for the function are now optional and may be
removed in a subsequent release: ``self.request`` and ``self.kwargs`` of the
view class will be used if the arguments are not present.

Base API View
-------------

The base SODAR API view has been renamed from ``BaseAPIView`` into
``SODARAPIBaseView``.

Taskflow Backend API
--------------------

The ``cleanup()`` function in ``TaskflowAPI`` now correctly raises a
``CleanupException`` if SODAR Taskflow encounters an error upon calling its
cleanup operation. This change should not affect normally running your site, as
the function in question should only be called during Taskflow testing.


v0.4.1 (2019-01-11)
===================

System Prerequisites
--------------------

Changes in system requirements:

- **Ubuntu 16.04 Xenial** is the target OS version.
- **Python 3.6 or newer required**: 3.5 and older releases no longer supported.
- **PostgreSQL 9.6** is the recommended minimum version for the database.

Site Messages in Login Template
-------------------------------

If your site overrides the default login template in
``projectroles/login.html``, make sure your overridden version contains an
include for ``projectroles/_messages.html``. Following the SODAR Core template
conventions, it should be placed as the first element under the
``container-fluid`` div in the ``content`` block. Otherwise, site app messages
not requiring user authorization will not be visible on the login page. Example:

.. code-block:: django

  {% block content %}
    <div class="container-fluid">
      {# Django messages / site app messages #}
      {% include 'projectroles/_messages.html' %}
      {# ... #}
    </div>
  {% endblock content %}


v0.4.0 (2018-12-19)
===================

List Button Classes in Templates
--------------------------------

Custom small button and dropdown classes for including buttons within tables and
lists have been modified. The naming has also been unified. The following
classes should now be used:

- Button group: ``sodar-list-btn-group`` (formerly ``sodar-edit-button-group``)
- Button: ``sodar-list-btn``
- Dropdown: ``sodar-list-dropdown`` (formerly ``sodar-edit-dropdown``)

See projectroles templates for examples.

.. warning::

    The standard bootstrap class ``btn-sm`` should **not** be used with these
    custom classes!

SODAR Taskflow v0.3.1 Required
------------------------------

If using SODAR Taskflow, this release requires release v0.3.1 or higher due to
mandatory support of the ``TASKFLOW_SODAR_SECRET`` setting.

Taskflow Secret String
----------------------

If you are using the ``taskflow`` backend app, you **must** set the value of
``TASKFLOW_SODAR_SECRET`` in your Django settings. Note that this must match the
similarly named setting in your SODAR Taskflow instance!


v0.3.0 (2018-10-26)
===================

Remote Site Setup
-----------------

For specifying the role of your site in remote project metadata synchronization,
you will need to add two new settings to your Django site configuration:

The ``PROJECTROLES_SITE_MODE`` setting sets the role of your site in remote
project sync and it is **mandatory**. Accepted values are ``SOURCE`` and
``TARGET``. For deployment, it is recommended to fetch this setting from
environment variables.

If your site is set in ``TARGET`` mode, the boolean setting
``PROJECTROLES_TARGET_CREATE`` must also be included to control whether
creation of local projects is allowed. If your site is in ``SOURCE`` mode, this
setting can be included but will have no effect.

Furthermore, if your site is in ``TARGET`` mode you must include the
``PROJECTROLES_ADMIN_OWNER`` setting, which must point to an existing local
superuser account on your site.

Example for a ``SOURCE`` site:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'SOURCE')

Example for a ``TARGET`` site:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'TARGET')
    PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)
    PROJECTROLES_ADMIN_OWNER = env.str('PROJECTROLES_ADMIN_OWNER', 'admin')

General API Settings
--------------------

Add the following lines to your configuration to enable the general API
settings:

.. code-block:: python

    SODAR_API_DEFAULT_VERSION = '0.1'
    SODAR_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar+json'

DataTables Includes
-------------------

Includes for the DataTables Javascript library are no longer included in
templates by default. If you want to use DataTables, include the required CSS
and Javascript in relevant templates. See the ``projectroles/search.html``
template for an example.
