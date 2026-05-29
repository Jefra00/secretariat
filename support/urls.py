# support/urls.py
from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("liste/", views.liste_tickets, name="liste_tickets"),
    path("nouveau/", views.nouveau_ticket, name="nouveau_ticket"),
    path("<str:reference>/", views.details_ticket, name="details_ticket"),
]
