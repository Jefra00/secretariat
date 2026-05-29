from django.urls import path
from . import views

app_name = "company"

urlpatterns = [
    path("", views.company_list, name="company_list"),
    path("<int:pk>/", views.company_detail, name="company_detail"),
    path("ajouter/", views.company_create, name="company_create"),
    path("<int:pk>/toggle/", views.company_toggle_status, name="company_toggle_status"),
    path("<int:company_id>/ajouter-service/", views.add_company_service, name="add_company_service"),
    path("services/", views.company_service_list, name="company_service_list"),
]
