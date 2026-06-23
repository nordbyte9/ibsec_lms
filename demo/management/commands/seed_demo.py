from datetime import timedelta
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import Department, Position, Profile
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course, Lesson, SecurityCategory, TrainingProgram
from integrations.models import IntegrationSyncLog
from quizzes.models import Answer, Option, Question, Quiz, Submission


class Command(BaseCommand):
    help = 'Создаёт демо-данные и аккаунты'

    def handle(self, *args, **kwargs):
        password_env = {
            'admin': 'DEMO_ADMIN_PASSWORD',
            'security_officer': 'DEMO_SECURITY_OFFICER_PASSWORD',
            'employee': 'DEMO_EMPLOYEE_PASSWORD',
            'employee2': 'DEMO_EMPLOYEE2_PASSWORD',
        }
        missing = [name for name in password_env.values() if not os.getenv(name)]
        if missing:
            raise CommandError(
                'Не заданы переменные демонстрационных паролей: ' + ', '.join(missing)
            )

        demo_passwords = {
            username: os.environ[env_name]
            for username, env_name in password_env.items()
        }

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

        def create_user(username, email, password, role, department=None, position=None, is_staff=False, is_superuser=False):
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.email = email
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.department = department
            profile.position = position
            profile.save()
            return user

        admin = create_user(
            'admin',
            'admin@example.com',
            demo_passwords['admin'],
            'admin',
            department=departments[0],
            position=positions[0],
            is_staff=True,
            is_superuser=True,
        )
        security_officer = create_user(
            'security_officer',
            'security_officer@example.com',
            demo_passwords['security_officer'],
            'security_officer',
            department=departments[0],
            position=positions[0],
        )
        employee = create_user(
            'employee',
            'employee@example.com',
            demo_passwords['employee'],
            'employee',
            department=departments[1],
            position=positions[1],
        )
        employee_two = create_user(
            'employee2',
            'employee2@example.com',
            demo_passwords['employee2'],
            'employee',
            department=departments[2],
            position=positions[2],
        )

        category_specs = [
            ('personal-data', 'Персональные данные', 'Материалы о защите и обработке персональных данных.'),
            ('phishing', 'Фишинг', 'Программы по распознаванию фишинга и социальной инженерии.'),
            ('password-security', 'Парольная безопасность', 'Обучение правилам работы с паролями и MFA.'),
            ('corporate-mail', 'Корпоративная почта', 'Безопасная работа с корпоративной почтой и вложениями.'),
        ]
        categories = {}
        for code, name, description in category_specs:
            category, _ = SecurityCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description},
            )
            category.name = name
            category.description = description
            category.save(update_fields=['name', 'description'])
            categories[code] = category

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
            program, _ = TrainingProgram.objects.get_or_create(
                title=title,
                defaults={
                    'category': categories[category_code],
                    'description': description,
                    'is_mandatory': is_mandatory,
                    'periodicity_days': periodicity_days,
                },
            )
            program.category = categories[category_code]
            program.description = description
            program.is_mandatory = is_mandatory
            program.periodicity_days = periodicity_days
            program.save(update_fields=['category', 'description', 'is_mandatory', 'periodicity_days'])
            programs[title] = program

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
            defaults={
                'description': '3 вопроса',
                'pass_score': 70,
                'time_limit_minutes': 20,
                'max_attempts': 3,
                'is_active': True,
            },
        )
        quiz.description = '3 вопроса'
        quiz.pass_score = 70
        quiz.time_limit_minutes = 20
        quiz.max_attempts = 3
        quiz.is_active = True
        quiz.save(update_fields=['description', 'pass_score', 'time_limit_minutes', 'max_attempts', 'is_active'])
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

        created_submissions = []
        demo_attempts = [
            (employee, 1, 100.0, True),
            (employee, 2, 66.67, False),
            (employee_two, 1, 100.0, True),
        ]
        for demo_user, attempt_number, percent, passed in demo_attempts:
            submission, _ = Submission.objects.get_or_create(
                user=demo_user,
                quiz=quiz,
                attempt_number=attempt_number,
                defaults={
                    'score': 0,
                    'percent': percent,
                    'passed': passed,
                },
            )
            submission.score = 3 if passed else 2
            submission.percent = percent
            submission.passed = passed
            submission.save(update_fields=['score', 'percent', 'passed'])
            if not submission.answers.exists():
                for question in quiz.questions.all():
                    Answer.objects.get_or_create(submission=submission, question=question)
            created_submissions.append(submission)

        today = timezone.localdate()
        created_assignments = []
        assignments = [
            (employee, course, admin, today + timedelta(days=14), CourseAssignment.Status.ASSIGNED),
            (employee, course, security_officer, today + timedelta(days=7), CourseAssignment.Status.IN_PROGRESS),
            (employee_two, course, security_officer, today - timedelta(days=3), CourseAssignment.Status.COMPLETED),
            (employee_two, course, admin, today - timedelta(days=1), CourseAssignment.Status.OVERDUE),
        ]
        for employee_user, assigned_course, assigned_by, due_date, status in assignments:
            assignment, _ = CourseAssignment.objects.get_or_create(
                employee=employee_user,
                course=assigned_course,
                due_date=due_date,
                defaults={
                    'assigned_by': assigned_by,
                    'status': status,
                },
            )
            assignment.assigned_by = assigned_by
            assignment.status = status
            assignment.due_date = due_date
            assignment.save()
            created_assignments.append(assignment)

        audit_entries = [
            (admin, 'course_assigned', 'CourseAssignment', created_assignments[0].pk, 'Демо: назначен курс сотруднику employee'),
            (employee, 'quiz_submitted', 'Submission', created_submissions[0].pk, 'Демо: первая попытка теста сотрудником employee'),
            (security_officer, 'assignment_completed', 'CourseAssignment', created_assignments[2].pk, 'Демо: завершено назначение сотрудником employee2'),
            (admin, 'csv_export', 'Report', 'employee_report', 'Демо: экспорт отчета по сотрудникам'),
        ]
        for user, action, object_type, object_id, description in audit_entries:
            log_action(user, action, object_type, object_id, description, request=None)

        integration_logs = [
            ('csv', 'success', 3, 3, 4, 'Демо: импорт оргструктуры из CSV'),
        ]
        for source, status, departments_count, positions_count, users_count, message in integration_logs:
            log = IntegrationSyncLog.objects.create(
                source=source,
                status=status,
                imported_departments=departments_count,
                imported_positions=positions_count,
                imported_users=users_count,
                message=message,
                finished_at=timezone.now() if status != 'started' else None,
            )
            if status == 'started':
                log.message = message
                log.save(update_fields=['message'])

        self.stdout.write(self.style.SUCCESS('Демо-данные созданы.'))
