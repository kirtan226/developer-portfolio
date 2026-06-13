from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .models import ContactSubmission, NotificationSetting, UserSiteVisit
from .utils import send_contact_notifications, send_site_visit_notifications


class SiteVisitDurationApiTests(TestCase):
    def setUp(self):
        self.site_visit = UserSiteVisit.objects.create(
            ip_address='203.0.113.10',
            browser_name='Chrome',
            last_visited_at=timezone.now(),
        )

    @override_settings(TRACK_SITE_VISIT_DURATION=True)
    def test_updates_duration_when_enabled(self):
        response = self.client.post(reverse('site_visit_duration_api'), {
            'site_visit_id': self.site_visit.id,
            'duration_seconds': 15,
        })

        self.site_visit.refresh_from_db()
        self.assertJSONEqual(response.content, {'ok': True})
        self.assertEqual(self.site_visit.total_duration_seconds, 15)

    @override_settings(TRACK_SITE_VISIT_DURATION=False)
    def test_does_not_update_duration_when_disabled(self):
        response = self.client.post(reverse('site_visit_duration_api'), {
            'site_visit_id': self.site_visit.id,
            'duration_seconds': 15,
        })

        self.site_visit.refresh_from_db()
        self.assertJSONEqual(response.content, {
            'ok': False,
            'tracking_enabled': False,
        })
        self.assertEqual(self.site_visit.total_duration_seconds, 0)


class TelegramAlertFlagTests(TestCase):
    def setUp(self):
        self.contact_submission = ContactSubmission.objects.create(
            name='Visitor',
            email='visitor@example.com',
            message='Hello',
        )
        self.site_visit = UserSiteVisit.objects.create(
            ip_address='203.0.113.10',
            browser_name='Chrome',
            last_visited_at=timezone.now(),
        )

    @override_settings(SEND_TELEGRAM_ALERTS=False)
    @patch('core.utils.send_contact_confirmation_email', return_value=False)
    @patch('core.utils.send_contact_telegram_notification')
    def test_contact_telegram_requires_global_flag(
        self,
        send_telegram_mock,
        _send_confirmation_mock,
    ):
        NotificationSetting.objects.create(
            notification_type=NotificationSetting.NotificationType.CONTACT_US,
            telegram_notification=True,
        )

        result = send_contact_notifications(self.contact_submission, profile=None)

        send_telegram_mock.assert_not_called()
        self.assertFalse(result['telegram_enabled'])

    @override_settings(SEND_TELEGRAM_ALERTS=False)
    @patch('core.utils.send_telegram_notification')
    def test_site_visit_telegram_requires_global_flag(self, send_telegram_mock):
        NotificationSetting.objects.create(
            notification_type=NotificationSetting.NotificationType.SITE_VISIT,
            telegram_notification=True,
        )

        result = send_site_visit_notifications(self.site_visit, profile=None, is_new_visit=True)

        send_telegram_mock.assert_not_called()
        self.assertFalse(result['telegram_sent'])


class SiteVisitNotifyApiTests(TestCase):
    def setUp(self):
        self.site_visit = UserSiteVisit.objects.create(
            ip_address='203.0.113.20',
            browser_name='Firefox',
            last_visited_at=timezone.now(),
        )

    @patch('core.views.send_site_visit_notifications')
    def test_sends_notification_for_active_visit(self, send_notifications_mock):
        send_notifications_mock.return_value = {
            'email_sent': False,
            'telegram_sent': True,
        }

        response = self.client.post(reverse('site_visit_notify_api'), {
            'site_visit_id': self.site_visit.id,
            'is_new_visit': 'true',
        })

        self.assertJSONEqual(response.content, {
            'ok': True,
            'email_sent': False,
            'telegram_sent': True,
        })
        send_notifications_mock.assert_called_once()

    @patch('core.views.send_site_visit_notifications')
    def test_does_not_send_notification_for_inactive_visit(self, send_notifications_mock):
        self.site_visit.is_active = False
        self.site_visit.save(update_fields=['is_active'])

        response = self.client.post(reverse('site_visit_notify_api'), {
            'site_visit_id': self.site_visit.id,
            'is_new_visit': 'true',
        })

        self.assertJSONEqual(response.content, {'ok': False})
        send_notifications_mock.assert_not_called()
