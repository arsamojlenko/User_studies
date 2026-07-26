from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    # path('start/<str:session_type>/', views.start_session, name='start_session'),
    path('submit/<int:session_id>/', views.submit_session, name='submit_session'),
    path('start/', views.start_training_page, name='start_training_page'),
    path('begin/', views.begin_training, name='begin_training'),
    path('session/<int:session_id>/', views.training_session, name='training_session'),
    path('stop/<int:session_id>/', views.stop_training, name='stop_training'),
    path('session/<int:session_id>/answer/', views.submit_answer, name='submit_answer'),
    path('pretest/', views.pretest, name='pretest'),
    path('posttest1/', views.posttest1, name='posttest1'),
    path('posttest2/', views.posttest2, name='posttest2'),
]