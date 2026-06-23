from accounts.permissions import Permission, has_permission


def can_manage_courses(user):
    return has_permission(user, Permission.MANAGE_COURSES)


def can_download_course_materials(user, course):
    if can_manage_courses(user):
        return True

    if not has_permission(user, Permission.DOWNLOAD_PROTECTED_MATERIAL):
        return False

    if not course.is_published:
        return False

    return course.assignments.filter(employee_id=getattr(user, 'pk', None)).exists()


def can_download_lesson_material(user, lesson):
    return (
        bool(lesson.file)
        and lesson.file_active
        and can_download_course_materials(user, lesson.course)
    )
