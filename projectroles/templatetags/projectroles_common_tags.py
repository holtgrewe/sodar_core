"""Template tags provided by projectroles for use in other apps"""

from importlib import import_module
import mistune

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.urls import reverse

import projectroles
from projectroles.app_settings import AppSettingAPI
from projectroles.models import Project, RemoteProject, SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.utils import get_display_name as _get_display_name


# SODAR constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


site = import_module(settings.SITE_PACKAGE)
User = get_user_model()

# App settings API
app_settings = AppSettingAPI()

register = template.Library()


# SODAR and site operations ----------------------------------------------------


@register.simple_tag
def site_version():
    """Return the site version"""
    return site.__version__ if hasattr(site, '__version__') else '[UNKNOWN]'


@register.simple_tag
def core_version():
    """Return the SODAR Core version"""
    return projectroles.__version__


@register.simple_tag
def check_backend(name):
    """Return True if backend app is available, else False"""
    return True if get_backend_api(name) else False


@register.simple_tag
def get_project_by_uuid(sodar_uuid):
    """Return Project by sodar_uuid"""
    try:
        return Project.objects.get(sodar_uuid=sodar_uuid)

    except Project.DoesNotExist:
        return None


@register.simple_tag
def get_user_by_username(username):
    """Return User by username"""
    try:
        return User.objects.get(username=username)

    except User.DoesNotExist:
        return None


# Django helpers ---------------------------------------------------------------


@register.simple_tag
def get_django_setting(name, js=False):
    """
    Return value of Django setting by name or None if it is not found.
    Return a Javascript-safe value if js=True.
    """
    val = getattr(settings, name) if hasattr(settings, name) else None

    # If for javascript, modify
    if js and isinstance(val, bool):
        val = int(val)

    return val


# DEPRECATION PROTECTION: To be removed in v0.7.0, use get_django_setting()
@register.simple_tag
def get_setting(name, js=False):
    """
    Return value of Django setting by name or None if it is not found.
    Return a Javascript-safe value if js=True.
    """
    return get_django_setting(name, js)


@register.simple_tag
def get_app_setting(app_name, setting_name, project=None, user=None):
    """
    Get a project/user specific app setting from AppSettingAPI
    """
    return app_settings.get_app_setting(app_name, setting_name, project, user)


@register.simple_tag
def static_file_exists(path):
    """Return True/False based on whether a static file exists"""
    return True if finders.find(path) else False


@register.simple_tag
def template_exists(path):
    """Return True/False based on whether a template exists"""
    try:
        get_template(path)
        return True

    except template.TemplateDoesNotExist:
        return False


@register.simple_tag
def get_full_url(request, url):
    """Get full URL based on a local URL"""
    return request.scheme + '://' + request.get_host() + url


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_display_name(key, title=False, count=1, plural=False):
    """Return display name from SODAR_CONSTANTS"""
    return _get_display_name(key, title, count, plural)


@register.simple_tag
def get_project_title_html(project):
    """Return HTML version of the full project title including parents"""
    ret = ''

    if project.get_parents():
        ret += ' / '.join(project.get_full_title().split(' / ')[:-1]) + ' / '

    ret += project.title
    return ret


@register.simple_tag
def get_project_link(project, full_title=False, request=None):
    """Return link to project with a simple or full title"""
    remote_icon = ''

    if request:
        remote_icon = get_remote_icon(project, request)

    return '<a href="{}">{}</a> {}'.format(
        reverse('projectroles:detail', kwargs={'project': project.sodar_uuid}),
        project.get_full_title() if full_title else project.title,
        remote_icon,
    )


@register.simple_tag
def get_user_html(user):
    """Return standard HTML representation for a User object"""
    return (
        '<a title="{}" href="mailto:{}" data-toggle="tooltip" '
        'data-placement="top">{}'
        '</a>'.format(user.get_full_name(), user.email, user.username)
    )


@register.simple_tag
def get_history_dropdown(project, obj):
    """Return link to object timeline events within project"""
    timeline = get_backend_api('timeline_backend')

    if not timeline:
        return ''

    url = timeline.get_object_url(project.sodar_uuid, obj)
    return (
        '<a class="dropdown-item" href="{}">\n<i class="fa fa-fw '
        'fa-clock-o"></i> History</a>\n'.format(url)
    )


@register.simple_tag
def highlight_search_term(item, term):
    """Return string with search term highlighted"""

    def get_highlights(item):
        pos = item.lower().find(term.lower())
        tl = len(term)

        if pos == -1:
            return item  # Nothing to highlight

        ret = item[:pos]
        ret += (
            '<span class="sodar-search-highlight">'
            + item[pos : pos + tl]
            + '</span>'
        )

        if len(item[pos + tl :]) > 0:
            ret += get_highlights(item[pos + tl :])
        return ret

    return get_highlights(item)


@register.simple_tag
def get_info_link(content, html=False):
    """Return info popover link icon"""
    return (
        '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
        'data-trigger="focus" data-placement="top" data-content="{}" '
        '{}><i class="fa fa-info-circle text-info"></i></a>'.format(
            content, 'data-html="true"' if html else ''
        )
    )


@register.simple_tag
def get_remote_icon(project, request):
    """Get remote project icon HTML"""
    if project.is_remote() and request.user.is_superuser:
        try:
            remote_project = RemoteProject.objects.get(project=project)
            return (
                '<i class="fa fa-globe text-info mx-1 '
                'sodar-pr-remote-project-icon" title="Remote project from '
                '{}" data-toggle="tooltip" data-placement="top">'
                '</i>'.format(remote_project.site.name)
            )

        except RemoteProject.DoesNotExist:
            pass

    return ''


@register.simple_tag
def render_markdown(raw_markdown):
    """Markdown field rendering helper"""
    return mistune.markdown(raw_markdown)


@register.filter
def force_wrap(s, length):
    """Force wrapping of string"""
    # If string contains spaces or hyphens, leave wrapping to browser
    if not {' ', '-'}.intersection(s) and len(s) > length:
        return '<wbr />'.join(
            [s[i : i + length] for i in range(0, len(s), length)]
        )
    return s


# General helpers  -------------------------------------------------------------


@register.simple_tag
def get_class(obj, lower=False):
    """Return object class as string"""
    c = obj.__class__.__name__
    return c.lower() if lower else c
