from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),  # Main landing after login
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('account-deleted/', views.account_deleted, name='account_deleted'),
    path('questionnaire1/', views.questionnaire1, name='questionnaire1'),
    path('questionnaire2/', views.questionnaire2, name='questionnaire2'),
    path('questionnaire3/', views.questionnaire3, name='questionnaire3'),
    path('instruction/', views.instruction, name='instruction'),
    path('final-thankyou/', views.final_thankyou, name='final_thankyou'),
]
