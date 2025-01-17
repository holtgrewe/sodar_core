# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from .api import ExampleAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'example_backend_app'

    #: Title (used in templates)
    title = 'Example Backend App'

    #: FontAwesome icon ID string
    icon = 'code'

    #: Description string
    description = 'Example Backend API'

    #: URL of optional javascript file to be included
    javascript_url = None

    def get_api(self):
        """Return API entry point object."""
        return ExampleAPI()

    def get_statistics(self):
        return {
            'backend_example_stat': {'label': 'Backend example', 'value': True}
        }
