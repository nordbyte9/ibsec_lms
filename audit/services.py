from .models import AuditLog


def log_action(user, action, object_type, object_id, description, request=None):
    ip_address = None
    user_agent = ''
    if request is not None:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            ip_address = forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    return AuditLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id is not None else '',
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
