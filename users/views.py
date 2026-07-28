from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .forms import SimpleRegisterForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from users.utils import get_next_step

def register(request):
    if request.method == 'POST':
        form = SimpleRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Make sure progress starts correctly
            profile = user.profile
            profile.progress = 'registered'
            profile.save()

            print("Progress after registration:", user.profile.progress)
            print("Next step would be:", get_next_step(user))

            return redirect('users:terms')          # ← go directly to terms
    else:
        form = SimpleRegisterForm()

    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def dashboard(request):
    return redirect('core:dashboard')  # Or render your main dashboard


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()  # Delete profile and all related TestSessions
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('login')

    return render(request, 'users/delete_account.html')


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        # Redirect to a dedicated thank-you page
        return redirect('users:account_deleted')

    return render(request, 'users/delete_account.html')

def account_deleted(request):
    return render(request, 'users/account_deleted.html')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

@receiver(user_logged_in)
def update_last_login(sender, request, user, **kwargs):
    if hasattr(user, 'profile'):
        user.profile.last_login_at = timezone.now()
        user.profile.save(update_fields=['last_login_at'])


@login_required
def questionnaire1(request):
    profile = request.user.profile
    print("=== Questionnaire 1 ===")
    print("Current progress:", profile.progress)
    print("Expected: registered")

    if profile.progress != 'terms_accepted':
        print("→ Redirecting to", get_next_step(request.user))
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        profile.progress = 'questionnaire1'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/questionnaire1.html')

@login_required
def questionnaire2(request):
    profile = request.user.profile
    if profile.progress != 'posttest1':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        # Save answers later, for now just advance
        profile.progress = 'questionnaire2'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/questionnaire2.html')

@login_required
def questionnaire3(request):
    profile = request.user.profile
    if profile.progress != 'posttest2':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        # Save answers later – for now just advance
        profile.progress = 'questionnaire3'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/questionnaire3.html')

@login_required
def instruction(request):
    profile = request.user.profile
    if profile.progress != 'questionnaire2':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        profile.progress = 'free_use'
        profile.free_use_started = timezone.now()
        profile.save()
        return redirect('core:dashboard')

    return render(request, 'users/instruction.html')

@login_required
def final_thankyou(request):
    profile = request.user.profile
    if profile.progress != 'questionnaire3':
        return redirect(get_next_step(request.user))

    # Mark the study as finished
    if profile.progress != 'finished':
        profile.progress = 'finished'
        profile.save()

    return render(request, 'users/final_thankyou.html')

@login_required
def terms_and_conditions(request):
    profile = request.user.profile

    if profile.progress != 'registered':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'agree':
            profile.progress = 'terms_accepted'
            profile.save()
            return redirect(get_next_step(request.user))

        elif action == 'disagree':
            user = request.user
            logout(request)
            user.delete()
            return redirect('users:study_declined')

    return render(request, 'users/terms.html')

def study_declined(request):
    return render(request, 'users/study_declined.html')

@login_required
def pretest_explanation(request):
    profile = request.user.profile

    if profile.progress != 'questionnaire1':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        profile.progress = 'pretest_explanation'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/pretest_explanation.html')

@login_required
def post_pretest_explanation(request):
    profile = request.user.profile
    if profile.progress != 'pretest':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        profile.progress = 'post_pretest_explanation'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/post_pretest_explanation.html')

@login_required
def pre_posttest_explanation(request):
    profile = request.user.profile

    if profile.progress != 'training1':
        return redirect(get_next_step(request.user))

    if request.method == 'POST':
        profile.progress = 'pre_posttest_explanation'
        profile.save()
        return redirect(get_next_step(request.user))

    return render(request, 'users/pre_posttest_explanation.html')