"""UI tests for the timeline app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.tests.test_ui import TestUIBase

from .test_models import ProjectEventMixin, ProjectEventStatusMixin


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestListView(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Tests for the timeline list view UI"""

    def setUp(self):
        super().setUp()

        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_event_visibility(self):
        """Test visibility of events in the timeline event list"""
        expected = [
            (self.superuser, 2),
            (self.as_owner.user, 2),
            (self.as_delegate.user, 2),
            (self.as_contributor.user, 1),
            (self.as_guest.user, 1),
        ]

        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_object_event_visibility(self):
        """Test visibility of object related events events in the timeline event list"""

        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )

        self.classified_ref_obj = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )

        expected = [
            (self.superuser, 2),
            (self.as_owner.user, 2),
            (self.as_delegate.user, 2),
            (self.as_contributor.user, 1),
            (self.as_guest.user, 1),
        ]

        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_event_visibility_details(self):
        """Test visibility of events on the project details page"""
        expected = [
            (self.superuser, 1),
            (self.as_owner.user, 1),
            (self.as_delegate.user, 1),
            (self.as_contributor.user, 1),
            (self.as_guest.user, 1),
        ]

        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')
