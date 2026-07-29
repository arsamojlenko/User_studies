from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import RPMItem, TestSession
import json
from datetime import datetime
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta
from users.utils import get_next_step
from users.utils import assign_condition_balanced
import random

@login_required
def start_session(request, session_type):
    user = request.user
    condition = getattr(user, 'condition', 'control')

    # Placeholder item selection TODO
    if session_type == 'pretest':
        items = list(RPMItem.objects.filter(set_number=1)[:12])
    elif session_type == 'posttest':
        items = list(RPMItem.objects.filter(set_number=2)[:12])
    else:
        items = list(RPMItem.objects.all()[:10])

    session = TestSession.objects.create(
        user=user,
        session_type=session_type,
        condition=condition
    )
    session.items.set(items)

    context = {
        'session': session,
        'items': items,
        'is_gamified': condition == 'gamified'
    }
    return render(request, 'tests/session.html', context)

@login_required
def submit_session(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(TestSession, id=session_id, user=request.user)
        try:
            data = json.loads(request.body)
            session.responses = data.get('responses', {})
            session.end_time = datetime.now()
            # Simple scoring
            correct = sum(1 for r in session.responses.values() if r.get('correct'))
            session.score = correct
            session.total_time_seconds = data.get('total_time', 0)
            session.save()
            return JsonResponse({'status': 'success', 'score': session.score})
        except:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def start_training_page(request):
    """Page that only shows the start training button"""
    return render(request, 'tests/start_training.html')

@login_required
def begin_training(request):
    """Called when the user presses the start training button"""
    if request.method != 'POST':
        return redirect('tests:start_training_page')

    profile = request.user.profile

    condition = 'control'
    if hasattr(request.user, 'profile'):
        condition = profile.condition

    session = TestSession.objects.create(
        user=request.user,
        session_type='training',
        condition=request.user.profile.condition,
        start_time=timezone.now()
    )
    # For testing
    #items = list(RPMItem.objects.all()[:3])

    is_first_training = not TestSession.objects.filter(
        user=request.user,
        session_type='training'
    ).exists()

    if is_first_training:
        items = get_fixed_session_items('training1')
    else:
        items = get_random_training_items()

    session.items.set(items)

    return redirect('tests:training_session', session_id=session.id)


@login_required
def stop_training(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)

    # How many items belong to this session
    total = session.items.count()
    answered = len(session.responses or {})

    # Mandatory sessions must be fully answered
    is_mandatory = session.session_type in ['pretest', 'posttest1', 'posttest2'] or \
                   (session.session_type == 'training' and
                    not TestSession.objects.filter(user=request.user, session_type='training',
                                                   start_time__lt=session.start_time).exists())

    if is_mandatory and answered < total:
        # If user tries to stop early send them back
        from django.contrib import messages
        messages.warning(request,f"Please answer all questions before ending the session. "
                                 f"You have answered {answered} out of {total}.")
        return redirect('tests:training_session', session_id=session.id)

    if session.end_time is None:
        session.end_time = timezone.now()
        session.total_time_seconds = int((session.end_time - session.start_time).total_seconds())
        session.answered_count = answered
        duration = session.end_time - session.start_time
        session.total_time_seconds = int(duration.total_seconds())
        session.save()

        # Update daily streak
        profile = request.user.profile
        today = date.today()

        if profile.last_activity_date is None:
            # First time
            profile.current_daily_streak = 1
            profile.longest_daily_streak = 1
        else:
            delta = (today - profile.last_activity_date).days

            if delta == 0:
                # Already trained today
                pass
            elif delta == 1:
                # Consecutive day
                profile.current_daily_streak += 1
                profile.longest_daily_streak = max(
                    profile.longest_daily_streak,
                    profile.current_daily_streak
                )
            else:
                # Streak broken
                profile.current_daily_streak = 1

        profile.last_activity_date = today
        profile.save()

        print("=== STOP DEBUG ===")
        print("Session type:", session.session_type)
        print("Progress before:", profile.progress)

        if session.session_type == 'pretest':
            profile.progress = 'pretest'
            assign_condition_balanced(request.user)
            print("set to pretest")

        #elif session.session_type == 'training' and profile.progress == 'post_pretest_explanation':
        #elif session.session_type == 'training':
            #if profile.progress in ['pretest', 'post_pretest_explanation']:
            #    profile.progress = 'training1'
            #profile.progress = 'training1'
            #print("forcing to training1")

        elif session.session_type == 'training':
            is_first_training = not TestSession.objects.filter(
                user=request.user,
                session_type='training',
                start_time__lt=session.start_time
            ).exists()

            if is_first_training:
                profile.progress = 'training1'

        elif session.session_type == 'posttest1':
            profile.progress = 'posttest1'
            print("set to posttest1")

        elif session.session_type == 'posttest2':
            profile.progress = 'posttest2'

        profile.save()
        print("Progress after:", profile.progress)
        print("Next step will be:", get_next_step(request.user))

    return redirect(get_next_step(request.user))

@login_required
def session_history(request):
    sessions = TestSession.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'tests/history.html', {'sessions': sessions})


@login_required
def training_session(request, session_id):
    session = get_object_or_404(TestSession, id=session_id, user=request.user)

    is_first_training = (
            session.session_type == 'training' and
            not TestSession.objects.filter(
                user=request.user,
                session_type='training',
                start_time__lt=session.start_time
            ).exists()
    )

    if session.end_time is not None:
        return redirect('tests:start_training_page')

    items = list(session.items.all().order_by('id'))
    if not items:
        items = list(RPMItem.objects.all()[:3])
        session.items.set(items)

    try:
        current_index = int(request.GET.get('q', 0))
    except ValueError:
        current_index = 0

    current_index = max(0, min(current_index, len(items) - 1))
    current_item = items[current_index]

    responses_json = json.dumps(session.responses or {}, cls=DjangoJSONEncoder)

    context = {
        'session': session,
        'items': items,
        'current_item': current_item,
        'current_index': current_index,
        'total_items': len(items),
        'is_gamified': session.condition == 'gamified',
        'has_previous': current_index > 0,
        'has_next': current_index < len(items) - 1,
        'responses_json': responses_json,
        'is_first_training': is_first_training,
    }
    return render(request, 'tests/training_session.html', context)

@login_required
def submit_answer(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    session = get_object_or_404(TestSession, id=session_id, user=request.user)
    data = json.loads(request.body)

    item_id = data.get('item_id')
    user_answer = str(data.get('answer'))
    item = get_object_or_404(RPMItem, id=item_id)

    is_correct = (user_answer == item.correct_answer)

    # Save response
    responses = session.responses or {}
    responses[str(item.id)] = {
        'user_answer': user_answer,
        'correct_answer': item.correct_answer,
        'is_correct': is_correct,
        'item_id': item.item_id,
        'points': item.points if is_correct else 0,
    }
    session.responses = responses
    session.score = sum(r.get('points', 0) for r in responses.values())
    session.save()

    # Count how many questions got answered during the free use period
    session.answered_count = len(session.responses)
    session.save()

    # Calculate longest streak
    # Items should be in the same order as shown
    items = list(session.items.all().order_by('id'))
    current_streak = 0
    longest_streak = 0

    for it in items:
        resp = responses.get(str(it.id))
        if resp and resp.get('is_correct'):
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    # Save during session
    session.longest_streak = longest_streak
    session.save()

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': item.correct_answer,
        'score': session.score,
        'longest_streak': longest_streak,
        'points_earned': item.points if is_correct else 0,
    })

@login_required
def pretest(request):
    profile = request.user.profile
    if profile.progress != 'pretest_explanation':
        return redirect(get_next_step(request.user))

    session, created = TestSession.objects.get_or_create(
        user=request.user,
        session_type='pretest',
        defaults={'condition': profile.condition}
    )

    if created or not session.items.exists():
        # For testing
       #items = RPMItem.objects.filter(set_number=1).order_by('id')[:2]
        # Proper version
        items = get_fixed_session_items('pretest')
        session.items.set(items)

    return redirect('tests:training_session', session_id=session.id)

@login_required
def posttest1(request):
    profile = request.user.profile
    if profile.progress != 'pre_posttest_explanation':
        return redirect(get_next_step(request.user))

    session, created = TestSession.objects.get_or_create(
        user=request.user,
        session_type='posttest1',
        defaults={'condition': profile.condition}
    )

    if created or not session.items.exists():
        # For testing
        #items = RPMItem.objects.filter(set_number=2).order_by('id')[:2]
        # Proper version
        items = get_fixed_session_items('posttest1')
        session.items.set(items)

    return redirect('tests:training_session', session_id=session.id)

@login_required
def posttest2(request):
    profile = request.user.profile
    if profile.progress not in ['free_use', 'posttest2']:
        return redirect(get_next_step(request.user))

    session, created = TestSession.objects.get_or_create(
        user=request.user,
        session_type='posttest2',
        defaults={'condition': profile.condition}
    )
    if created or not session.items.exists():
        # For testing
        #items = RPMItem.objects.filter(set_number=3).order_by('id')[:2]
        # Proper version
        items = get_fixed_session_items('posttest2')
        session.items.set(items)

    return redirect('tests:training_session', session_id=session.id)


def get_random_training_items():
    """3 random matrices from each level (never reserved ones)."""
    selected = []
    for level in [1, 2, 3]:
        pool = list(RPMItem.objects.filter(set_number=level, is_reserved=False))
        if len(pool) >= 3:
            selected.extend(random.sample(pool, 3))
        else:
            selected.extend(pool)
    random.shuffle(selected)
    return selected

def get_fixed_session_items(session_type):
    """
        Returns exactly 9 fixed matrices (3 from each level) for mandatory tests.
        Different non overlapping slices for pretest, training1, posttest1, posttest2.
    """
    offsets = {
        'pretest': 0,
        'training1': 3,
        'posttest1': 6,
        'posttest2': 9,
    }
    offset = offsets.get(session_type, 0)

    selected = []
    for level in [1, 2, 3]:
        items = list(
            RPMItem.objects.filter(set_number=level, is_reserved=True)
            .order_by('id')[offset:offset+3]
        )
        selected.extend(items)
    return selected