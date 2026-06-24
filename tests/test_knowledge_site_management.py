from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from accounts.permissions import Permission, has_permission
from knowledge.models import Article, ArticleAttachment, ArticleCategory, ArticleImage


User = get_user_model()


class KnowledgeSiteManagementTests(TestCase):
    def make_user(self, username, role):
        user = User.objects.create_user(username=username, password="StrongPass123!")
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save(update_fields=("role",))
        return user

    def setUp(self):
        self.employee = self.make_user("knowledge_employee", Profile.Role.EMPLOYEE)
        self.security_officer = self.make_user(
            "knowledge_security", Profile.Role.SECURITY_OFFICER
        )
        self.admin_user = self.make_user("knowledge_admin", Profile.Role.ADMIN)
        self.category = ArticleCategory.objects.create(name="Пароли", order=1)

    def test_permission_is_granted_only_to_management_roles(self):
        self.assertFalse(
            has_permission(self.employee, Permission.MANAGE_KNOWLEDGE)
        )
        self.assertTrue(
            has_permission(self.security_officer, Permission.MANAGE_KNOWLEDGE)
        )
        self.assertTrue(
            has_permission(self.admin_user, Permission.MANAGE_KNOWLEDGE)
        )

    def test_employee_cannot_open_article_management(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("knowledge:manage"))
        self.assertEqual(response.status_code, 403)

    def test_security_officer_can_create_draft_on_site(self):
        self.client.force_login(self.security_officer)
        response = self.client.post(
            reverse("knowledge:create"),
            {
                "category": self.category.pk,
                "title": "Как создавать надёжные пароли",
                "slug": "",
                "summary": "Практическая памятка для сотрудников.",
                "content": "Используйте уникальные длинные пароли.",
                "reading_minutes": 4,
                "is_published": "",
                "images-TOTAL_FORMS": "2",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "1000",
                "attachments-TOTAL_FORMS": "2",
                "attachments-INITIAL_FORMS": "0",
                "attachments-MIN_NUM_FORMS": "0",
                "attachments-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertRedirects(response, reverse("knowledge:manage"))
        article = Article.objects.get(title="Как создавать надёжные пароли")
        self.assertEqual(article.author, self.security_officer)
        self.assertFalse(article.is_published)
        self.assertIsNone(article.published_at)

    def test_security_officer_can_publish_article(self):
        article = Article.objects.create(
            category=self.category,
            title="Фишинг",
            summary="Как распознать сообщение злоумышленника.",
            content="Проверяйте адрес отправителя.",
            author=self.security_officer,
            is_published=False,
        )
        self.client.force_login(self.security_officer)
        response = self.client.post(reverse("knowledge:publish", args=(article.pk,)))
        self.assertRedirects(response, reverse("knowledge:manage"))
        article.refresh_from_db()
        self.assertTrue(article.is_published)
        self.assertIsNotNone(article.published_at)

    def test_article_list_links_to_site_management_not_django_admin(self):
        self.client.force_login(self.security_officer)
        response = self.client.get(reverse("knowledge:list"))
        self.assertContains(response, reverse("knowledge:manage"))
        self.assertNotContains(response, "admin:knowledge_article_add")
        self.assertNotContains(response, "/admin/knowledge/article/add/")

    def test_knowledge_models_are_not_registered_in_django_admin(self):
        for model in (Article, ArticleCategory, ArticleImage, ArticleAttachment):
            self.assertFalse(admin.site.is_registered(model))

    def test_employee_does_not_see_management_button(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("knowledge:list"))
        self.assertNotContains(response, "Управление статьями")

    def test_security_officer_can_manage_categories(self):
        self.client.force_login(self.security_officer)
        response = self.client.post(
            reverse("knowledge:category_create"),
            {
                "name": "Фишинг",
                "slug": "",
                "description": "Материалы по противодействию фишингу.",
                "order": 2,
            },
        )
        self.assertRedirects(response, reverse("knowledge:manage_categories"))
        self.assertTrue(ArticleCategory.objects.filter(name="Фишинг").exists())
