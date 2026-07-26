from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta

def get_next_step(user):
    """Returns the correct URL name the user must go to next."""
    profile = user.profile
    progress = profile.progress

    if progress == 'registered':
        return 'users:questionnaire1'
    elif progress == 'questionnaire1':
        return 'tests:pretest'
    elif progress == 'pretest':
        return 'tests:start_training_page'          # first normal training
    elif progress == 'training1':
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