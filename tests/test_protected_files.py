import hashlib
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from assignments.models import CourseAssignment
from audit.models import AuditLog
from courses.forms import LessonForm
from courses.models import Course, Lesson
from tests.utils import create_user


class ProtectedFileStorageTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.temp_media.name,
            PROTECTED_FILE_MAX_SIZE=20 * 1024 * 1024,
        )
        self.settings_override.enable()

        self.employee = create_user(
            'material_employee',
            role=Profile.Role.EMPLOYEE,
        )
        self.unassigned_employee = create_user(
            'material_unassigned',
            role=Profile.Role.EMPLOYEE,
        )
        self.security_officer = create_user(
            'material_security',
            role=Profile.Role.SECURITY_OFFICER,
        )
        self.admin = create_user(
            'material_admin',
            role=Profile.Role.ADMIN,
        )
        self.course = Course.objects.create(
            title='Защищённые материалы',
            description='Курс с закрытыми файлами',
            author=self.security_officer,
            is_published=True,
        )
        CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=timezone.localdate() + timedelta(days=7),
        )

    def tearDown(self):
        self.settings_override.disable()
        self.temp_media.cleanup()

    @staticmethod
    def pdf_upload(name='Политика ИБ.pdf', content=None):
        payload = content or b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n'
        return SimpleUploadedFile(
            name,
            payload,
            content_type='application/pdf',
        )

    @staticmethod
    def consume_download_response(response):
        """Считывает FileResponse и освобождает файловый дескриптор."""

        try:
            return b''.join(response.streaming_content)
        finally:
            file_to_stream = getattr(response, 'file_to_stream', None)
            if file_to_stream is not None and not file_to_stream.closed:
                file_to_stream.close()

    def create_file_lesson(self):
        upload = self.pdf_upload()
        form = LessonForm(
            data={
                'title': 'Политика ИБ',
                'content': '',
                'type': 'file',
                'order': 1,
            },
            files={'file': upload},
        )
        self.assertTrue(form.is_valid(), form.errors)
        lesson = form.save(commit=False)
        lesson.course = self.course
        lesson.file_uploaded_by = self.security_officer
        lesson.save()
        return lesson

    def test_valid_file_is_stored_under_random_name_with_metadata(self):
        lesson = self.create_file_lesson()

        self.assertEqual(lesson.original_filename, 'Политика ИБ.pdf')
        self.assertEqual(lesson.file_content_type, 'application/pdf')
        self.assertEqual(lesson.file_uploaded_by, self.security_officer)
        self.assertIsNotNone(lesson.file_uploaded_at)
        self.assertTrue(lesson.file_active)
        self.assertTrue(lesson.file.name.startswith('protected/lessons/'))
        self.assertNotIn('Политика ИБ', lesson.file.name)

        with lesson.file.open('rb') as source:
            payload = source.read()
        self.assertEqual(lesson.file_size, len(payload))
        self.assertEqual(lesson.file_sha256, hashlib.sha256(payload).hexdigest())

    def test_executable_extension_is_rejected(self):
        form = LessonForm(
            data={
                'title': 'Опасный файл',
                'content': '',
                'type': 'file',
                'order': 1,
            },
            files={
                'file': SimpleUploadedFile(
                    'payload.exe',
                    b'MZ' + b'\x00' * 32,
                    content_type='application/octet-stream',
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_extension_and_actual_content_mismatch_is_rejected(self):
        form = LessonForm(
            data={
                'title': 'Подменённый PDF',
                'content': '',
                'type': 'file',
                'order': 1,
            },
            files={
                'file': SimpleUploadedFile(
                    'document.pdf',
                    b'MZ' + b'\x00' * 32,
                    content_type='application/pdf',
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    @override_settings(PROTECTED_FILE_MAX_SIZE=10)
    def test_oversized_file_is_rejected(self):
        form = LessonForm(
            data={
                'title': 'Большой PDF',
                'content': '',
                'type': 'file',
                'order': 1,
            },
            files={'file': self.pdf_upload(content=b'%PDF-' + b'a' * 100)},
        )

        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_file_lesson_requires_uploaded_file(self):
        form = LessonForm(
            data={
                'title': 'Пустой урок',
                'content': '',
                'type': 'file',
                'order': 1,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_assigned_employee_can_download_file(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['Content-Security-Policy'], 'sandbox')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(
            self.consume_download_response(response),
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n',
        )
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.employee,
                action='material_downloaded',
                object_id=str(lesson.pk),
            ).exists()
        )

    def test_unassigned_employee_is_forbidden(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.unassigned_employee)

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.unassigned_employee,
                action='material_download_denied',
                object_id=str(lesson.pk),
            ).exists()
        )

    def test_security_officer_can_download_without_assignment(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.security_officer)

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.consume_download_response(response)

    def test_admin_can_download_without_assignment(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.consume_download_response(response)

    def test_inactive_file_returns_not_found(self):
        lesson = self.create_file_lesson()
        lesson.file_active = False
        lesson.save(update_fields=['file_active'])
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        lesson = self.create_file_lesson()

        response = self.client.get(
            reverse('courses:lesson_download', args=[lesson.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_direct_media_url_is_not_available(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.employee)

        response = self.client.get(f'/media/{lesson.file.name}')

        self.assertEqual(response.status_code, 404)

    def test_course_page_uses_protected_download_route(self):
        lesson = self.create_file_lesson()
        self.client.force_login(self.employee)

        response = self.client.get(reverse('courses:detail', args=[self.course.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('courses:lesson_download', args=[lesson.pk]),
        )
        self.assertNotContains(response, f'/media/{lesson.file.name}')
