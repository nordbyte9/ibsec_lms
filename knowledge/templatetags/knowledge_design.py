from django import template
from django.templatetags.static import static

register = template.Library()

FALLBACKS = (
    ("фиш", "img/courses/zashchita-ot-fishinga.webp"),
    ("парол", "img/courses/paroli-i-autentifikatsiya.webp"),
    ("доступ", "img/courses/upravlenie-dostupom.webp"),
    ("сет", "img/courses/setevaya-bezopasnost.webp"),
    ("облак", "img/courses/kiberbezopasnost-sotrudnikov.webp"),
)


@register.simple_tag
def article_cover(article):
    if article.cover_image:
        return article.cover_image.url
    haystack = f"{article.title} {article.summary} {article.category.name}".lower()
    for needle, path in FALLBACKS:
        if needle in haystack:
            return static(path)
    return static("img/courses/osnovy-informatsionnoy-bezopasnosti.webp")
