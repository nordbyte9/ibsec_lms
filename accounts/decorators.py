from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

from .permissions import has_permission


def permission_required(permission):
    """Ограничивает представление прикладным разрешением IBSec LMS."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if not has_permission(request.user, permission):
                return HttpResponseForbidden('Недостаточно прав')

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
