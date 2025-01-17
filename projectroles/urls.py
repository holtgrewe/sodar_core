from django.conf.urls import url

from . import views


app_name = 'projectroles'

urlpatterns = [
    # General project views
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectDetailView.as_view(),
        name='detail',
    ),
    url(
        regex=r'^update/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectUpdateView.as_view(),
        name='update',
    ),
    url(
        regex=r'^create/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    # Search view
    url(
        regex=r'^search/$',
        view=views.ProjectSearchView.as_view(),
        name='search',
    ),
    # Project role views
    url(
        regex=r'^members/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectRoleView.as_view(),
        name='roles',
    ),
    url(
        regex=r'^members/create/(?P<project>[0-9a-f-]+)$',
        view=views.RoleAssignmentCreateView.as_view(),
        name='role_create',
    ),
    url(
        regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentUpdateView.as_view(),
        name='role_update',
    ),
    url(
        regex=r'^members/delete/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentDeleteView.as_view(),
        name='role_delete',
    ),
    # Project invite views
    url(
        regex=r'^invites/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectInviteView.as_view(),
        name='invites',
    ),
    url(
        regex=r'^invites/create/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectInviteCreateView.as_view(),
        name='invite_create',
    ),
    url(
        regex=r'^invites/accept/(?P<secret>[\w\-]+)$',
        view=views.ProjectInviteAcceptView.as_view(),
        name='invite_accept',
    ),
    url(
        regex=r'^invites/resend/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteResendView.as_view(),
        name='invite_resend',
    ),
    url(
        regex=r'^invites/revoke/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteRevokeView.as_view(),
        name='invite_revoke',
    ),
    # Remote site and project views
    url(
        regex=r'^remote/sites$',
        view=views.RemoteSiteListView.as_view(),
        name='remote_sites',
    ),
    url(
        regex=r'^remote/site/add$',
        view=views.RemoteSiteCreateView.as_view(),
        name='remote_site_create',
    ),
    url(
        regex=r'^remote/site/update/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteUpdateView.as_view(),
        name='remote_site_update',
    ),
    url(
        regex=r'^remote/site/delete/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteDeleteView.as_view(),
        name='remote_site_delete',
    ),
    url(
        regex=r'^remote/site/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectListView.as_view(),
        name='remote_projects',
    ),
    url(
        regex=r'^remote/site/access/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectsBatchUpdateView.as_view(),
        name='remote_projects_update',
    ),
    url(
        regex=r'^remote/site/sync/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteProjectsSyncView.as_view(),
        name='remote_projects_sync',
    ),
    # SODAR API views
    url(
        regex=r'^api/remote/get/(?P<secret>[\w\-]+)$',
        view=views.RemoteProjectGetAPIView.as_view(),
        name='api_remote_get',
    ),
    # Ajax API views
    url(
        regex=r'^star/(?P<project>[0-9a-f-]+)',
        view=views.ProjectStarringAPIView.as_view(),
        name='star',
    ),
    url(
        r'^autocomplete/user$',
        view=views.UserAutocompleteAPIView.as_view(),
        name='autocomplete_user',
    ),
    url(
        r'^autocomplete/user/exclude$',
        view=views.UserAutocompleteExcludeMembersAPIView.as_view(),
        name='autocomplete_user_exclude',
    ),
    url(
        r'^autocomplete/user/redirect$',
        view=views.UserAutocompleteRedirectAPIView.as_view(create_field='user'),
        name='autocomplete_user_redirect',
    ),
    url(
        regex=r'^create$', view=views.ProjectCreateView.as_view(), name='create'
    ),
    # Taskflow API views
    url(
        regex=r'^taskflow/get$',
        view=views.TaskflowProjectGetAPIView.as_view(),
        name='taskflow_project_get',
    ),
    url(
        regex=r'^taskflow/update$',
        view=views.TaskflowProjectUpdateAPIView.as_view(),
        name='taskflow_project_update',
    ),
    url(
        regex=r'^taskflow/role/get$',
        view=views.TaskflowRoleAssignmentGetAPIView.as_view(),
        name='taskflow_role_get',
    ),
    url(
        regex=r'^taskflow/role/set$',
        view=views.TaskflowRoleAssignmentSetAPIView.as_view(),
        name='taskflow_role_set',
    ),
    url(
        regex=r'^taskflow/role/delete$',
        view=views.TaskflowRoleAssignmentDeleteAPIView.as_view(),
        name='taskflow_role_delete',
    ),
    url(
        regex=r'^taskflow/settings/get$',
        view=views.TaskflowProjectSettingsGetAPIView.as_view(),
        name='taskflow_settings_get',
    ),
    url(
        regex=r'^taskflow/settings/set$',
        view=views.TaskflowProjectSettingsSetAPIView.as_view(),
        name='taskflow_settings_set',
    ),
]
