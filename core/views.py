from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from tests.models import TestSession
from collections import defaultdict
import csv
from django.http import HttpResponse
from datetime import date, timedelta, datetime, time
from users.utils import get_next_step
from django.contrib.auth.models import User
from users.models import QuestionnaireResponse
from django.utils import timezone

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

    if not request.user.is_staff and request.user.profile.condition != 'gamified':
        return redirect('tests:start_training_page')

    # Check if end of study has been reached
    show_final_message = False
    seconds_until_end = None

    if profile.progress == 'free_use' and profile.free_use_started:
        #end_time = profile.free_use_started + timedelta(minutes=1)
        target_date = profile.free_use_started + timedelta(days=3)   # 3 days to learn
        end_time = timezone.make_aware(
            datetime.combine(target_date, time.min)  # 00:00 Uhr
        )
        print(f"Time started: {profile.free_use_started}")
        print(f"Time target: {target_date}")
        print(f"Time end: {end_time}")
        now = timezone.now()

        if now >= end_time:
            show_final_message = True
        else:
            seconds_until_end = int((end_time - now).total_seconds())

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

    # Highest score from all sessions
    highest_score = 0
    if my_sessions.exists():
        highest_score = max(s.score or 0 for s in my_sessions)

    return render(request, 'core/user_dashboard.html', {
        'sessions': my_sessions,
        'best_streak': best_streak,
        'last_7_days': last_7_days,
        'next_step': next_step,
        'progress': profile.progress,
        'highest_score': highest_score,
        'show_final_message': show_final_message,
        'seconds_until_end': seconds_until_end,
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
    response['Content-Disposition'] = 'attachment; filename="rpm_study_full_export.csv"'

    writer = csv.writer(response)

    # Header
    writer.writerow([
        # user
        'User ID', 'Username', 'Email', 'Condition', 'Study Progress',
        'Current Daily Streak', 'Longest Daily Streak', 'Last Activity Date', 'Last Login', 'Registration Date',
        # session
        'Session ID', 'Session Type', 'Session Condition', 'Session Score',
        'Longest Streak', 'Total Time', 'Start Time', 'End Time', 'Answered Count',
        # answers
        'Item ID', 'Points of Item', 'User Answer', 'Correct Answer', 'Is Correct', 'Points Earned',
    ])

    users = User.objects.select_related('profile').all().order_by('id')

    for user in users:
        profile = getattr(user, 'profile', None)
        sessions = TestSession.objects.filter(user=user).order_by('start_time')

        # Find the first training session
        first_training = sessions.filter(session_type='training').order_by('start_time').first()

        for session in sessions:
            is_important = session.session_type in ['pretest', 'posttest1', 'posttest2'] or \
                           (session.session_type == 'training' and first_training and session.id == first_training.id)

            responses = session.responses or {}

            if is_important and responses:
                # Details for pretest, training1, posttest1 and posttest2
                for item_id, resp in responses.items():
                    writer.writerow([
                        user.id, user.username, user.email,
                        profile.condition if profile else '',
                        profile.progress if profile else '',
                        profile.current_daily_streak if profile else '',
                        profile.longest_daily_streak if profile else '',
                        profile.last_activity_date if profile else '',
                        profile.last_login_at if profile else '',
                        user.date_joined,

                        session.id, session.session_type, session.condition,
                        session.score, session.longest_streak, session.total_time_seconds,
                        session.start_time, session.end_time, session.answered_count,

                        resp.get('item_id', item_id),
                        resp.get('points', ''),
                        resp.get('user_answer', ''),
                        resp.get('correct_answer', ''),
                        resp.get('is_correct', ''),
                        resp.get('points', 0) if resp.get('is_correct') else 0,
                    ])
            else:
                # Summary row only
                writer.writerow([
                    user.id, user.username, user.email,
                    profile.condition if profile else '',
                    profile.progress if profile else '',
                    profile.current_daily_streak if profile else '',
                    profile.longest_daily_streak if profile else '',
                    profile.last_activity_date if profile else '',
                    profile.last_login_at if profile else '',
                    user.date_joined,

                    session.id, session.session_type, session.condition,
                    session.score, session.longest_streak, session.total_time_seconds,
                    session.start_time, session.end_time,

                    '', '', '', '', '', ''
                ])

    return response

@login_required
@user_passes_test(is_staff)
def export_questionnaires(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rpm_questionnaires_export.csv"'

    writer = csv.writer(response)

    # Header
    writer.writerow([
        'User ID',
        'Username',
        'Condition',
        'Questionnaire',
        'Submitted At',
        'Age',
        'Gender',
        'Prior Knowledge',
        'Freq Educational',
        'Freq Social',
        'Freq Video',
        'Freq Games',
        'Features',
        'Genuine Interest (1-5)',
        'Less Use Reasons',
        'Less Use Other (text)',
        'Less Use Severity (1-5)',
        'All Answers (JSON)',
    ])

    responses = (QuestionnaireResponse.objects
                 .select_related('user', 'user__profile')
                 .order_by('user__id', 'questionnaire'))

    for resp in responses:
        answers = resp.answers or {}
        profile = getattr(resp.user, 'profile', None)

        # Checkboxes
        features = answers.get('features', [])
        if isinstance(features, list):
            features_str = ', '.join(features)
        else:
            features_str = str(features)

        # Less use reasons (checkboxes)
        less_use_reasons = answers.get('less_use_reasons', [])
        if isinstance(less_use_reasons, list):
            less_use_reasons_str = ', '.join(less_use_reasons)
        else:
            less_use_reasons_str = str(less_use_reasons)

        writer.writerow([
            resp.user.id,
            resp.user.username,
            getattr(profile, 'condition', ''),
            resp.get_questionnaire_display(),
            resp.submitted_at,
            answers.get('age', ''),
            answers.get('gender', ''),
            answers.get('prior_knowledge', ''),
            answers.get('freq_edu', ''),
            answers.get('freq_social', ''),
            answers.get('freq_video', ''),
            answers.get('freq_games', ''),
            features_str,
            answers.get('genuine_interest', ''),
            less_use_reasons_str,
            answers.get('less_use_other', ''),
            answers.get('less_use_severity', ''),
            str(answers),
        ])

    return response