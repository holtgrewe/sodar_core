"""Plugin point definitions and plugin API for apps based on projectroles"""

from django.conf import settings
from djangoplugins.point import PluginPoint


# Local costants
PLUGIN_TYPES = {
    'project_app': 'ProjectAppPluginPoint',
    'backend': 'BackendPluginPoint',
    'site_app': 'SiteAppPluginPoint',
}

# From djangoplugins
ENABLED = 0
DISABLED = 1
REMOVED = 2


# Plugin points ----------------------------------------------------------------


class ProjectAppPluginPoint(PluginPoint):
    """Projectroles plugin point for registering project specific apps"""

    #: App URLs (will be included in settings by djangoplugins)
    urls = []

    #: App settings definition
    #:
    #: Example ::
    #:
    #:     app_settings = {
    #:         'example_setting': {
    #:             'scope': 'PROJECT',  # PROJECT/USER
    #:             'type': 'STRING',  # STRING/INTEGER/BOOLEAN
    #:             'default': 'example',
    #:             'label': 'Project setting',  # Optional, defaults to name/key
    #:             'placeholder': 'Enter example setting here',  # Optional
    #:             'description': 'Example project setting',  # Optional
    #:             'user_modifiable': True,  # Optional, show/hide in forms
    #:         }
    #:     }
    # TODO: Define project specific settings in your app plugin, example above
    app_settings = {}

    # DEPRECATED, will be removed in the next SODAR Core release
    project_settings = {}

    #: FontAwesome icon ID string
    # TODO: Implement this in your app plugin
    icon = 'question-circle-o'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    # TODO: Implement this in your app plugin
    entry_point_url_id = 'home'

    #: Description string
    # TODO: Implement this in your app plugin
    description = 'TODO: Write a description for your plugin'

    #: Required permission for accessing the app
    # TODO: Implement this in your app plugin (can be None)
    app_permission = None

    #: Enable or disable general search from project title bar
    # TODO: Implement this in your app plugin
    search_enable = False

    #: List of search object types for the app
    # TODO: Implement this in your app plugin
    search_types = []

    #: Search results template
    # TODO: Implement this in your app plugin
    search_template = None

    #: App card template for the project details page
    # TODO: Implement this in your app plugin
    details_template = None

    #: App card title for the project details page
    # TODO: Implement this in your app plugin (can be None)
    details_title = None

    #: Position in plugin ordering
    # TODO: Implement this in your app plugin (must be an integer)
    plugin_ordering = 50

    #: Optional project list column definition
    #:
    #: Example ::
    #:
    #:     project_list_columns = {
    #:         'column_id': {
    #:             'title': 'Column Title',
    #:             'width': 100,  # Desired width of column in pixels
    #:             'description': 'Description',  # Optional description string
    #:             'active': True,  # Boolean for whether the column is active
    #:             'align': 'left'  # Alignment of content
    #:         }
    #:     }
    # TODO: Define project list column data in your app plugin (optional)
    project_list_columns = {}

    # NOTE: For projectroles, this is implemented directly in synctaskflow
    def get_taskflow_sync_data(self):
        """
        Return data for synchronizing taskflow operations.

        :return: List of dicts or None.
        """
        '''
        Example of valid return data:
        [
            {
                'flow_name': ''
                'project_pk: ''
                'flow_data': {}
            }
        ]
        '''
        # TODO: Implement this in your app plugin
        return None

    def get_object(self, model, uuid):
        """
        Return object based on the model class and the object's SODAR UUID.

        :param model: Object model class
        :param uuid: sodar_uuid of the referred object
        :return: Model object or None if not found
        :raise: NameError if model is not found
        """
        try:
            return model.objects.get(sodar_uuid=uuid)

        except model.DoesNotExist:
            return None

    def get_object_link(self, model_str, uuid):
        """
        Return the URL for referring to a object used by the app, along with a
        label to be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: Dict or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)

        if not obj:
            return None

        # TODO: Implement this in your app plugin
        return None

    def get_extra_data_link(self, _extra_data, _name):
        """
        Return a link for the given timeline label that stars with ``"extra:"``.
        """
        # TODO: Implement this in your app plugin
        return '(unknown)'

    def search(self, search_term, user, search_type=None, keywords=None):
        """
        Return app items based on a search term, user, optional type and
        optional keywords.

        :param search_term: String
        :param user: User object for user initiating the search
        :param search_type: String
        :param keywords: List (optional)
        :return: Dict
        """
        # TODO: Implement this in your app plugin
        # TODO: Implement display of results in the app's search template
        return {
            'all': {  # You can add 1-N lists of result items
                'title': 'Title to be displayed',
                'search_types': [],
                'items': [],
            }
        }

    def update_cache(self, name=None, project=None, user=None):
        """
        Update cached data for this app, limitable to item ID and/or project.

        :param name: Item name to limit update to (string, optional)
        :param project: Project object to limit update to (optional)
        :param user: User object to denote user triggering the update (optional)
        """
        # TODO: Implement this in your app plugin
        return None

    def get_statistics(self):
        """
        Return app statistics as a dict. Should take the form of
        {id: {label, value, url (optional), description (optional)}}.

        :return: Dict
        """
        # TODO: Implement this in your app plugin
        return {}

    def get_project_list_value(self, column_id, project):
        """
        Return a value for the optional additional project list column specific
        to a project.

        :param column_id: ID of the column (string)
        :param project: Project object
        :return: String (may contain HTML) or None
        """
        # TODO: Implement this in your app plugin (optional)
        return None


class BackendPluginPoint(PluginPoint):
    """Projectroles plugin point for registering backend apps"""

    #: FontAwesome icon ID string
    # TODO: Implement this in your backend plugin
    icon = 'question-circle-o'

    #: Description string
    # TODO: Implement this in your backend plugin
    description = 'TODO: Write a description for your plugin'

    #: URL of optional javascript file to be included
    # TODO: Implement this in your backend plugin if applicable
    javascript_url = None

    def get_api(self):
        """Return API entry point object."""
        # TODO: Implement this in your backend plugin
        raise NotImplementedError

    def get_statistics(self):
        """
        Return backend statistics as a dict. Should take the form of
        {id: {label, value, url (optional), description (optional)}}.

        :return: Dict
        """
        # TODO: Implement this in your backend plugin
        return {}


class SiteAppPluginPoint(PluginPoint):
    """Projectroles plugin point for registering site-wide apps"""

    #: FontAwesome icon ID string
    # TODO: Implement this in your site app plugin
    icon = 'question-circle-o'

    #: Description string
    # TODO: Implement this in your site app plugin
    description = 'TODO: Write a description for your plugin'

    #: Entry point URL ID
    # TODO: Implement this in your app plugin
    entry_point_url_id = 'home'

    #: Required permission for displaying the app
    # TODO: Implement this in your site app plugin (can be None)
    app_permission = None

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.

        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        '''
        Example of valid return data:
        return [{
            'content': 'Message content in here, can contain html',
            'color': 'info',        # Corresponds to bg-* in Bootstrap
            'dismissable': True     # False for non-dismissable
        }]
        '''
        # TODO: Implement this in your site app plugin
        return []


# Plugin API -------------------------------------------------------------------


def get_active_plugins(plugin_type='project_app'):
    """
    Return active plugins of a specific type.

    :param plugin_type: "project_app", "site_app" or "backend" (string)
    :return: List or None
    :raise: ValueError if plugin_type is not recognized
    """
    if plugin_type not in PLUGIN_TYPES.keys():
        raise ValueError(
            'Invalid value for plugin_type. Accepted values: {}'.format(
                ', '.join(PLUGIN_TYPES.keys())
            )
        )

    plugins = eval(PLUGIN_TYPES[plugin_type]).get_plugins()

    if plugins:
        return sorted(
            [
                p
                for p in plugins
                if (
                    p.is_active()
                    and (
                        plugin_type in ['project_app', 'site_app']
                        or p.name in settings.ENABLED_BACKEND_PLUGINS
                    )
                )
            ],
            key=lambda x: x.name,
        )

    return None


def change_plugin_status(name, status, plugin_type='app'):
    """
    Change the status of a selected plugin in the database.

    :param name: Plugin name (string)
    :param status: Status (int, see djangoplugins)
    :param plugin_type: Type of plugin ("app", "backend" or "site")
    :raise: ValueError if plugin_type is invalid or plugin with name not found
    """
    # NOTE: Used to forge plugin to a specific status for e.g. testing
    if plugin_type == 'app':
        plugin = ProjectAppPluginPoint.get_plugin(name)

    elif plugin_type == 'backend':
        plugin = BackendPluginPoint.get_plugin(name)

    elif plugin_type == 'site':
        plugin = SiteAppPluginPoint.get_plugin(name)

    else:
        raise ValueError('Invalid plugin_type: "{}"'.format(plugin_type))

    if not plugin:
        raise ValueError(
            'Plugin of type "{}" not found with name "{}"'.format(
                plugin_type, name
            )
        )

    plugin = plugin.get_model()
    plugin.status = status
    plugin.save()


def get_app_plugin(plugin_name):
    """
    Return active app plugin.

    :param plugin_name: Plugin name (string)
    :return: ProjectAppPlugin object or None if not found
    """
    try:
        return ProjectAppPluginPoint.get_plugin(plugin_name)

    except ProjectAppPluginPoint.DoesNotExist:
        return None


def get_backend_api(plugin_name, force=False):
    """
    Return backend API object.

    :param plugin_name: Plugin name (string)
    :param force: Return plugin regardless of status in ENABLED_BACKEND_PLUGINS
    :return: Plugin object or None if not found
    """
    if plugin_name in settings.ENABLED_BACKEND_PLUGINS or force:
        try:
            plugin = BackendPluginPoint.get_plugin(plugin_name)
            return plugin.get_api() if plugin.is_active() else None

        except Exception:
            pass

    return None


# Plugins within projectroles --------------------------------------------------


class RemoteSiteAppPlugin(SiteAppPluginPoint):
    """Site plugin for remote site and project management"""

    #: Name (slug-safe, used in URLs)
    name = 'remotesites'

    #: Title (used in templates)
    title = 'Remote Site Access'

    #: App URLs (will be included in settings by djangoplugins)
    urls = []

    #: FontAwesome icon ID string
    icon = 'cloud'

    #: Description string
    description = 'Management of remote SODAR sites and remote project access'

    #: Entry point URL ID
    entry_point_url_id = 'projectroles:remote_sites'

    #: Required permission for displaying the app
    app_permission = 'userprofile.update_remote'
