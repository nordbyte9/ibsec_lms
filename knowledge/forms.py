from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Article, ArticleAttachment, ArticleCategory, ArticleImage


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024


class StyledFormMixin:
    """Добавляет единые классы элементам форм базы знаний."""

    def _apply_styles(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "knowledge-checkbox")
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "knowledge-file-input")
            else:
                current = widget.attrs.get("class", "")
                widget.attrs["class"] = f"knowledge-control {current}".strip()


class ArticleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            "category",
            "title",
            "slug",
            "summary",
            "content",
            "cover_image",
            "reading_minutes",
            "is_published",
        )
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "content": forms.Textarea(attrs={"rows": 18}),
            "slug": forms.TextInput(
                attrs={"placeholder": "Можно оставить пустым — адрес создастся автоматически"}
            ),
            "reading_minutes": forms.NumberInput(attrs={"min": 1, "max": 120}),
        }
        help_texts = {
            "cover_image": "Форматы JPEG, PNG и WebP; размер — до 8 МБ.",
            "is_published": "Опубликованная статья сразу становится доступна сотрудникам.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()
        self.fields["category"].empty_label = "Выберите категорию"
        self.fields["slug"].required = False

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if not image:
            return image
        extension = Path(image.name).suffix.lower()
        if extension not in IMAGE_EXTENSIONS:
            raise ValidationError("Допустимы изображения JPEG, PNG и WebP.")
        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError("Размер обложки не должен превышать 8 МБ.")
        return image


class ArticleCategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ArticleCategory
        fields = ("name", "slug", "description", "order")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "slug": forms.TextInput(
                attrs={"placeholder": "Можно оставить пустым — адрес создастся автоматически"}
            ),
            "order": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()
        self.fields["slug"].required = False


class ArticleImageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ArticleImage
        fields = ("image", "caption", "alternative_text", "order")
        widgets = {"order": forms.NumberInput(attrs={"min": 0})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def has_changed(self):
        """Не считает пустую дополнительную строку изменённой.

        У новой строки поле ``order`` получает модельное значение по умолчанию 0.
        Если браузер или тест не отправил это поле, стандартный ModelForm может
        посчитать строку изменённой и потребовать обязательное изображение.
        """
        if self.is_bound and not self.instance.pk:
            image_name = self.add_prefix("image")
            caption_name = self.add_prefix("caption")
            alternative_text_name = self.add_prefix("alternative_text")
            has_file = bool(self.files.get(image_name))
            has_text = any(
                str(self.data.get(name, "")).strip()
                for name in (caption_name, alternative_text_name)
            )
            if not has_file and not has_text:
                return False
        return super().has_changed()

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            return image
        extension = Path(image.name).suffix.lower()
        if extension not in IMAGE_EXTENSIONS:
            raise ValidationError("Допустимы изображения JPEG, PNG и WebP.")
        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError("Размер изображения не должен превышать 8 МБ.")
        return image


class ArticleAttachmentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ArticleAttachment
        fields = ("title", "file")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def has_changed(self):
        """Полностью пустая строка вложения не должна блокировать сохранение."""
        if self.is_bound and not self.instance.pk:
            title_name = self.add_prefix("title")
            file_name = self.add_prefix("file")
            has_title = bool(str(self.data.get(title_name, "")).strip())
            has_file = bool(self.files.get(file_name))
            if not has_title and not has_file:
                return False
        return super().has_changed()

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded and uploaded.size > MAX_ATTACHMENT_SIZE:
            raise ValidationError("Размер вложения не должен превышать 20 МБ.")
        return uploaded


ArticleImageFormSet = inlineformset_factory(
    Article,
    ArticleImage,
    form=ArticleImageForm,
    extra=2,
    can_delete=True,
)

ArticleAttachmentFormSet = inlineformset_factory(
    Article,
    ArticleAttachment,
    form=ArticleAttachmentForm,
    extra=2,
    can_delete=True,
)
