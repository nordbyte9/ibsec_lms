from django.db import connections
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Return 200 only when the database and the migrated schema are ready."""

    connection = connections["default"]

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        table_names = set(connection.introspection.table_names())
        required_tables = {"django_migrations", "auth_user"}
        missing_tables = sorted(required_tables - table_names)
        if missing_tables:
            return JsonResponse(
                {
                    "status": "unhealthy",
                    "database": "schema_not_ready",
                    "missing_tables": missing_tables,
                },
                status=503,
            )
    except Exception:
        return JsonResponse(
            {"status": "unhealthy", "database": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok", "database": "ok"})
