from django.db import migrations, models


def remove_unsupported_source_logs(apps, schema_editor):
    IntegrationSyncLog = apps.get_model('integrations', 'IntegrationSyncLog')
    IntegrationSyncLog.objects.filter(
        source__in=('ldap', 'active_directory')
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_unsupported_source_logs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='integrationsynclog',
            name='source',
            field=models.CharField(choices=[('csv', 'CSV')], max_length=32),
        ),
        migrations.AlterField(
            model_name='integrationsynclog',
            name='status',
            field=models.CharField(
                choices=[
                    ('started', 'Запущено'),
                    ('success', 'Успешно'),
                    ('failed', 'Ошибка'),
                ],
                max_length=32,
            ),
        ),
    ]
