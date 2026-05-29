from django.urls import path
from . import views

app_name = "elearning"

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('cours/<int:pk>/', views.course_detail, name='course_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('inscrire/<int:course_id>/', views.inscrire_course, name='inscrire_course'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('certificat/<int:enrollment_id>/', views.telecharger_certificat, name='telecharger_certificat'),
]
