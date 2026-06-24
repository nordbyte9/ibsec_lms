from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_department_position_alter_profile_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/avatars/%Y/%m/', verbose_name='Аватар'),
        ),
    ]
