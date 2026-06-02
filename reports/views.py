from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from quizzes.models import Submission, Quiz
import csv
from django.db.models import Avg

@login_required
def my_progress(request):
    submissions = Submission.objects.filter(user=request.user).select_related('quiz').order_by('-taken_at')
    return render(request, 'reports/my_progress.html', {'submissions': submissions})

@login_required
def analytics(request):
    if request.user.profile.role not in ('security_officer', 'admin'):
        return HttpResponseForbidden('Недостаточно прав')
    quizzes = Quiz.objects.all().prefetch_related('submissions', 'course')
    stats = [
        {
            'course': q.course.title,
            'quiz': q.title,
            'count': q.submissions.count(),
            'avg': round(q.submissions.aggregate(Avg('score'))['score__avg'] or 0.0, 2)
        }
        for q in quizzes
    ]
    return render(request, 'reports/analytics.html', {'stats': stats})

@login_required
def export_csv(request):
    if request.user.profile.role not in ('security_officer', 'admin'):
        return HttpResponseForbidden('Недостаточно прав')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="submissions.csv"'
    writer = csv.writer(response)
    writer.writerow(['Пользователь', 'Тест', 'Баллы', 'Дата'])
    for s in Submission.objects.select_related('user', 'quiz'):
        writer.writerow([s.user.username, s.quiz.title, s.score, s.taken_at.strftime('%Y-%m-%d %H:%M')])
    return response
