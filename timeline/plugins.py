"""Plugins for the Timeline app"""

# Projectroles dependency
from projectroles.plugins import ProjectAppPluginPoint, BackendPluginPoint

from .api import TimelineAPI
from .urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = 'timeline'

    #: Title (used in templates)
    title = 'Timeline'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: Project settings definition
    project_settings = {}

    # Project settings example:
    '''
    {
    'example_boolean_setting': {
        'type': 'BOOLEAN',
        'default': False,
        'description': 'Example boolean setting'},
    'example_string_setting': {
        'type': 'STRING',
        'default': 'Example',
        'description': 'Example string setting'},
    'example_int_setting': {
        'type': 'INTEGER',
        'default': 1000,
        'description': 'Example integer setting'}
    }
    '''

    #: FontAwesome icon ID string
    icon = 'clock-o'

    #: Entry point URL ID (must take project omics_uuid as "project" argument)
    entry_point_url_id = 'timeline:list_project'

    #: Description string
    description = 'Timeline of project events'

    #: Required permission for accessing the app
    app_permission = 'timeline.view_timeline'

    #: Enable or disable general search from project title bar
    search_enable = False   # Not allowed for timeline

    #: App card template for the project details page
    details_template = 'timeline/_details_card.html'

    #: App card title for the project details page
    details_title = 'Project Timeline Overview'

    #: Position in plugin ordering
    plugin_ordering = 40


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'timeline_backend'

    #: Title (used in templates)
    title = 'Timeline Backend'

    #: FontAwesome icon ID string
    icon = 'clock-o'

    #: Description string
    description = 'Timeline backend for modifying events'

    def get_api(self):
        """Return API entry point object."""
        return TimelineAPI()