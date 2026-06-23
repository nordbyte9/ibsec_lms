"""Load the existing IBSec LMS demo dataset only when it is absent."""

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from courses.models import Course
from quizzes.models import Quiz


class Command(BaseCommand):
    help = "Creates demo data once and skips repeated container restarts."

    def handle(self, *args, **options):
        required_users_exist = all(
            User.objects.filter(username=username).exists()
            for username in ("admin", "security_officer", "employee", "employee2")
        )
        course_exists = Course.objects.filter(
            title="Основы информационной безопасности"
        ).exists()
        quiz_exists = Quiz.objects.filter(title="Тест по основам ИБ").exists()

        if required_users_exist and course_exists and quiz_exists:
            self.stdout.write(
                self.style.WARNING(
                    "Demo data already exists; seed_demo was skipped."
                )
            )
            return

        call_command("seed_demo")
        self.stdout.write(self.style.SUCCESS("Demo data initialization completed."))
