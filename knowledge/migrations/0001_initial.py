import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="ArticleCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Название")),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True, verbose_name="Адрес")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
            ],
            options={"verbose_name": "Категория статьи", "verbose_name_plural": "Категории статей", "ordering": ("order", "name")},
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220, verbose_name="Название")),
                ("slug", models.SlugField(blank=True, max_length=240, unique=True, verbose_name="Адрес")),
                ("summary", models.TextField(max_length=500, verbose_name="Краткое описание")),
                ("content", models.TextField(verbose_name="Текст статьи")),
                ("cover_image", models.ImageField(blank=True, upload_to="knowledge/covers/%Y/%m/", verbose_name="Обложка")),
                ("reading_minutes", models.PositiveSmallIntegerField(default=5, verbose_name="Время чтения, минут")),
                ("is_published", models.BooleanField(default=False, verbose_name="Опубликована")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата публикации")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлена")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="knowledge_articles", to=settings.AUTH_USER_MODEL, verbose_name="Автор")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="articles", to="knowledge.articlecategory", verbose_name="Категория")),
            ],
            options={"verbose_name": "Статья", "verbose_name_plural": "Статьи", "ordering": ("-published_at", "-created_at")},
        ),
        migrations.CreateModel(
            name="ArticleImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="knowledge/articles/%Y/%m/", verbose_name="Изображение")),
                ("caption", models.CharField(blank=True, max_length=240, verbose_name="Подпись")),
                ("alternative_text", models.CharField(blank=True, max_length=240, verbose_name="Альтернативный текст")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="knowledge.article", verbose_name="Статья")),
            ],
            options={"verbose_name": "Изображение статьи", "verbose_name_plural": "Изображения статьи", "ordering": ("order", "id")},
        ),
        migrations.CreateModel(
            name="ArticleAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220, verbose_name="Название")),
                ("file", models.FileField(upload_to="knowledge/attachments/%Y/%m/", validators=[django.core.validators.FileExtensionValidator(allowed_extensions=("pdf", "docx", "xlsx", "zip", "txt"))], verbose_name="Файл")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")),
                ("article", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="knowledge.article", verbose_name="Статья")),
            ],
            options={"verbose_name": "Вложение статьи", "verbose_name_plural": "Вложения статьи", "ordering": ("title",)},
        ),
    ]
