from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # BLOG
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # NEWSLETTER
    path('newsletter/', views.newsletter_list, name='newsletter_list'),
    path('newsletter/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),
    path('subscribe/', views.subscribe, name='subscribe'),

    # NOTIFICATIONS
    path('notifications/', views.mes_notifications, name='mes_notifications'),
    path('notifications/<int:pk>/', views.lire_notification, name='lire_notification'),
]
