import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from djangoplugins.models import Plugin
from markupfield.fields import MarkupField


from .utils import set_user_group


# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# Global constants
SODAR_CONSTANTS = {
    # Project roles
    'PROJECT_ROLE_OWNER': 'project owner',
    'PROJECT_ROLE_DELEGATE': 'project delegate',
    'PROJECT_ROLE_CONTRIBUTOR': 'project contributor',
    'PROJECT_ROLE_GUEST': 'project guest',

    # Project types
    'PROJECT_TYPE_CATEGORY': 'CATEGORY',
    'PROJECT_TYPE_PROJECT': 'PROJECT',

    # Submission status
    'SUBMIT_STATUS_OK': 'OK',
    'SUBMIT_STATUS_PENDING': 'PENDING',
    'SUBMIT_STATUS_PENDING_TASKFLOW': 'PENDING-TASKFLOW',

    # RemoteSite mode
    'SITE_MODE_SOURCE': 'SOURCE',
    'SITE_MODE_TARGET': 'TARGET',

    # RemoteProject access types
    'REMOTE_LEVEL_NONE': 'NONE',
    'REMOTE_LEVEL_VIEW_AVAIL': 'VIEW_AVAIL',
    'REMOTE_LEVEL_READ_INFO': 'READ_INFO',
    'REMOTE_LEVEL_READ_ROLES': 'READ_ROLES'
}

# Choices for forms/admin with project type
SODAR_CONSTANTS['PROJECT_TYPE_CHOICES'] = [
    (SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'], 'Category'),
    (SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'], 'Project')]

# RemoteSite modes
SODAR_CONSTANTS['SITE_MODES'] = [
    SODAR_CONSTANTS['SITE_MODE_SOURCE'],
    SODAR_CONSTANTS['SITE_MODE_TARGET']]

# RemoteProject access levels
SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'] = {
    SODAR_CONSTANTS['REMOTE_LEVEL_NONE']: 'No access',
    SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']: 'View availability',
    SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']: 'Read information',
    SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']: 'Read members'}

# Local constants
PROJECT_SETTING_TYPES = [
    'BOOLEAN',
    'INTEGER',
    'STRING']

PROJECT_SETTING_TYPE_CHOICES = [
    ('BOOLEAN', 'Boolean'),
    ('INTEGER', 'Integer'),
    ('STRING', 'String')]

PROJECT_SETTING_VAL_MAXLENGTH = 255

PROJECT_SEARCH_TYPES = [
    'project']

PROJECT_TAG_STARRED = 'STARRED'


# Project ----------------------------------------------------------------------


class ProjectManager(models.Manager):
    """Manager for custom table-level Project queries"""
    def find(self, search_term, keywords=None, project_type=None):
        """
        Return projects with a partial match in full title or, including titles
        of parent Project objects, or the description of the current object.
        Restrict to project type if project_type is set.
        :param search_term: Search term (string)
        :param keywords: Optional search keywords as key/value pairs (dict)
        :param project_type: Project type or None
        :return: Python list of Project objects
        """
        search_term = search_term.lower()
        projects = super(
            ProjectManager, self).get_queryset().order_by('title')

        if project_type:
            projects = projects.filter(type=project_type)

        # NOTE: Can't use a custom function in filter()
        result = [
            p for p in projects if (
                search_term in p.get_full_title().lower() or
                search_term in p.description.lower())]

        return sorted(result, key=lambda x: x.get_full_title())


class Project(models.Model):
    """A SODAR project. Can have one parent category in case of nested
    projects. The project must be of a specific type, of which "CATEGORY" and
    "PROJECT" are currently implemented. "CATEGORY" projects are used as
    containers for other projects"""

    #: Project title
    title = models.CharField(
        max_length=255,
        unique=False,
        help_text='Project title')

    #: Type of project ("CATEGORY", "PROJECT")
    type = models.CharField(
        max_length=64,
        choices=SODAR_CONSTANTS['PROJECT_TYPE_CHOICES'],
        default=SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
        help_text='Type of project ("CATEGORY", "PROJECT")')

    #: Parent category if nested, otherwise null
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        help_text='Parent category if nested')

    #: Short project description
    description = models.CharField(
        max_length=512,
        unique=False,
        blank=True,
        null=True,
        help_text='Short project description')

    #: Project README (optional, supports markdown)
    readme = MarkupField(
        null=True,
        blank=True,
        markup_type='markdown',
        help_text='Project README (optional, supports markdown)')

    #: Status of project creation
    submit_status = models.CharField(
        max_length=64,
        default=SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
        help_text='Status of project creation')

    #: Project SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='Project SODAR UUID')

    # Set manager for custom queries
    objects = ProjectManager()

    class Meta:
        unique_together = ('title', 'parent')
        ordering = ['parent__title', 'title']

    def __str__(self):
        parents = self.get_parents()
        ret = ' / '.join([p.title for p in parents]) if parents else ''

        if ret:
            ret += ' / '

        ret += self.title
        return ret

    def __repr__(self):
        values = (
            self.title, self.type,
            self.parent.title if self.parent else None)
        return 'Project({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to include custom validation for Project"""
        self._validate_parent()
        self._validate_title()
        self._validate_parent_type()
        super().save(*args, **kwargs)

    def _validate_parent(self):
        """Validate parent value to ensure project can't be set as its own
        parent"""
        if self.parent == self:
            raise ValidationError('Project can not be set as its own parent')

    def _validate_parent_type(self):
        """Validate parent value to ensure parent can not be a project"""
        if (self.parent and
                self.parent.type == SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']):
            raise ValidationError(
                'Subprojects are only allowed within categories')

    def _validate_title(self):
        """Validate title against parent title to ensure they don't equal
        parent"""
        if self.parent and self.title == self.parent.title:
            raise ValidationError(
                'Project and parent titles can not be equal')

    def get_absolute_url(self):
        return reverse(
            'projectroles:detail', kwargs={'project': self.sodar_uuid})

    # Custom row-level functions
    def get_children(self):
        """Return child objects for the Project sorted by title"""
        return self.children.filter(
            submit_status=SODAR_CONSTANTS['SUBMIT_STATUS_OK']).order_by('title')

    def get_depth(self):
        """Return depth of project in the project tree structure (root=0)"""
        ret = 0
        p = self

        while p.parent:
            ret += 1
            p = p.parent

        return ret

    def get_owner(self):
        """Return RoleAssignment for owner or None if not set"""
        try:
            return self.roles.get(
                role__name=SODAR_CONSTANTS['PROJECT_ROLE_OWNER'])

        except RoleAssignment.DoesNotExist:
            return None

    def get_delegate(self):
        """Return RoleAssignment for delegate or None if not set"""
        try:
            return self.roles.get(
                role__name=SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE'])

        except RoleAssignment.DoesNotExist:
            return None

    def get_members(self):
        """Return RoleAssignments for members of project excluding owner and
        delegate"""
        return self.roles.filter(
            ~Q(role__name=SODAR_CONSTANTS['PROJECT_ROLE_OWNER']) &
            ~Q(role__name=SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']))

    def has_role(self, user, include_children=False):
        """Return whether user has roles in Project. If include_children is
        True, return True if user has roles in ANY child project"""
        if self.roles.filter(user=user).count() > 0:
            return True

        if include_children:
            for child in self.children.all():
                if child.has_role(user, include_children=True):
                    return True

        return False

    def get_parents(self):
        """Return an array of parent projects in inheritance order"""
        if not self.parent:
            return None

        ret = []
        parent = self.parent

        while parent:
            ret.append(parent)
            parent = parent.parent

        return reversed(ret)

    def get_full_title(self):
        """Return full title of project (just an alias for __str__())"""
        return str(self)

    def is_remote(self):
        """Return True if current project has been retrieved from a remote
        SODAR site"""
        if (settings.PROJECTROLES_SITE_MODE ==
                SODAR_CONSTANTS['SITE_MODE_TARGET']):
            RemoteProject = apps.get_model('projectroles', 'RemoteProject')

            try:
                RemoteProject.objects.get(
                    project_uuid=self.sodar_uuid,
                    site__mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'])
                return True

            except RemoteProject.DoesNotExist:
                pass

        return False


# Role -------------------------------------------------------------------------


class Role(models.Model):
    """Role definition, used to assign roles to projects in RoleAssignment"""

    #: Name of role
    name = models.CharField(
        max_length=64,
        unique=True,
        help_text='Name of role')

    #: Role description
    description = models.TextField(
        help_text='Role description')

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Role({})'.format(repr(self.name))


# RoleAssignment ---------------------------------------------------------------


class RoleAssignmentManager(models.Manager):
    """Manager for custom table-level RoleAssignment queries"""
    def get_assignment(self, user, project):
        """Return assignment of user to project, or None if not found"""
        try:
            return super(RoleAssignmentManager, self).get_queryset().get(
                user=user, project=project)

        except RoleAssignment.DoesNotExist:
            return None


class RoleAssignment(models.Model):
    """Assignment of an user to a role in a project. One role per user is
    allowed for each project. Roles of project owner and project delegate are
    limited to one assignment per project."""

    #: Project in which role is assigned
    project = models.ForeignKey(
        Project,
        related_name='roles',
        help_text='Project in which role is assigned')

    #: User for whom role is assigned
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='roles',
        help_text='User for whom role is assigned')

    #: Role to be assigned
    role = models.ForeignKey(
        Role,
        related_name='assignments',
        help_text='Role to be assigned')

    #: RoleAssignment SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='RoleAssignment SODAR UUID')

    # Set manager for custom queries
    objects = RoleAssignmentManager()

    class Meta:
        ordering = [
            'project__parent__title',
            'project__title',
            'role__name',
            'user__username']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['user'])]

    def __str__(self):
        return '{}: {}: {}'.format(self.project, self.role, self.user)

    def __repr__(self):
        values = (self.project.title, self.user.username, self.role.name)
        return 'RoleAssignment({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to include custom validation for RoleAssignment"""
        self._validate_user()
        self._validate_owner()
        self._validate_delegate()
        self._validate_category()
        super().save(*args, **kwargs)

    def _validate_user(self):
        """Validate fields to ensure user has only one role set for the
        project"""
        assignment = RoleAssignment.objects.get_assignment(
            self.user, self.project)

        if assignment and (not self.pk or assignment.pk != self.pk):
            raise ValidationError(
                'Role {} already set for {} in {}'.format(
                    assignment.role, assignment.user, assignment.project))

    def _validate_owner(self):
        """Validate role to ensure no more than one project owner is assigned
        to a project"""
        if self.role.name == SODAR_CONSTANTS['PROJECT_ROLE_OWNER']:
            owner = self.project.get_owner()

            if owner and (not self.pk or owner.pk != self.pk):
                raise ValidationError(
                    'User {} already set as owner of {}'.format(
                        owner, self.project))

    def _validate_delegate(self):
        """Validate role to ensure no more than one project delegate is
        assigned to a project"""
        if self.role.name == SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']:
            delegate = self.project.get_delegate()

            if delegate and (not self.pk or delegate.pk != self.pk):
                raise ValidationError(
                    '{} already set as delegate of {}'.format(
                        delegate.user, self.project))

    def _validate_category(self):
        """Validate project and role types to ensure roles other than project
        owner are not set for category-type projects"""
        if (self.project.type == SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'] and
                self.role.name != SODAR_CONSTANTS['PROJECT_ROLE_OWNER']):
            raise ValidationError(
                'Only the role of project owner is allowed for categories')


# ProjectSetting ---------------------------------------------------------------


class ProjectSettingManager(models.Manager):
    """Manager for custom table-level ProjectSetting queries"""
    def get_setting_value(self, project, app_name, setting_name):
        """
        Return value of setting_name for app_name in project
        :param project: Project object or pk
        :param app_name: App plugin name (string)
        :param setting_name: Name of setting (string)
        :return: Value (string)
        :raise: ProjectSetting.DoesNotExist if setting is not found
        """
        setting = super(ProjectSettingManager, self).get_queryset().get(
            app_plugin__name=app_name, project=project, name=setting_name)
        return setting.get_value()


class ProjectSetting(models.Model):
    """Project settings variable. These are generated based on the
    'project_settings' definition in app plugins (plugins.py)"""

    #: App to which the setting belongs
    app_plugin = models.ForeignKey(
        Plugin,
        null=False,
        unique=False,
        related_name='settings',
        help_text='App to which the setting belongs')

    #: Project to which the setting belongs
    project = models.ForeignKey(
        Project,
        null=False,
        related_name='settings',
        help_text='Project to which the setting belongs')

    #: Name of the setting
    name = models.CharField(
        max_length=255,
        unique=False,
        help_text='Name of the setting')

    #: Type of the setting
    type = models.CharField(
        max_length=64,
        unique=False,
        choices=PROJECT_SETTING_TYPE_CHOICES,
        help_text='Type of the setting')

    #: Value of the setting
    value = models.CharField(
        max_length=PROJECT_SETTING_VAL_MAXLENGTH,
        unique=False,
        null=True,
        blank=True,
        help_text='Value of the setting')

    #: ProjectSetting SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='ProjectSetting SODAR UUID')

    # Set manager for custom queries
    objects = ProjectSettingManager()

    class Meta:
        ordering = [
            'project__title',
            'app_plugin__name',
            'name']
        unique_together = ('project', 'app_plugin', 'name')

    def __str__(self):
        return '{}: {} / {}'.format(
            self.project.title, self.app_plugin.name, self.name)

    def __repr__(self):
        values = (self.project.title, self.app_plugin.name, self.name)
        return 'ProjectSetting({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to convert 'value' data according to 'type'"""
        if self.type == 'BOOLEAN':
            self.value = str(int(self.value))

        elif self.type == 'INTEGER':
            self.value = str(self.value)

        super().save(*args, **kwargs)

    # Custom row-level functions

    def get_value(self):
        """Return value of the setting in the format specified in 'type'"""
        if self.type == 'INTEGER':
            return int(self.value)

        elif self.type == 'BOOLEAN':
            return bool(int(self.value))

        return self.value


# ProjectInvite ----------------------------------------------------------------


class ProjectInvite(models.Model):
    """Invite which is sent to a non-logged in user, determining their role in
    the project."""

    #: Email address of the person to be invited
    email = models.EmailField(
        unique=False,
        null=False,
        blank=False,
        help_text='Email address of the person to be invited')

    #: Project to which the person is invited
    project = models.ForeignKey(
        Project,
        null=False,
        related_name='invites',
        help_text='Project to which the person is invited')

    #: Role assigned to the person
    role = models.ForeignKey(
        Role,
        null=False,
        help_text='Role assigned to the person')

    #: User who issued the invite
    issuer = models.ForeignKey(
        AUTH_USER_MODEL,
        null=False,
        related_name='issued_invites',
        help_text='User who issued the invite')

    #: DateTime of invite creation
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text='DateTime of invite creation')

    #: Expiration of invite as DateTime
    date_expire = models.DateTimeField(
        null=False,
        help_text='Expiration of invite as DateTime')

    #: Message to be included in the invite email (optional)
    message = models.TextField(
        blank=True,
        help_text='Message to be included in the invite email (optional)')

    #: Secret token provided to user with the invite
    secret = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text='Secret token provided to user with the invite')

    #: Status of the invite (False if claimed or revoked)
    active = models.BooleanField(
        default=True,
        help_text='Status of the invite (False if claimed or revoked)')

    #: ProjectInvite SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='ProjectInvite SODAR UUID')

    class Meta:
        ordering = [
            'project__title',
            'email',
            'role__name']

    def __str__(self):
        return '{}: {} ({}){}'.format(
            self.project,
            self.email,
            self.role.name,
            ' [ACTIVE]' if self.active else '')

    def __repr__(self):
        values = (self.project.title, self.email, self.role.name, self.active)
        return 'ProjectInvite({})'.format(', '.join(repr(v) for v in values))


# ProjectUserTag ---------------------------------------------------------------


class ProjectUserTag(models.Model):
    """Tag assigned by a user to a project"""

    #: Project to which the tag is assigned
    project = models.ForeignKey(
        Project,
        null=False,
        related_name='tags',
        help_text='Project in which the tag is assigned')

    #: User for whom the tag is assigned
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        null=False,
        related_name='project_tags',
        help_text='User for whom the tag is assigned')

    #: Name of tag to be assigned
    name = models.CharField(
        max_length=64,
        unique=False,
        null=False,
        blank=False,
        default=PROJECT_TAG_STARRED,
        help_text='Name of tag to be assigned')

    #: ProjectUserTag SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='ProjectUserTag SODAR UUID')

    class Meta:
        ordering = [
            'project__title',
            'user__username',
            'name']

    def __str__(self):
        return '{}: {}: {}'.format(
            self.project.title, self.user.username, self.name)

    def __repr__(self):
        values = (self.project.title, self.user.username, self.name)
        return 'ProjectUserTag({})'.format(', '.join(repr(v) for v in values))


# RemoteSite--------------------------------------------------------------------


class RemoteSite(models.Model):
    """Remote SODAR site"""

    #: Site name
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Site name')

    #: Site URL
    url = models.URLField(
        max_length=2000,
        blank=False,
        null=False,
        unique=False,
        help_text='Site URL')

    #: Site mode
    mode = models.CharField(
        max_length=64,
        unique=False,
        blank=False,
        null=False,
        default=SODAR_CONSTANTS['SITE_MODE_TARGET'],
        help_text='Site mode')

    #: Site description
    description = models.TextField(
        help_text='Site description')

    #: Secret token used to connect to the master site
    secret = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        help_text='Secret token for connecting to the source site')

    #: RemoteSite relation UUID (local)
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='RemoteSite relation UUID (local)')

    class Meta:
        ordering = ['name']
        unique_together = ['url', 'mode', 'secret']

    def __str__(self):
        return '{} ({})'.format(
            self.name, self.mode, self.name)

    def __repr__(self):
        values = (self.name, self.mode, self.url)
        return 'RemoteSite({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to include custom validation"""
        self._validate_mode()
        super().save(*args, **kwargs)

    def _validate_mode(self):
        """Validate mode value"""
        if self.mode not in SODAR_CONSTANTS['SITE_MODES']:
            raise ValidationError(
                'Mode "{}" not found in SITE_MODES'.format(self.mode))

    # Custom row-level functions

    def get_access_date(self):
        """Return date of latest project access by remote site"""
        projects = RemoteProject.objects.filter(
            site=self).order_by('-date_access')

        if projects.count() > 0:
            return projects.first().date_access


# RemoteProject ----------------------------------------------------------------


class RemoteProject(models.Model):
    """Remote project relation"""

    #: Related project UUID
    project_uuid = models.UUIDField(
        default=None,
        unique=False,
        help_text='Project UUID')

    #: Related project object (if created locally)
    project = models.ForeignKey(
        Project,
        related_name='remotes',
        blank=True,
        null=True,
        help_text='Related project object (if created locally)')

    #: Related remote SODAR site
    site = models.ForeignKey(
        RemoteSite,
        null=False,
        related_name='projects',
        help_text='Remote SODAR site')

    #: Project access level
    level = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        default=SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
        help_text='Project access level')

    #: DateTime of last access from/to remote site
    date_access = models.DateTimeField(
        null=True,
        auto_now_add=False,
        help_text='DateTime of last access from/to remote site')

    #: RemoteProject relation UUID (local)
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='RemoteProject relation UUID (local)')

    class Meta:
        ordering = [
            'site__name', 'project_uuid']

    def __str__(self):
        return '{}: {} ({})'.format(
            self.site.name, str(self.project_uuid), self.site.mode)

    def __repr__(self):
        values = (self.site.name, str(self.project_uuid), self.site.mode)
        return 'RemoteProject({})'.format(', '.join(repr(v) for v in values))

    # Custom row-level functions

    def get_project(self):
        """Get the related Project object"""
        try:
            return Project.objects.get(sodar_uuid=self.project_uuid)

        except Project.DoesNotExist:
            return None


# Abstract User Model ----------------------------------------------------------


# TODO: Use/extend this in your projectroles-based project


class SODARUser(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_('Name of User'), blank=True, max_length=255)

    #: User SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='User SODAR UUID')

    class Meta:
        abstract = True

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return full name or username if not set"""

        if hasattr(self, 'name') and self.name:
            return self.name

        elif self.first_name and self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)

        return self.username


# User signals -----------------------------------------------------------------


def handle_ldap_login(sender, user, **kwargs):
    """Handle LDAP logins here as needed"""

    if hasattr(user, 'ldap_username'):

        # Make domain in username uppercase
        if (user.username.find('@') != -1 and
                user.username.split('@')[1].islower()):
            u_split = user.username.split('@')
            user.username = u_split[0] + '@' + u_split[1].upper()
            user.save()

        # Save user name from first_name and last_name into name
        if user.name in ['', None]:
            if user.first_name != '':
                user.name = user.first_name + (
                    ' ' + user.last_name if user.last_name != '' else '')

                user.save()


def assign_user_group(sender, user, **kwargs):
    """Assign user to group if not yet set"""
    set_user_group(user)


user_logged_in.connect(handle_ldap_login)
user_logged_in.connect(assign_user_group)
