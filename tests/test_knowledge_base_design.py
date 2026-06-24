from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from knowledge.models import Article, ArticleCategory


class KnowledgeBaseDesignTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reader", password="StrongPass123!"
        )
        self.category = ArticleCategory.objects.create(name="Фишинг")
        self.article = Article.objects.create(
            category=self.category,
            title="Как распознать фишинг",
            summary="Краткое описание статьи",
            content="Что такое фишинг?\n\nПроверяйте адрес отправителя.",
            reading_minutes=5,
            is_published=True,
            published_at=timezone.now(),
        )

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(reverse("knowledge:list"))
        self.assertEqual(response.status_code, 302)

    def test_article_list_is_in_russian(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("knowledge:list"))
        self.assertContains(response, "База знаний")
        self.assertContains(response, self.article.title)
        self.assertNotContains(response, "Knowledge base")

    def test_article_detail_uses_uploaded_content(self):
        self.client.force_login(self.user)
        response = self.client.get(self.article.get_absolute_url())
        self.assertContains(response, self.article.title)
        self.assertContains(response, "Проверяйте адрес отправителя")
        self.assertContains(response, "Содержание")

    def test_unpublished_article_is_hidden(self):
        hidden = Article.objects.create(
            category=self.category,
            title="Черновик",
            summary="Не опубликовано",
            content="Текст",
            is_published=False,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("knowledge:list"))
        self.assertNotContains(response, hidden.title)
        response = self.client.get(hidden.get_absolute_url())
        self.assertEqual(response.status_code, 404)
