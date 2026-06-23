import hashlib
import mimetypes
from pathlib import Path

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import courses.file_security
import courses.models


def populate_existing_file_metadata(apps, schema_editor):
    Lesson = apps.get_model('courses', 'Lesson')

    for lesson in Lesson.objects.exclude(file='').iterator():
        changed_fields = []
        original_name = Path(lesson.file.name).name

        if not lesson.original_filename:
            lesson.original_filename = original_name[:255]
            changed_fields.append('original_filename')

        if not lesson.file_content_type:
            lesson.file_content_type = (
                mimetypes.guess_type(original_name)[0] or 'application/octet-stream'
            )[:127]
            changed_fields.append('file_content_type')

        try:
            with lesson.file.open('rb') as source:
                digest = hashlib.sha256()
                size = 0
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
        except (FileNotFoundError, OSError):
            size = None
            digest = None

        if lesson.file_size is None and size is not None:
            lesson.file_size = size
            changed_fields.append('file_size')

        if not lesson.file_sha256 and digest is not None:
            lesson.file_sha256 = digest.hexdigest()
            changed_fields.append('file_sha256')

        if changed_fields:
            lesson.save(update_fields=changed_fields)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0002_securitycategory_course_is_mandatory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='file_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='file_content_type',
            field=models.CharField(blank=True, max_length=127),
        ),
        migrations.AddField(
            model_name='lesson',
            name='file_sha256',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name='lesson',
            name='file_size',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='file_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='file_uploaded_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='uploaded_lesson_files',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='lesson',
            name='original_filename',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=courses.models.protected_lesson_upload_to,
                validators=[courses.file_security.validate_protected_upload],
            ),
        ),
        migrations.RunPython(
            populate_existing_file_metadata,
            migrations.RunPython.noop,
        ),
    ]
