from django import template
from django.urls import reverse
from django.utils.timezone import localtime

# Projectroles dependency
from projectroles.plugins import ProjectAppPluginPoint

from timeline.api import TimelineAPI
from timeline.models import ProjectEvent

register = template.Library()


STATUS_STYLES = {
    'OK': 'bg-success',
    'INIT': 'bg-secondary',
    'SUBMIT': 'bg-warning',
    'FAILED': 'bg-danger',
    'INFO': 'bg-info',
    'CANCEL': 'bg-dark',
}

# Event helpers ----------------------------------------------------------------


@register.simple_tag
def get_timestamp(event):
    """Return printable timestamp of event in local timezone"""
    return localtime(event.get_timestamp()).strftime('%Y-%m-%d %H:%M:%S')


@register.simple_tag
def get_event_description(event, request=None):
    """Return printable version of event description"""
    timeline = TimelineAPI()
    return timeline.get_event_description(event, request)


@register.simple_tag
def get_details_events(project, view_classified):
    """Return recent events for card on project details page"""
    events = ProjectEvent.objects.filter(project=project)

    if not view_classified:
        events = events.exclude(classified=True)

    events = events.order_by('-pk')

    return [x for x in events if x.get_current_status().status_type == 'OK'][:5]


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_status_style(status):
    """Retrn status style class"""
    return (
        (STATUS_STYLES[status.status_type] + ' text-light')
        if status.status_type in STATUS_STYLES
        else 'bg-light'
    )


@register.simple_tag
def get_app_url(event):
    """Return URL for event application"""
    # Projectroles is a special case
    if event.app == 'projectroles':
        return reverse(
            'projectroles:detail', kwargs={'project': event.project.sodar_uuid}
        )

    else:
        app_plugin = ProjectAppPluginPoint.get_plugin(event.app)

        if app_plugin:
            return reverse(
                app_plugin.entry_point_url_id,
                kwargs={'project': event.project.sodar_uuid},
            )

    return '#'


@register.simple_tag
def get_event_details(event):
    """Return HTML data for event detail popover"""
    ret = (
        '<table class="table table-striped sodar-card-table '
        'sodar-tl-table-detail">\n'
        '<thead>\n<th>Timestamp</th>\n<th>Description</th>\n'
        '<th>Status</th>\n</thead>\n<tbody>'
    )
    status_changes = event.get_status_changes(reverse=True)

    for status in status_changes:
        ret += (
            '\n<tr><td>{}</td>\n<td>{}</td>\n'
            '<td class="{}">{}</td>\n</tr>'.format(
                localtime(status.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                status.description[:256]
                + (
                    '<em class="text-muted"> (...)</em>'
                    if len(status.description) > 256
                    else ''
                ),
                get_status_style(status),
                status.status_type,
            )
        )
    ret += '\n</tbody>\n</table>'
    return ret
