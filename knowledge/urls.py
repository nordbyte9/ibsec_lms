from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.article_list, name="list"),
    path("manage/", views.manage_articles, name="manage"),
    path("manage/create/", views.article_create, name="create"),
    path("manage/<int:pk>/edit/", views.article_edit, name="edit"),
    path("manage/<int:pk>/preview/", views.article_preview, name="preview"),
    path("manage/<int:pk>/publish/", views.article_publish, name="publish"),
    path("manage/<int:pk>/unpublish/", views.article_unpublish, name="unpublish"),
    path("manage/<int:pk>/delete/", views.article_delete, name="delete"),
    path("manage/categories/", views.manage_categories, name="manage_categories"),
    path("manage/categories/create/", views.category_create, name="category_create"),
    path("manage/categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("manage/categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("files/<int:pk>/", views.attachment_download, name="attachment_download"),
    path("<str:slug>/", views.article_detail, name="detail"),
]
