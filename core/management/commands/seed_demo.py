from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Department, Position, Profile
from courses.models import Course, Lesson, SecurityCategory, TrainingProgram
from quizzes.models import Option, Question, Quiz


class Command(BaseCommand):
    help = 'Создаёт демо-данные и аккаунты'

    def handle(self, *args, **kwargs):
        departments = [
            Department.objects.get_or_create(name='Отдел информационной безопасности')[0],
            Department.objects.get_or_create(name='ИТ-отдел')[0],
            Department.objects.get_or_create(name='Отдел кадров')[0],
        ]
        positions = [
            Position.objects.get_or_create(name='Специалист по ИБ')[0],
            Position.objects.get_or_create(name='Системный администратор')[0],
            Position.objects.get_or_create(name='Менеджер по персоналу')[0],
        ]

        def create_user(username, email, pwd, role, department=None, position=None, is_staff=False, is_superuser=False):
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.email = email
            user.set_password(pwd)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.department = department
            profile.position = position
            profile.save()
            return user

        create_user(
            'admin',
            'admin@example.com',
            'admin12345',
            'admin',
            department=departments[0],
            position=positions[0],
            is_staff=True,
            is_superuser=True,
        )
        security_officer = create_user(
            'security_officer',
            'security_officer@example.com',
            'security_officer12345',
            'security_officer',
            department=departments[0],
            position=positions[0],
        )
        create_user(
            'employee',
            'employee@example.com',
            'employee12345',
            'employee',
            department=departments[1],
            position=positions[1],
        )

        category_specs = [
            ('personal-data', 'Персональные данные', 'Материалы о защите и обработке персональных данных.'),
            ('phishing', 'Фишинг', 'Программы по распознаванию фишинга и социальной инженерии.'),
            ('password-security', 'Парольная безопасность', 'Обучение правилам работы с паролями и MFA.'),
            ('corporate-mail', 'Корпоративная почта', 'Безопасная работа с корпоративной почтой и вложениями.'),
        ]
        categories = {}
        for code, name, description in category_specs:
            categories[code], _ = SecurityCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description},
            )
            if categories[code].name != name or categories[code].description != description:
                categories[code].name = name
                categories[code].description = description
                categories[code].save(update_fields=['name', 'description'])

        program_specs = [
            (
                'Антифишинг для сотрудников',
                'phishing',
                'Как распознавать фишинговые письма и не реагировать на социальную инженерию.',
                True,
                365,
            ),
            (
                'Работа с персональными данными',
                'personal-data',
                'Базовые требования по защите и обработке персональных данных.',
                True,
                365,
            ),
            (
                'Парольная гигиена',
                'password-security',
                'Создание и хранение надёжных паролей, MFA и защита учётных записей.',
                True,
                180,
            ),
            (
                'Безопасная корпоративная почта',
                'corporate-mail',
                'Практики безопасной работы с корпоративной почтой и вложениями.',
                False,
                365,
            ),
        ]
        programs = {}
        for title, category_code, description, is_mandatory, periodicity_days in program_specs:
            programs[title], _ = TrainingProgram.objects.get_or_create(
                title=title,
                defaults={
                    'category': categories[category_code],
                    'description': description,
                    'is_mandatory': is_mandatory,
                    'periodicity_days': periodicity_days,
                },
            )
            programs[title].category = categories[category_code]
            programs[title].description = description
            programs[title].is_mandatory = is_mandatory
            programs[title].periodicity_days = periodicity_days
            programs[title].save()

        course, _ = Course.objects.get_or_create(
            title='Основы информационной безопасности',
            defaults={
                'description': 'Базовый курс по ИБ для сотрудников.',
                'author': security_officer,
                'is_published': True,
            },
        )
        course.description = 'Базовый курс по ИБ для сотрудников.'
        course.author = security_officer
        course.is_published = True
        course.training_program = programs['Антифишинг для сотрудников']
        course.is_mandatory = True
        course.validity_days = 365
        course.save()
        course.target_departments.set([departments[0], departments[1]])
        course.target_positions.set([positions[0], positions[1]])

        Lesson.objects.get_or_create(
            course=course,
            title='Введение в ИБ',
            order=1,
            defaults={'content': 'Основные понятия ИБ...'},
        )
        Lesson.objects.get_or_create(
            course=course,
            title='Фишинг и социальная инженерия',
            order=2,
            defaults={'content': 'Как распознавать фишинговые письма...'},
        )
        Lesson.objects.get_or_create(
            course=course,
            title='Пароли и аутентификация',
            order=3,
            defaults={'content': 'Надёжные пароли, MFA...'},
        )

        quiz, _ = Quiz.objects.get_or_create(
            course=course,
            title='Тест по основам ИБ',
            defaults={'description': '3 вопроса', 'pass_score': 70, 'is_active': True},
        )
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
