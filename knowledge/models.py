from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ArticleCategory(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    slug = models.SlugField("Адрес", max_length=140, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "Категория статьи"
        verbose_name_plural = "Категории статей"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    category = models.ForeignKey(
        ArticleCategory,
        verbose_name="Категория",
        related_name="articles",
        on_delete=models.PROTECT,
    )
    title = models.CharField("Название", max_length=220)
    slug = models.SlugField("Адрес", max_length=240, unique=True, blank=True)
    summary = models.TextField("Краткое описание", max_length=500)
    content = models.TextField("Текст статьи")
    cover_image = models.ImageField(
        "Обложка", upload_to="knowledge/covers/%Y/%m/", blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор",
        related_name="knowledge_articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reading_minutes = models.PositiveSmallIntegerField("Время чтения, минут", default=5)
    is_published = models.BooleanField("Опубликована", default=False)
    published_at = models.DateTimeField("Дата публикации", null=True, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "statya"
            slug = base
            index = 2
            while Article.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{index}"
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("knowledge:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class ArticleImage(models.Model):
    article = models.ForeignKey(
        Article, verbose_name="Статья", related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField("Изображение", upload_to="knowledge/articles/%Y/%m/")
    caption = models.CharField("Подпись", max_length=240, blank=True)
    alternative_text = models.CharField("Альтернативный текст", max_length=240, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "Изображение статьи"
        verbose_name_plural = "Изображения статьи"

    def __str__(self):
        return self.caption or Path(self.image.name).name


class ArticleAttachment(models.Model):
    article = models.ForeignKey(
        Article, verbose_name="Статья", related_name="attachments", on_delete=models.CASCADE
    )
    title = models.CharField("Название", max_length=220)
    file = models.FileField(
        "Файл",
        upload_to="knowledge/attachments/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=("pdf", "docx", "xlsx", "zip", "txt")
            )
        ],
    )
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        ordering = ("title",)
        verbose_name = "Вложение статьи"
        verbose_name_plural = "Вложения статьи"

    @property
    def extension(self):
        return Path(self.file.name).suffix.lower().lstrip(".")

    @property
    def size_label(self):
        try:
            size = self.file.size
        except (FileNotFoundError, OSError):
            return ""
        if size < 1024:
            return f"{size} Б"
        if size < 1024 * 1024:
            return f"{size / 1024:.0f} КБ"
        return f"{size / (1024 * 1024):.1f} МБ"

    def __str__(self):
        return self.title
