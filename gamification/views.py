from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def badges_view(request):
    # Placeholder
    return render(request, 'gamification/badges.html', {'badges': []})

@login_required
def streaks_view(request):
    return render(request, 'gamification/streaks.html')

@login_required
def leaderboard(request):
    return render(request, 'gamification/leaderboard.html')