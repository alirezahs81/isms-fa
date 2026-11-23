from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url


ROLE_GROUPS = {
    "admin": "isms_admin",
    "finance": "isms_finance",
    "support": "isms_support",
    "viewer": "isms_viewer",
}


def role_required(*roles):
    """Allow superusers or staff assigned to one of the named ISMS role groups."""
    unknown = set(roles) - set(ROLE_GROUPS)
    if unknown:
        raise ValueError(f"Unknown ISMS roles: {', '.join(sorted(unknown))}")

    group_names = [ROLE_GROUPS[role] for role in roles]

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(), resolve_url(settings.LOGIN_URL)
                )
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            if user.is_staff and user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have an ISMS role for this operation.")

        return wrapped

    return decorator
