"""Remote project management utilities for the projectroles app"""

import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import Group
from django.utils import timezone

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    RemoteProject,
    SODAR_CONSTANTS,
)
from projectroles.plugins import get_backend_api


User = auth.get_user_model()
logger = logging.getLogger(__name__)

APP_NAME = 'projectroles'


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW'
]
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']


class RemoteProjectAPI:
    """Remote project data handling API"""

    #: Remote data retrieved from source site
    remote_data = None

    #: Remote source site currently being worked with
    source_site = None

    #: Timeline API
    timeline = get_backend_api('timeline_backend')

    #: User for storing timeline events
    tl_user = None

    #: Default owner for projects
    default_owner = None

    #: Updated parent projects in current sync operation
    updated_parents = []

    # Internal functions -------------------------------------------------------

    @staticmethod
    def _update_obj(obj, data, fields):
        """Update object"""
        for f in [f for f in fields if hasattr(obj, f)]:
            setattr(obj, f, data[f])
        obj.save()
        return obj

    def _sync_user(self, uuid, u_data):
        """Synchronize LDAP user based on source site data"""
        # Update existing user
        try:
            user = User.objects.get(username=u_data['username'])
            updated_fields = []

            for k, v in u_data.items():
                if (
                    k not in ['groups', 'sodar_uuid']
                    and hasattr(user, k)
                    and str(getattr(user, k)) != str(v)
                ):
                    updated_fields.append(k)

            if updated_fields:
                user = self._update_obj(user, u_data, updated_fields)
                u_data['status'] = 'updated'

                logger.info(
                    'Updated user: {} ({}): {}'.format(
                        u_data['username'], uuid, ', '.join(updated_fields)
                    )
                )

            # Check and update groups
            if sorted([g.name for g in user.groups.all()]) != sorted(
                u_data['groups']
            ):
                for g in user.groups.all():
                    if g.name not in u_data['groups']:
                        g.user_set.remove(user)
                        logger.debug(
                            'Removed user {} ({}) from group "{}"'.format(
                                user.username, user.sodar_uuid, g.name
                            )
                        )

                existing_groups = [g.name for g in user.groups.all()]

                for g in u_data['groups']:
                    if g not in existing_groups:
                        group, created = Group.objects.get_or_create(name=g)
                        group.user_set.add(user)
                        logger.debug(
                            'Added user {} ({}) to group "{}"'.format(
                                user.username, user.sodar_uuid, g
                            )
                        )

        # Create new user
        except User.DoesNotExist:
            create_values = {k: v for k, v in u_data.items() if k != 'groups'}
            user = User.objects.create(**create_values)
            u_data['status'] = 'created'
            logger.info('Created user: {}'.format(user.username))

            for g in u_data['groups']:
                group, created = Group.objects.get_or_create(name=g)
                group.user_set.add(user)
                logger.debug(
                    'Added user {} ({}) to group "{}"'.format(
                        user.username, user.sodar_uuid, g
                    )
                )

    def _handle_user_error(self, error_msg, project, role_uuid):
        logger.error(error_msg)
        self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
            role_uuid
        ]['status'] = 'error'
        self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
            role_uuid
        ]['status_msg'] = error_msg

    def _handle_project_error(self, error_msg, uuid, p, action):
        """Add and log project error in remote sync"""
        logger.error(
            '{} {} "{}" ({}): {}'.format(
                action.capitalize(),
                p['type'].lower(),
                p['title'],
                uuid,
                error_msg,
            )
        )
        self.remote_data['projects'][uuid]['status'] = 'error'
        self.remote_data['projects'][uuid]['status_msg'] = error_msg

    def _update_project(self, project, p_data, parent):
        """Update an existing project during sync"""
        updated_fields = []
        uuid = str(project.sodar_uuid)

        for k, v in p_data.items():
            if (
                k not in ['parent', 'sodar_uuid', 'roles', 'readme']
                and hasattr(project, k)
                and str(getattr(project, k)) != str(v)
            ):
                updated_fields.append(k)

        # README is a special case
        if project.readme.raw != p_data['readme']:
            updated_fields.append('readme')

        if updated_fields or project.parent != parent:
            project = self._update_obj(project, p_data, updated_fields)

            # Manually update parent
            if parent != project.parent:
                project.parent = parent
                project.save()
                updated_fields.append('parent')

            self.remote_data['projects'][uuid]['status'] = 'updated'

            if self.tl_user:  # Taskflow
                tl_desc = (
                    'update project from remote site '
                    '"{{{}}}" ({})'.format('site', ', '.join(updated_fields))
                )
                # TODO: Add extra_data
                tl_event = self.timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=self.tl_user,
                    event_name='remote_project_update',
                    description=tl_desc,
                    status_type='OK',
                )
                tl_event.add_object(
                    self.source_site, 'site', self.source_site.name
                )

            logger.info(
                'Updated {}: {}'.format(
                    p_data['type'].lower(), ', '.join(sorted(updated_fields))
                )
            )

        else:
            logger.debug('Nothing to update in project details')

    def _create_project(self, uuid, p_data, parent):
        """Create a new project from source site data"""

        # Check existing title under the same parent
        try:
            old_project = Project.objects.get(
                parent=parent, title=p_data['title']
            )

            # Handle error
            error_msg = (
                '{} with the title "{}" exists under the same '
                'parent, unable to create'.format(
                    old_project.type.capitalize(), old_project.title
                )
            )
            self._handle_project_error(error_msg, uuid, p_data, 'create')
            return

        except Project.DoesNotExist:
            pass

        create_fields = ['title', 'description', 'readme']
        create_values = {k: v for k, v in p_data.items() if k in create_fields}
        create_values['type'] = p_data['type']
        create_values['parent'] = parent
        create_values['sodar_uuid'] = uuid
        project = Project.objects.create(**create_values)

        self.remote_data['projects'][uuid]['status'] = 'created'

        if self.tl_user:  # Taskflow
            tl_event = self.timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=self.tl_user,
                event_name='remote_project_create',
                description='create project from remote site {site}',
                status_type='OK',
            )
            # TODO: Add extra_data
            tl_event.add_object(self.source_site, 'site', self.source_site.name)

        logger.info('Created {}'.format(p_data['type'].lower()))

    def _update_roles(self, project, p_data):
        """Create or update project roles"""
        # TODO: Refactor this
        uuid = str(project.sodar_uuid)

        allow_local = (
            settings.PROJECTROLES_ALLOW_LOCAL_USERS
            if hasattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS')
            else False
        )

        for r_uuid, r in {k: v for k, v in p_data['roles'].items()}.items():
            # Ensure the Role exists
            try:
                role = Role.objects.get(name=r['role'])

            except Role.DoesNotExist:
                error_msg = 'Role object "{}" not found (assignment {})'.format(
                    r['role'], r_uuid
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # Ensure the user is valid
            if (
                '@' not in r['user']
                and not allow_local
                and r['role'] != PROJECT_ROLE_OWNER
            ):
                error_msg = (
                    'Local user "{}" set for role "{}" but local '
                    'users are not allowed'.format(r['user'], r['role'])
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # If local user, ensure they exist
            elif (
                '@' not in r['user']
                and allow_local
                and r['role'] != PROJECT_ROLE_OWNER
                and not User.objects.filter(username=r['user']).first()
            ):
                error_msg = (
                    'Local user "{}" not found, role of "{}" will '
                    'not be assigned'.format(r['user'], r['role'])
                )
                self._handle_user_error(error_msg, project, r_uuid)
                continue

            # Use the default owner, if owner role for a non-LDAP user and local
            # users are not allowed
            if (
                r['role'] == PROJECT_ROLE_OWNER
                and (
                    not allow_local
                    or not User.objects.filter(username=r['user']).first()
                )
                and '@' not in r['user']
            ):
                role_user = self.default_owner

                # Notify of assigning role to default owner
                status_msg = (
                    'Non-LDAP/AD user "{}" set as owner, assigning role '
                    'to user "{}"'.format(
                        r['user'], self.default_owner.username
                    )
                )
                self.remote_data['projects'][uuid]['roles'][r_uuid][
                    'user'
                ] = self.default_owner.username
                self.remote_data['projects'][uuid]['roles'][r_uuid][
                    'status_msg'
                ] = status_msg
                logger.info(status_msg)

            else:
                role_user = User.objects.get(username=r['user'])

            # Update RoleAssignment if it exists and is changed
            as_updated = False
            role_query = {'project__sodar_uuid': project.sodar_uuid}

            if r['role'] == PROJECT_ROLE_OWNER:
                role_query['role__name'] = PROJECT_ROLE_OWNER

            else:
                role_query['user'] = role_user

            old_as = RoleAssignment.objects.filter(**role_query).first()

            # Owner updating
            if old_as and r['role'] == PROJECT_ROLE_OWNER:
                # Update user or local admin user
                if ('@' in r['user'] and old_as.user != role_user) or (
                    role_user == self.default_owner
                    and project.get_owner().user != self.default_owner
                ):
                    as_updated = True

                    # Delete existing role of the new owner if it exists
                    try:
                        RoleAssignment.objects.get(
                            project__sodar_uuid=project.sodar_uuid,
                            user=role_user,
                        ).delete()
                        logger.debug(
                            'Deleted existing role from '
                            'user "{}"'.format(role_user.username)
                        )

                    except RoleAssignment.DoesNotExist:
                        logger.debug(
                            'No existing role found for user "{}"'.format(
                                role_user.username
                            )
                        )

            # Updating of other roles
            elif (
                old_as
                and r['role'] != PROJECT_ROLE_OWNER
                and old_as.role != role
            ):
                as_updated = True

            if as_updated:
                old_as.role = role
                old_as.user = role_user
                old_as.save()
                self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
                    r_uuid
                ]['status'] = 'updated'

                if self.tl_user:  # Taskflow
                    tl_desc = (
                        'update role to "{}" for {{{}}} from site '
                        '{{{}}}'.format(role.name, 'user', 'site')
                    )
                    tl_event = self.timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_update',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(role_user, 'user', role_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

                logger.info(
                    'Updated role {}: {} = {}'.format(
                        r_uuid, role_user.username, role.name
                    )
                )

            # Create a new RoleAssignment
            elif not old_as:
                role_values = {
                    'sodar_uuid': r_uuid,
                    'project': project,
                    'role': role,
                    'user': role_user,
                }
                RoleAssignment.objects.create(**role_values)

                self.remote_data['projects'][str(project.sodar_uuid)]['roles'][
                    r_uuid
                ]['status'] = 'created'

                if self.tl_user:  # Taskflow
                    tl_desc = 'add role "{}" for {{{}}} from site {{{}}}'.format(
                        role.name, 'user', 'site'
                    )
                    tl_event = self.timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_create',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(role_user, 'user', role_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

                logger.info(
                    'Created role {}: {} -> {}'.format(
                        r_uuid, role_user.username, role.name
                    )
                )

    def _remove_deleted_roles(self, project, p_data):
        """Remove roles for project deleted in source site"""
        timeline = get_backend_api('timeline_backend')
        uuid = str(project.sodar_uuid)
        current_users = [v['user'] for k, v in p_data['roles'].items()]

        deleted_roles = (
            RoleAssignment.objects.filter(project=project)
            .exclude(role__name=PROJECT_ROLE_OWNER)
            .exclude(user__username__in=current_users)
        )
        deleted_count = deleted_roles.count()

        if deleted_count > 0:
            deleted_users = sorted([r.user.username for r in deleted_roles])

            for del_as in deleted_roles:
                del_user = del_as.user
                del_role = del_as.role
                del_uuid = str(del_as.sodar_uuid)
                del_as.delete()

                self.remote_data['projects'][uuid]['roles'][del_uuid] = {
                    'user': del_user.username,
                    'role': del_role.name,
                    'status': 'deleted',
                }

                if self.tl_user:  # Taskflow
                    tl_desc = (
                        'remove role "{}" from {{{}}} by site '
                        '{{{}}}'.format(del_role.name, 'user', 'site')
                    )
                    tl_event = timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=self.tl_user,
                        event_name='remote_role_delete',
                        description=tl_desc,
                        status_type='OK',
                    )
                    tl_event.add_object(del_user, 'user', del_user.username)
                    tl_event.add_object(
                        self.source_site, 'site', self.source_site.name
                    )

            logger.info(
                'Deleted {} removed role{} for: {}'.format(
                    deleted_count,
                    's' if deleted_count != 1 else '',
                    ', '.join(deleted_users),
                )
            )

    def _sync_project(self, uuid, p_data):
        """Synchronize a project from source site. Create/update project, its
        parents and user roles"""
        # Add/update parents if not yet handled
        if (
            p_data['parent_uuid']
            and p_data['parent_uuid'] not in self.updated_parents
        ):
            c_data = self.remote_data['projects'][p_data['parent_uuid']]
            self._sync_project(p_data['parent_uuid'], c_data)
            self.updated_parents.append(p_data['parent_uuid'])

        project = Project.objects.filter(
            type=p_data['type'], sodar_uuid=uuid
        ).first()
        parent = None
        action = 'create' if not project else 'update'

        logger.info(
            'Processing {} "{}" ({})..'.format(
                p_data['type'].lower(), p_data['title'], uuid
            )
        )

        # Get parent and ensure it exists
        if p_data['parent_uuid']:
            try:
                parent = Project.objects.get(sodar_uuid=p_data['parent_uuid'])

            except Project.DoesNotExist:
                # Handle error
                error_msg = 'Parent {} not found'.format(p_data['parent_uuid'])
                self._handle_project_error(error_msg, uuid, p_data, action)
                return

        # Update project
        if project:
            self._update_project(project, p_data, parent)

        # Create new project
        else:
            self._create_project(uuid, p_data, parent)
            project = Project.objects.filter(
                type=p_data['type'], sodar_uuid=uuid
            ).first()

        # Create/update a RemoteProject object
        try:
            remote_project = RemoteProject.objects.get(
                site=self.source_site, project=project
            )
            remote_project.level = p_data['level']
            remote_project.project = project
            remote_project.date_access = timezone.now()
            remote_action = 'updated'

        except RemoteProject.DoesNotExist:
            remote_project = RemoteProject.objects.create(
                site=self.source_site,
                project_uuid=project.sodar_uuid,
                project=project,
                level=p_data['level'],
                date_access=timezone.now(),
            )
            remote_action = 'created'

        logger.debug(
            '{} RemoteProject {}'.format(
                remote_action.capitalize(), remote_project.sodar_uuid
            )
        )

        # Skip the rest if not updating roles
        if 'level' in p_data and p_data['level'] != REMOTE_LEVEL_READ_ROLES:
            return

        # Create/update roles
        # NOTE: Only update AD/LDAP user roles and local owner roles
        self._update_roles(project, p_data)

        # Remove deleted user roles
        self._remove_deleted_roles(project, p_data)

    # API functions ------------------------------------------------------------

    def get_target_data(self, target_site):
        """
        Get user and project data to be synchronized into a target site.

        :param target_site: RemoteSite object for the target site
        :return: Dict
        """
        sync_data = {'users': {}, 'projects': {}}

        def _add_user(user):
            if user.username not in [
                u['username'] for u in sync_data['users'].values()
            ]:
                sync_data['users'][str(user.sodar_uuid)] = {
                    'username': user.username,
                    'name': user.name,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'groups': [g.name for g in user.groups.all()],
                }

        def _add_parent_categories(category, project_level):
            if category.parent:
                _add_parent_categories(category.parent, project_level)

            if str(category.sodar_uuid) not in sync_data['projects'].keys():
                cat_data = {
                    'title': category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'parent_uuid': str(category.parent.sodar_uuid)
                    if category.parent
                    else None,
                    'description': category.description,
                    'readme': category.readme.raw,
                }

                if project_level == REMOTE_LEVEL_READ_ROLES:
                    cat_data['level'] = REMOTE_LEVEL_READ_ROLES
                    role_as = category.get_owner()
                    cat_data['roles'] = {}
                    cat_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name,
                    }
                    _add_user(role_as.user)

                else:
                    cat_data['level'] = REMOTE_LEVEL_READ_INFO

                sync_data['projects'][str(category.sodar_uuid)] = cat_data

        for rp in target_site.projects.all():
            project = rp.get_project()
            project_data = {
                'level': rp.level,
                'title': project.title,
                'type': PROJECT_TYPE_PROJECT,
            }

            # View available projects
            if rp.level == REMOTE_LEVEL_VIEW_AVAIL:
                project_data['available'] = True if project else False

            # Add info
            elif project and rp.level in [
                REMOTE_LEVEL_READ_INFO,
                REMOTE_LEVEL_READ_ROLES,
            ]:
                project_data['description'] = project.description
                project_data['readme'] = project.readme.raw

                # Add categories
                if project.parent:
                    _add_parent_categories(project.parent, rp.level)
                    project_data['parent_uuid'] = str(project.parent.sodar_uuid)

            # If level is READ_ROLES, add categories and roles
            if rp.level in REMOTE_LEVEL_READ_ROLES:
                project_data['roles'] = {}

                for role_as in project.roles.all():
                    project_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name,
                    }
                    _add_user(role_as.user)

            sync_data['projects'][str(rp.project_uuid)] = project_data

        return sync_data

    def sync_source_data(self, site, remote_data, request=None):
        """
        Synchronize remote user and project data into the local Django database
        and return information of additions.

        :param site: RemoteSite object for the source site
        :param remote_data: Data returned by get_target_data() in the source
        :param request: Request object (optional)
        :return: Dict with updated remote_data
        :raise: ValueError if user from PROJECTROLES_DEFAULT_ADMIN is not found
        """
        self.source_site = site
        self.remote_data = remote_data
        self.updated_parents = []

        # Get default owner if remote projects have a local owner
        try:
            self.default_owner = User.objects.get(
                username=settings.PROJECTROLES_DEFAULT_ADMIN
            )

        except User.DoesNotExist:
            error_msg = (
                'Local user "{}" defined in PROJECTROLES_DEFAULT_ADMIN '
                'not found'.format(settings.PROJECTROLES_DEFAULT_ADMIN)
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Set up timeline user
        if self.timeline:
            self.tl_user = request.user if request else self.default_owner

        logger.info('Synchronizing data from "{}"..'.format(site.name))

        # Return unchanged data if no projects with READ_ROLES are included
        if not {
            k: v
            for k, v in self.remote_data['projects'].items()
            if v['type'] == PROJECT_TYPE_PROJECT
            and v['level'] == REMOTE_LEVEL_READ_ROLES
        }.values():
            logger.info('No READ_ROLES access set, nothing to synchronize')
            return self.remote_data

        ########
        # Users
        ########
        logger.info('Synchronizing LDAP/AD users..')

        # NOTE: only sync LDAP/AD users
        for sodar_uuid, u_data in {
            k: v
            for k, v in self.remote_data['users'].items()
            if '@' in v['username']
        }.items():
            self._sync_user(sodar_uuid, u_data)

        logger.info('User sync OK')

        ##########################
        # Categories and Projects
        ##########################

        # Update projects
        logger.info('Synchronizing projects..')

        for sodar_uuid, p_data in {
            k: v
            for k, v in self.remote_data['projects'].items()
            if v['type'] == PROJECT_TYPE_PROJECT
            and v['level'] == REMOTE_LEVEL_READ_ROLES
        }.items():
            self._sync_project(sodar_uuid, p_data)

        logger.info('Synchronization OK')
        return self.remote_data
