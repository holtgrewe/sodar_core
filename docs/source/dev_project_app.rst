.. _dev_project_app:


Project App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing
**project apps** to be used with the SODAR Core framework. This also applies for
modifying existing Django apps into project apps.

.. hint::

   The package ``example_project_app`` in the projectroles repository provides
   a concrete minimal example of a working project app.


Project App Basics
==================

**Characteristics** of a project app:

- Provides a functionality related to a project
- Is dynamically included in project views by projectroles using plugins
- Uses the project-based role and access control provided by projectroles
- Is included in projectroles search (optionally)
- Provides a dynamically included element (e.g. content overview) for the
  project details page
- Appears in the project menu sidebar in the default projectroles templates

**Requirements** for setting up a project app:

- Implement project relations and SODAR UUIDs in the app's Django models
- Use provided mixins, keyword arguments and conventions in views
- Extend projectroles base templates in your templates
- Implement specific templates for dynamic inclusion by Projectroles
- Implement ``plugins.py`` with definitions and function implementations
- Implement ``rules.py`` with access rules

Fulfilling these requirements is detailed further in this document.


Prerequisites
=============

This documentation assumes you have a Django project with the ``projectroles``
app set up (see the
:ref:`projectroles integration document <app_projectroles_integration>`).
The instructions can be applied either to modify a previously existing app, or
to set up a fresh app generated in the standard way with
``./manage.py startapp``.

It is also assumed that apps are more or less created according to best
practices defined by `Two Scoops <https://www.twoscoopspress.com/>`_, with the
use of `Class-Based Views <https://docs.djangoproject.com/en/1.11/topics/class-based-views/>`_
being a requirement.


Models
======

In order to hook up your Django models into projects, there are two
requirements: implementing a **project foreign key** and a **UUID field**.

Project Foreign Key
-------------------

Add a ``ForeignKey`` field for the ``projectroles.models.Project`` model,
either called ``project`` or accessible with a ``get_project()`` function
implemented in your model.

If the project foreign key for your is **not** ``project``, make sure to define
a ``get_project_filter_key()`` function. It should return the name of the field
to use as key for filtering your model by project.

.. note::

    If your app contains a complex model structure with e.g. nested models using
    foreign keys, it's not necessary to add this to all your models, just the
    topmost one(s) used e.g. in URL kwargs.

Model UUID Field
----------------

To provide a unique identifier for objects in the SODAR context, add a
``UUIDField`` with the name of ``sodar_uuid`` into your model.

.. note::

    Projectroles links to objects in URLs, links and forms using UUIDs instead
    of database private keys. This is strongly recommended for all Django models
    in apps using the projectroles framework.

.. note::

    When updating an existing Django model with an existing database, the
    ``sodar_uuid`` field needs to be populated. See
    `instructions in Django documentation <https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields>`_
    on how to create the required migrations.

Model Example
-------------

Below is an example of a projectroles-compatible Django model:

.. code-block:: python

    import uuid
    from django.db import models
    from projectroles.models import Project

    class SomeModel(models.Model):
        some_field = models.CharField(
            help_text='Your own field'
        )
        project = models.ForeignKey(
            Project,
            related_name='some_objects',
            help_text='Project in which this object belongs',
        )
        sodar_uuid = models.UUIDField(
            default=uuid.uuid4,
            unique=True,
            help_text='SomeModel SODAR UUID',
        )

.. note::

    The ``related_name`` field is optional, but recommended as it provides an
    easy way to lookup objects of a certain type related to a project. For
    example the ``project`` foreign key in a model called ``Document`` could
    feature e.g. ``related_name='documents'``.


Rules File
==========

Create a file ``rules.py`` in your app's directory. You should declare at least
one basic rule for enabling a user to view the app data for the project. This
can be named e.g. ``{APP_NAME}.view_data``. Predicates for the rules can be
found in projectroles and they can be extended within your app if needed.

.. code-block:: python

    import rules
    from projectroles import rules as pr_rules

    rules.add_perm(
        'example_project_app.view_data',
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
        | pr_rules.is_project_guest,
    )

.. hint::

    The ``rules.is_superuser`` predicate is often redundant, as permission
    checks are skipped for Django superusers. However, it can be handy if you
    e.g. want to define a rule allowing only superuser access for now, with the
    potential for adding other predicates later.


ProjectAppPlugin
================

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``ProjectAppPlugin`` class implementing
``projectroles.plugins.ProjectAppPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import ProjectAppPluginPoint
    from .urls import urlpatterns

    class ProjectAppPlugin(ProjectAppPluginPoint):
        """Plugin for registering app with Projectroles"""
        name = 'example_project_app'
        title = 'Example Project App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

- ``name``: App name (**NOTE:** should correspond to the app package name or
  some functionality may not work as expected)
- ``title``: Printable app title
- ``urls``: Urlpatterns (usually imported from the app's ``urls.py`` file)
- ``icon``: Font Awesome 4.7 icon name (without the ``fa-*`` prefix)
- ``entry_point_url_id``: View ID for the app entry point (**NOTE:** The view
  **must** take the project ``sodar_uuid`` as a kwarg named ``project``)
- ``description``: Verbose description of app
- ``app_permission``: Basic permission for viewing app data in project (see
  above)
- ``search_enable``: Boolean for enabling/disabling app search
- ``details_template``: Path to template to be included in the project details
  page, usually called ``{APP_NAME}/_details_card.html``
- ``details_title``: Title string to be displayed in the project details page
  for the app details template
- ``plugin_ordering``: Number to define the ordering of the app on the project
  menu sidebar and the details page

Implementing the following is **optional**:

- ``app_settings``: Implement if project or user specific settings for the app
  are needed. See the plugin point definition for an example.
- ``search_types``: Implement if searching the data of the app is enabled
- ``search_template``: Implement if searching the data of the app is enabled
- ``project_list_columns``: Optional custom columns do be shown in the project
  list. See the plugin point definition for an example.
- ``get_taskflow_sync_data()``: Applicable only if working with
  ``sodar_taskflow`` and iRODS
- ``get_object_link()``: If Django models are associated with the app. Used e.g.
  by ``django-sodar-timeline``.
- ``search()``: Function called when searching for data related to the app if
  search is enabled
- ``get_statistics()``: Return statistics for the siteinfo app. See details in
  :ref:`the siteinfo documentation <app_siteinfo>`.
- ``get_project_list_value()``: A function which **must** be implemented if
  ``project_list_columns`` are defined, to retrieve a column cell value for a
  specific project.

Once you have implemented the ``rules.py`` and ``plugins.py`` files and added
the app and its URL patterns to the Django site configuration, you can create
the project app plugin in the Django databse with the following command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output to ensure the plugin was successfully
registered:

.. code-block:: console

    Registering Plugin for {APP_NAME}.plugins.ProjectAppPlugin

For info on how to implement the specific required views/templates, see the end
of this document.


Views
=====

Certain guidelines must be followed in developing Django web UI views for them
to be successfully used with projectroles.

URL Keyword Arguments
---------------------

In order to link a view to project and check user permissions using mixins,
the URL keyword arguments **must** include an argument which matches *one of
the following conditions*:

- Contains a kwarg ``project`` which corresponds to the ``sodar_uuid``
  member value of a ``projectroles.models.Project`` object
- Contains a kwarg corresponding to the ``sodar_uuid`` of another Django
  model, which must contain a member field ``project`` which is a foreign key
  for a ``Projectroles.models.Project`` object. The kwarg **must** be named
  after the Django model of the referred object (in lowercase).
- Same as above, but the Django model provides a
  ``get_project()`` function which returns (you guessed it) a
  ``Projectroles.models.Project`` object.

Examples:

.. code-block:: python

   urlpatterns = [
       # Direct reference to the Project model
       url(
           regex=r'^(?P<project>[0-9a-f-]+)$',
           view=views.ProjectDetailView.as_view(),
           name='detail',
       ),
       # RoleAssignment model has a "project" member which is also OK
       url(
           regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
           view=views.RoleAssignmentUpdateView.as_view(),
           name='role_update',
       ),
   ]

Mixins
------

The ``projectroles.views`` module provides several useful mixins for augmenting
your view classes to add projectroles functionality. These can be found in the
``projectroles.views`` module.

The most commonly used mixins:

- ``LoggedInPermissionMixin``: Ensure correct redirection of users on no
  permissions
- ``ProjectPermissionMixin``: Provides a ``Project`` object for permission
  checking based on URL kwargs
- ``ProjectContextMixin``: Provides a ``Project`` object into the view context
  based on URL kwargs

See ``example_project_app.views.ExampleView`` for an example.


Templates
=========

Template Structure
------------------

It is strongly recommended to extend ``projectroles/project_base.html`` in your
project app templates. Just start your template with the following line:

.. code-block:: django

    {% extends 'projectroles/project_base.html' %}

The following **template blocks** are available for overriding or extending when
applicable:

- ``title``: Page title
- ``css``: Custom CSS (extend with ``{{ block.super }}``)
- ``projectroles_extend``: Your app content goes here!
- ``javascript``: Custom Javascript (extend with ``{{ block.super }}``)
- ``head_extend``: Optional block if you need to include additional content
  inside the HTML ``<head>`` element

Within the ``projectroles_extend`` block, it is recommended to use the
following ``div`` classes, both extending the Bootstrap 4 ``container-fluid``
class:

- ``sodar-subtitle-container``: Container for the page title
- ``sodar-content-container``: Container for the actual content of your app

Rules
-----

To control user access within a template, just do it as follows:

.. code-block:: django

    {% load rules %}
    {% has_perm 'app.do_something' request.user project as can_do_something %}

This checks if the current user from the HTTP request has permission for
``app.do_something`` in the current project retrieved from the page context.

Template Tags
-------------

General purpose template tags are available in
``projectroles/templatetags/projectroles_common_tags.py``. Include them to your
template as follows:

.. code-block:: django

    {% load projectroles_common_tags %}

Example
-------

Minimal example for a project app template:

.. code-block:: django

    {% extends 'projectroles/project_base.html' %}

    {% load projectroles_common_tags %}
    {% load rules %}

    {% block title %}
      Page Title
    {% endblock title %}

    {% block head_extend %}
      {# OPTIONAL: extra content under <head> goes here #}
    {% endblock head_extend %}

    {% block css %}
      {{ block.super }}
      {# OPTIONAL: Extend or override CSS here #}
    {% endblock css %}

    {% block projectroles_extend %}

      {# Page subtitle #}
      <div class="container-fluid sodar-subtitle-container">
        <h3><i class="fa fa-rocket"></i> App and/or Page Title/h3>
      </div>

      {# App content #}
      <div class="container-fluid sodar-page-container">
        <p>Your app content goes here!</p>
      </div>

    {% endblock projectroles_extend %}

    {% block javascript %}
      {{ block.super }}
      {# OPTIONAL: include additional Javascript here #}
    {% endblock javascript %}

See ``example_project_app/example.html`` for a working and fully commented
example of a minimal template.

.. hint::

    If you include some controls on your ``sodar-subtitle-container`` class and
    want it to remain sticky on top of the page while scrolling, use ``row``
    instead of ``container-fluid`` and add the ``bg-white sticky-top`` classes
    to the element.


General Guidelines for Views and Templates
==========================================

General guidelines and hints for developing views and templates are discussed
in this section.

Referring to Project Type
-------------------------

As of SODAR Core v0.4.3, it is possible to customize the display name for the
project type from the default "project" or "category". For more information, see
:ref:`app_projectroles_custom`.

It is thus recommended that instead of hard coding "project" or "category" in
your views or templates, use the ``get_display_name()`` function to refer to
project type.

In templates, this can be achieved with a custom template tag. Example:

.. code-block:: django

    {% load projectroles_common_tags %}
    {% get_display_name project.type title=True plural=False %}

In views and other Python code, the similar function can be accessed through
``utils.py``:

.. code-block:: python

    from projectroles.utils import get_display_name
    display_name = get_display_name(project.type, plural=False)

.. hint::

    If not dealing with a ``Project`` object, you can provide the
    ``PROJECT_TYPE_*`` constant from ``SODAR_CONSTANTS``. In templates, it's
    most straightforward to use "CATEGORY" and "PROJECT".


Forms
=====

This section contains guidelines for implementing forms.

Custom User Selection Widget
----------------------------

A widget for autocomplete user selection in forms is available and can be build
into any form.

First, the ``UserAutocompleteWidget`` needs to be imported from
``projectroles/forms.py``.

.. code-block:: python

    from projectroles.forms import UserAutocompleteWidget

In your form's ``Meta`` class, assign the ``UserAutocompleteWidget`` as the
widget of the user field:

.. code-block:: python

    class YourForm(forms.ModelForm):

        class Meta:
            model = YourModel
            fields ['user'] # ...
            widgets = {
                'user': UserAutocompleteWidget(
                url='projectroles:autocomplete_user',
                forward=['project'],
            )
        }

Some parameters have to be specified:

- ``url``: The URL of the ``UserAutocompleteAPIView`` (or another custom API
  view)
- ``forward``: Optional list with fields whose values will be forwarded to the
  view

If you wish to only display users who are members of a certain project, you need
to include a field with the project's UUID in the form. This form can be hidden.
This field's value needs to be forwarded to the autocomplete view (like in the
code example above).

The alternative ``UserAutocompleteExcludeMembersAPIView`` view provides the
opposite functionality: only users that are *not* project members are shown.
That can be useful, for example, in a form to invite new members. To have the
widget exclude project members, just change the URL parameter to the
``UserAutocompleteExcludeMembersAPIView``'s URL
(``projectroles:autocomplete_user_exclude``).
In that same way, you can provide your custom view's URL to the widget to
change its behaviour.

Also, as is required by SODAR, the user and the project fields need to point to
SODAR UUIDs:

.. code-block:: python

    self.fields['project'].to_field_name = 'sodar_uuid'
    self.fields['user'].to_field_name = 'sodar_uuid'

The following ``django-autocomplete-light`` and ``select2`` stylesheets and
javascript files have to be added to the html template that includes the form.

.. code-block:: django

    {% block javascript %}
      {{ block.super }}
      <!-- DAL for autocomplete widgets -->
      <script type="text/javascript" src="{% static 'autocomplete_light/jquery.init.js' %}"></script>
      <script type="text/javascript" src="{% static 'autocomplete_light/autocomplete.init.js' %}"></script>
      <script type="text/javascript" src="{% static 'autocomplete_light/vendor/select2/dist/js/select2.full.js' %}"></script>
      <script type="text/javascript" src="{% static 'autocomplete_light/select2.js' %}"></script>
    {% endblock javascript %}

    {% block css %}
      {{ block.super }}
      <!-- Select2 theme -->
      <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.6-rc.0/css/select2.min.css" rel="stylesheet" />
    {% endblock css %}

When using the ``RedirectWidget`` or any other widget with custom javascript,
include the corresponding js file instead of ``autocomplete_light/select2.js``.

If you create your own custom user selection widget on the basis of the
``UserAutocompleteWidget`` take a look at the ``RedirectWidget`` as an example,
or check out the ``django-autocomplete-light`` documentation for more
information on how to customize your autocomplete-widget.


Specific Views and Templates
============================

A few specific views/templates are expected to be implemented.

App Entry Point
---------------

As described in the Plugins chapter, an app entry point view is to be defined
in the ``ProjectAppPlugin``. This is **mandatory**.

The view **must** take a ``project`` URL kwarg which corresponds to a
``Project.sodar_uuid``.

For an example, see ``example_project_app.views.ExampleView`` and the associated
template.

Project Details Element
-----------------------

A sub-template to be included in the project details page (the project's "front
page" provided by projectroles, where e.g. overview of app content is shown).

Traditionally these files are called ``_details_card.html``, but you can name
them as you wish and point to the related template in the ``details_template``
variable of your plugin.

It is expected to have the content in a ``card-body`` container:

.. code-block:: django

   <div class="card-body">
     {# Content goes here #}
   </div>


Project Search Function and Template
====================================

If you want to implement search in your project app, you need to implement the
``search()`` function in your plugin as well as a template for displaying the
results.

.. hint::

   Implementing search *can* be complex. If you have access to the main SODAR
   repository, apps in that project might prove useful examples.

The search() Function
---------------------

See the signature of ``search()`` in
``projectroles.plugins.ProjectAppPluginPoint``. The arguments are as follows:

- ``search_term``
    - Term to be searched for (string). Should be self-explanatory.
    - Multiple strings or separating multiple phrases with quotation marks not
      yet supported.
- ``user``
    - User object for user initiating search
- ``search_type``
    - The type of object to search for (string, optional)
    - Used to restrict search to specific types of objects
    - You can specify supported types in the plugin's ``search_types`` list.
    - Examples: ``file``, ``sample``..
- ``keywords``
    - Special search keywords, e.g. "exact"
    - **NOTE:** Currently not implemented

.. note::

   Within this function, you are expected to verify appropriate access of the
   seaching user yourself!

The return data is a dictionary, which is split by groups in case your app can
return multiple different lists for data. This is useful where e.g. the same
type of HTML list isn't suitable for all returnable types. If only returning one
type of data, you can just use e.g. ``all`` as your only category. Example of
the result:

.. code-block:: python

   return {
       'all': {                     # 1-N categories to be included
           'title': 'List title',   # Title of the result list to be displayed
           'search_types': [],      # Object types included in this category
           'items': []              # The actual objects returned
           }
       }

Search Template
---------------

Projectroles will provide your template context the ``search_results`` object,
which corresponds to the result dict of the aforementioned function. There are
also includes for formatting the results list, which you are encouraged to use.

Example of a simple results template, in case of a single ``all`` category:

.. code-block:: django

   {% if search_results.all.items|length > 0 %}

     {# Include standard search list header here #}
     {% include 'projectroles/_search_header.html' with search_title=search_results.all.title result_count=search_results.all.items|length %}

     {# Set up a table with your results #}
     <table class="table table-striped sodar-card-table sodar-search-table" id="sodar-ff-search-table">
       <thead>
         <tr>
           <th>Name</th>
           <th>Some Other Field</th>
         </tr>
      </thead>
      <tbody>
        {% for item in search_results.all.items %}
          <tr>
            <td>
              <a href="#link_to_somewhere_in your_app">{{ item.name }}</a>
            </td>
            <td>
              {{ item.some_other_field }}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {# Include standard search list footer here #}
    {% include 'projectroles/_search_footer.html' %}

  {% endif %}


Tour Help
=========

SODAR Core uses `Shepherd <https://shipshapecode.github.io/shepherd/docs/welcome/>`_
to present an optional interactive tour for a rendered page. To enable the tour
in your template, set it up inside the ``javascript`` template block. Within an
inline javascript strucure, set the ``tourEnabled`` variable to ``true`` and add
steps according to the `Shepherd documentation <https://shipshapecode.github.io/shepherd>`_.

Example:

.. code-block:: django

    {% block javascript %}
      {{ block.super }}

      {# Tour content #}
      <script type="text/javascript">
        tourEnabled = true;

        /* Normal step */
        tour.addStep('id_of_step', {
            title: 'Step Title',
            text: 'Description of the step',
            attachTo: '#some-element top',
            advanceOn: '.docs-link click',
            showCancelLink: true
        });

        /* Conditional step */
        if ($('.potentially-existing-element').length) {
            tour.addStep('id_of_another_step', {
                title: 'Another Title',
                text: 'Another description here',
                attachTo: '.potentially-existing-element right',
                advanceOn: '.docs-link click',
                showCancelLink: true
            });
        }

      </script>
    {% endblock javascript %}


.. warning::

    Make sure you call ``{{ block.super }}`` at the start of the declared
    ``javascript`` block or you will overwrite the site's default Javascript
    setup!


API Views
=========

API View usage will be explained in this chapter, currently under construction.

.. warning::

    A unified SODAR API is currently under development and will be documented
    once stable. Current practices and base classes for API views are subject to
    change!

Ajax API Views
--------------

To set up Ajax API views for the UI, you can use the standard login and project
permission mixins along with ``APIPermissionMixin`` together with any Django
Rest Framework view class. Permissions can be managed as with normal Django
views. Example with generic ``APIView``:

.. code-block:: python

    from rest_framework.views import APIView
    from projectroles.views import (
        LoginRequiredMixin,
        ProjectPermissionMixin,
        APIPermissionMixin,
    )

    class ExampleAjaxAPIView(
            LoginRequiredMixin,
            ProjectPermissionMixin,
            APIPermissionMixin,
            APIView,
    ):

    permission_required = 'projectroles.view_project'

    def get(self, request):
        # ...


TODO
====

- Naming conventions
- Examples of recurring template styles (e.g. forms)
