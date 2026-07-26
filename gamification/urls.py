from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('badges/', views.badges_view, name='badges'),
    path('streaks/', views.streaks_view, name='streaks'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),  # Optional
]