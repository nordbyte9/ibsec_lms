from django.test import TestCase

from audit.models import AuditLog
from audit.services import log_action
from tests.utils import create_user


class AuditTests(TestCase):
    def test_log_action_creates_audit_log(self):
        user = create_user('auditor', password='password123', role='admin')
        log = log_action(user, 'test_action', 'TestObject', '123', 'Test description')

        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(log.user, user)
        self.assertEqual(log.action, 'test_action')
        self.assertEqual(log.object_type, 'TestObject')
        self.assertEqual(log.object_id, '123')
        self.assertEqual(log.description, 'Test description')
