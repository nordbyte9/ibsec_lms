from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from courses.models import Course, Lesson
from quizzes.models import Quiz, Question, Option

class Command(BaseCommand):
    help = "Создаёт демо-данные и аккаунты"

    def handle(self, *args, **kwargs):
        def create_user(username, email, pwd, role):
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            if not user.has_usable_password():
                user.set_password(pwd)
                user.save()
            prof = user.profile
            prof.role = role
            prof.save()
            return user

        admin = create_user('admin', 'admin@example.com', 'admin12345', 'admin')
        instructor = create_user('instructor', 'instructor@example.com', 'instructor12345', 'instructor')
        employee = create_user('employee', 'employee@example.com', 'employee12345', 'employee')

        course, _ = Course.objects.get_or_create(
            title='Основы информационной безопасности',
            defaults={'description': 'Базовый курс по ИБ для сотрудников.', 'author': instructor, 'is_published': True}
        )
        Lesson.objects.get_or_create(course=course, title='Введение в ИБ', order=1, defaults={'content': 'Основные понятия ИБ...'})
        Lesson.objects.get_or_create(course=course, title='Фишинг и социальная инженерия', order=2, defaults={'content': 'Как распознавать фишинговые письма...'})
        Lesson.objects.get_or_create(course=course, title='Пароли и аутентификация', order=3, defaults={'content': 'Надёжные пароли, MFA...'})

        quiz, _ = Quiz.objects.get_or_create(course=course, title='Тест по основам ИБ', defaults={'description': '3 вопроса', 'pass_score': 70, 'is_active': True})
        if not quiz.questions.exists():
            q1 = Question.objects.create(quiz=quiz, text='Что такое фишинг?')
            Option.objects.create(question=q1, text='Маскированная попытка выманить данные', is_correct=True)
            Option.objects.create(question=q1, text='Резервное копирование', is_correct=False)
            Option.objects.create(question=q1, text='Шифрование данных', is_correct=False)

            q2 = Question.objects.create(quiz=quiz, text='Выберите надёжный пароль')
            Option.objects.create(question=q2, text='qwerty123', is_correct=False)
            Option.objects.create(question=q2, text='P@55w0rd!', is_correct=False)
            Option.objects.create(question=q2, text='K9!mA7#xQ2', is_correct=True)

            q3 = Question.objects.create(quiz=quiz, text='Что означает MFA?')
            Option.objects.create(question=q3, text='Многофакторная аутентификация', is_correct=True)
            Option.objects.create(question=q3, text='Мобильный файловый архив', is_correct=False)
            Option.objects.create(question=q3, text='Межсетевой экран', is_correct=False)

        self.stdout.write(self.style.SUCCESS('Демо-данные созданы.'))
