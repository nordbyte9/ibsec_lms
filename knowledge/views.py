from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import Permission, has_permission

from .forms import (
    ArticleAttachmentFormSet,
    ArticleCategoryForm,
    ArticleForm,
    ArticleImageFormSet,
)
from .models import Article, ArticleAttachment, ArticleCategory


def knowledge_manager_required(view_func):
    """Разрешает управление базой знаний только уполномоченным ролям."""

    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not has_permission(request.user, Permission.MANAGE_KNOWLEDGE):
            raise PermissionDenied("Недостаточно прав для управления базой знаний.")
        return view_func(request, *args, **kwargs)

    return wrapped


def _can_manage(user):
    return has_permission(user, Permission.MANAGE_KNOWLEDGE)


@login_required
def article_list(request):
    articles = (
        Article.objects.filter(is_published=True)
        .select_related("category", "author")
        .prefetch_related("images")
    )
    categories = ArticleCategory.objects.annotate(
        published_count=Count("articles", filter=Q(articles__is_published=True))
    ).filter(published_count__gt=0)

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )
    if category_slug:
        articles = articles.filter(category__slug=category_slug)

    featured = articles.first()
    remaining = articles.exclude(pk=featured.pk) if featured else articles

    return render(
        request,
        "knowledge/article_list.html",
        {
            "featured": featured,
            "articles": remaining,
            "categories": categories,
            "query": query,
            "selected_category": category_slug,
            "can_manage_knowledge": _can_manage(request.user),
        },
    )


@login_required
def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.filter(is_published=True)
        .select_related("category", "author")
        .prefetch_related("images", "attachments"),
        slug=slug,
    )
    related = (
        Article.objects.filter(is_published=True, category=article.category)
        .exclude(pk=article.pk)
        .select_related("category")[:3]
    )
    return render(
        request,
        "knowledge/article_detail.html",
        {
            "article": article,
            "related_articles": related,
            "can_manage_knowledge": _can_manage(request.user),
            "is_preview": False,
        },
    )


@login_required
def attachment_download(request, pk):
    queryset = ArticleAttachment.objects.select_related("article")
    if not _can_manage(request.user):
        queryset = queryset.filter(article__is_published=True)
    attachment = get_object_or_404(queryset, pk=pk)
    try:
        stream = attachment.file.open("rb")
    except (FileNotFoundError, OSError) as exc:
        raise Http404("Файл не найден") from exc
    return FileResponse(
        stream,
        as_attachment=True,
        filename=attachment.file.name.rsplit("/", 1)[-1],
    )


@knowledge_manager_required
def manage_articles(request):
    articles = Article.objects.select_related("category", "author")
    categories = ArticleCategory.objects.annotate(article_count=Count("articles"))

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category_slug = request.GET.get("category", "").strip()

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(author__username__icontains=query)
            | Q(author__first_name__icontains=query)
            | Q(author__last_name__icontains=query)
        )
    if status == "published":
        articles = articles.filter(is_published=True)
    elif status == "draft":
        articles = articles.filter(is_published=False)
    if category_slug:
        articles = articles.filter(category__slug=category_slug)

    return render(
        request,
        "knowledge/manage_articles.html",
        {
            "articles": articles,
            "categories": categories,
            "query": query,
            "status": status,
            "selected_category": category_slug,
            "published_count": Article.objects.filter(is_published=True).count(),
            "draft_count": Article.objects.filter(is_published=False).count(),
        },
    )


def _article_form_context(request, article=None):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        image_formset = ArticleImageFormSet(
            request.POST,
            request.FILES,
            instance=article,
            prefix="images",
        )
        attachment_formset = ArticleAttachmentFormSet(
            request.POST,
            request.FILES,
            instance=article,
            prefix="attachments",
        )
    else:
        form = ArticleForm(instance=article)
        image_formset = ArticleImageFormSet(instance=article, prefix="images")
        attachment_formset = ArticleAttachmentFormSet(
            instance=article,
            prefix="attachments",
        )
    return form, image_formset, attachment_formset


def _save_article(request, form, image_formset, attachment_formset):
    article = form.save(commit=False)
    if article.author_id is None:
        article.author = request.user
    if article.is_published:
        article.published_at = article.published_at or timezone.now()
    else:
        article.published_at = None
    article.save()
    image_formset.instance = article
    attachment_formset.instance = article
    image_formset.save()
    attachment_formset.save()
    return article


@knowledge_manager_required
def article_create(request):
    form, image_formset, attachment_formset = _article_form_context(request)
    if request.method == "POST" and all(
        (form.is_valid(), image_formset.is_valid(), attachment_formset.is_valid())
    ):
        article = _save_article(request, form, image_formset, attachment_formset)
        messages.success(request, f"Статья «{article.title}» создана.")
        return redirect("knowledge:manage")
    return render(
        request,
        "knowledge/article_form.html",
        {
            "form": form,
            "image_formset": image_formset,
            "attachment_formset": attachment_formset,
            "article": None,
        },
    )


@knowledge_manager_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form, image_formset, attachment_formset = _article_form_context(request, article)
    if request.method == "POST" and all(
        (form.is_valid(), image_formset.is_valid(), attachment_formset.is_valid())
    ):
        article = _save_article(request, form, image_formset, attachment_formset)
        messages.success(request, f"Изменения статьи «{article.title}» сохранены.")
        return redirect("knowledge:manage")
    return render(
        request,
        "knowledge/article_form.html",
        {
            "form": form,
            "image_formset": image_formset,
            "attachment_formset": attachment_formset,
            "article": article,
        },
    )


@knowledge_manager_required
def article_preview(request, pk):
    article = get_object_or_404(
        Article.objects.select_related("category", "author").prefetch_related(
            "images", "attachments"
        ),
        pk=pk,
    )
    related = (
        Article.objects.filter(is_published=True, category=article.category)
        .exclude(pk=article.pk)
        .select_related("category")[:3]
    )
    return render(
        request,
        "knowledge/article_detail.html",
        {
            "article": article,
            "related_articles": related,
            "can_manage_knowledge": True,
            "is_preview": True,
        },
    )


@knowledge_manager_required
@require_POST
def article_publish(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.is_published = True
    article.published_at = article.published_at or timezone.now()
    article.save(update_fields=("is_published", "published_at", "updated_at"))
    messages.success(request, f"Статья «{article.title}» опубликована.")
    return redirect("knowledge:manage")


@knowledge_manager_required
@require_POST
def article_unpublish(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.is_published = False
    article.published_at = None
    article.save(update_fields=("is_published", "published_at", "updated_at"))
    messages.success(request, f"Статья «{article.title}» снята с публикации.")
    return redirect("knowledge:manage")


@knowledge_manager_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        title = article.title
        article.delete()
        messages.success(request, f"Статья «{title}» удалена.")
        return redirect("knowledge:manage")
    return render(
        request,
        "knowledge/article_confirm_delete.html",
        {"article": article},
    )


@knowledge_manager_required
def manage_categories(request):
    categories = ArticleCategory.objects.annotate(article_count=Count("articles"))
    return render(
        request,
        "knowledge/manage_categories.html",
        {"categories": categories},
    )


@knowledge_manager_required
def category_create(request):
    form = ArticleCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Категория «{category.name}» создана.")
        return redirect("knowledge:manage_categories")
    return render(
        request,
        "knowledge/category_form.html",
        {"form": form, "category": None},
    )


@knowledge_manager_required
def category_edit(request, pk):
    category = get_object_or_404(ArticleCategory, pk=pk)
    form = ArticleCategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Категория «{category.name}» обновлена.")
        return redirect("knowledge:manage_categories")
    return render(
        request,
        "knowledge/category_form.html",
        {"form": form, "category": category},
    )


@knowledge_manager_required
def category_delete(request, pk):
    category = get_object_or_404(ArticleCategory, pk=pk)
    if request.method == "POST":
        try:
            name = category.name
            category.delete()
        except ProtectedError:
            messages.error(
                request,
                "Нельзя удалить категорию, пока в ней есть статьи.",
            )
        else:
            messages.success(request, f"Категория «{name}» удалена.")
        return redirect("knowledge:manage_categories")
    return render(
        request,
        "knowledge/category_confirm_delete.html",
        {"category": category},
    )
