from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .navigation import breadcrumbs

def home(request):
    return render(request, 'core/home.html')


@login_required
def help_page(request):
    return render(
        request,
        'core/help.html',
        {
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Справка', None)),
        },
    )
