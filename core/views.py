from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from tests.models import TestSession
from collections import defaultdict
import csv
from django.http import HttpResponse
from datetime import date, timedelta
from users.utils import get_next_step

@login_required
def home(request):
    next_url = get_next_step(request.user)
    return redirect(next_url)

@login_required
def researcher_dashboard(request):
    # Only staff can see the full admin dashboard
    if request.user.is_staff:
        all_sessions = TestSession.objects.select_related('user', 'user__profile').order_by('user__username', '-start_time')
        sessions_by_user = defaultdict(list)
        for session in all_sessions:
            sessions_by_user[session.user].append(session)
        return render(request, 'core/admin_dashboard.html', {
            'sessions_by_user': dict(sessions_by_user)
        })

    # Gamified users are sent to their personal dashboard
    if hasattr(request.user, 'profile') and request.user.profile.condition == 'gamified':
        return redirect('core:user_dashboard')

    # Redirect control group to test page
    return redirect('tests:start_training_page')

@login_required
def user_dashboard(request):
    print("Current progress:", request.user.profile.progress)
    print("Next step:", get_next_step(request.user))

    profile = request.user.profile
    next_step = get_next_step(request.user)

    # Allow dashboard from pretest onwards
    allowed = ['pretest', 'training1', 'posttest1', 'questionnaire2',
               'instruction', 'free_use', 'posttest2', 'questionnaire3', 'finished']

    if profile.progress not in allowed and not request.user.is_staff:
        return redirect(next_step)
    # if next_step not in ['core:dashboard', 'core:user_dashboard'] and not request.user.is_staff:
    #         return redirect(next_step)
    
    # Force the correct next step if the user still has mandatory tasks
    #next_step = get_next_step(request.user)
    #if next_step not in ['core:dashboard', 'core:user_dashboard']:
    #    return redirect(next_step)

    if not request.user.is_staff and request.user.profile.condition != 'gamified':
        return redirect('tests:start_training_page')

    my_sessions = TestSession.objects.filter(user=request.user).order_by('-start_time')

    # Best matrix streak
    best_streak = 0
    if my_sessions.exists():
        best_streak = max((s.longest_streak or 0) for s in my_sessions)

    # Week activity
    today = date.today()
    last_7_days = []

    # Get all dates the user trained
    trained_dates = set(
        TestSession.objects.filter(
            user=request.user,
            end_time__isnull=False
        ).dates('start_time', 'day')
    )

    for i in range(6, -1, -1):          # from 6 days ago → today
        d = today - timedelta(days=i)
        last_7_days.append({
            'date': d,
            'active': d in trained_dates
        })

    return render(request, 'core/user_dashboard.html', {
        'sessions': my_sessions,
        'best_streak': best_streak,
        'last_7_days': last_7_days,
        'next_step': next_step,  # ← important
        'progress': profile.progress,
    })

@login_required
def export_data(request):
    return render(request, 'core/export.html')

@login_required
def participant_list(request):
    return render(request, 'core/participants.html')


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def export_data(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rpm_study_export.csv"'

    writer = csv.writer(response)

    # Header row
    writer.writerow([
        'Username',
        'Current Condition',
        'Session Type',
        'Condition at Session',
        'Score',
        'Start Time',
        'End Time',
        'Total Time (seconds)',
    ])

    sessions = TestSession.objects.select_related('user', 'user__profile').order_by('user__username', '-start_time')

    for s in sessions:
        current_condition = s.user.profile.condition if hasattr(s.user, 'profile') else 'unknown'
        writer.writerow([
            s.user.username,
            current_condition,
            s.session_type,
            s.condition,
            s.score,
            s.start_time,
            s.end_time,
            s.total_time_seconds,
        ])

    return response