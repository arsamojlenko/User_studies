from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from users.models import Profile
import random

def get_next_step(user):
    """Returns the correct URL name the user must go to next."""
    profile = user.profile
    progress = profile.progress

    if progress == 'registered':
        return 'users:terms'
    if progress == 'terms_accepted':
        return 'users:questionnaire1'
    elif progress == 'questionnaire1':
        return 'users:pretest_explanation'
    elif progress == 'pretest_explanation':
            return 'tests:pretest'
    elif progress == 'pretest':
            return 'users:post_pretest_explanation'
    elif progress == 'post_pretest_explanation':
            return 'tests:start_training_page'
    elif progress == 'training1':
        return 'users:pre_posttest_explanation'
    elif progress == 'pre_posttest_explanation':
        return 'tests:posttest1'
    elif progress == 'posttest1':
        return 'users:questionnaire2'
    elif progress == 'questionnaire2':
        return 'users:instruction'
    elif progress == 'instruction':
        return 'core:dashboard'                     # free use starts
    elif progress == 'free_use':
        # Check if 7 days have passed
        if profile.free_use_started and timezone.now() >= profile.free_use_started + timedelta(days=7):
            return 'tests:posttest2'
        return 'core:dashboard'
    elif progress == 'posttest2':
        return 'users:questionnaire3'
    elif progress == 'questionnaire3':
        return 'users:final_thankyou'
    else:
        return 'core:dashboard'


def assign_condition_balanced(user):
    """
    Randomly assigns the user to control or gamified so that the two groups
    stay roughly equal in size.
    """
    profile = user.profile

    # Count how many users are already in each group
    control_count = Profile.objects.filter(condition='control').count()
    gamified_count = Profile.objects.filter(condition='gamified').count()

    if control_count < gamified_count:
        chosen = 'control'
    elif gamified_count < control_count:
        chosen = 'gamified'
    else:
        # Equal size : random
        chosen = random.choice(['control', 'gamified'])

    profile.condition = chosen
    profile.save(update_fields=['condition'])
    return chosen