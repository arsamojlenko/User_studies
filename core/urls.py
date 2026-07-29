from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),                    # Optional landing page
    path('dashboard/', views.researcher_dashboard, name='dashboard'),      # Smart dashboard
    path('my-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('export/', views.export_data, name='export_data'),  # CSV export
    path('participants/', views.participant_list, name='participant_list'),
    #path('questionnaires/', views.questionnaire_list, name='questionnaires'),
    path('export/', views.export_data, name='export_data'),
    path('export-questionnaires/', views.export_questionnaires, name='export_questionnaires'),
]