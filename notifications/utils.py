from django.core.mail import send_mail
from django.conf import settings

def send_notice_email(to_email, subject, body):
    send_mail(subject, body, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'), [to_email])
