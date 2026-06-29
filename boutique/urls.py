from django.urls import path
from . import views

urlpatterns = [
    # ── Admin : géographie ──────────────────────────────────────────────────
    path('admin-panel/geo/',                    views.admin_geo,              name='admin_geo'),
    path('admin-panel/geo/villes/',             views.admin_villes,           name='admin_villes'),
    path('admin-panel/geo/communes/',           views.admin_communes,         name='admin_communes'),
    path('admin-panel/geo/quartiers/',          views.admin_quartiers,        name='admin_quartiers'),
    path('admin-panel/geo/marches/',            views.admin_marches,          name='admin_marches'),

    # ── Admin : boutiques ───────────────────────────────────────────────────
    path('admin-panel/boutiques-geo/',              views.admin_boutiques_list,   name='admin_boutiques_list'),
    path('admin-panel/boutiques-geo/creer/',        views.admin_boutique_creer,   name='admin_boutique_creer'),
    path('admin-panel/boutiques-geo/<int:pk>/modifier/', views.admin_boutique_modifier, name='admin_boutique_modifier'),
    path('admin-panel/boutiques-geo/<int:pk>/toggle/',   views.admin_boutique_toggle,   name='admin_boutique_toggle'),

    # ── Vendeur : ses boutiques ──────────────────────────────────────────────
    path('vendeur/boutiques/',            views.vendeur_mes_boutiques,  name='vendeur_mes_boutiques'),
    path('vendeur/boutiques/creer/',      views.vendeur_boutique_creer, name='vendeur_boutique_creer'),
    path('vendeur/boutiques/<int:pk>/modifier/', views.vendeur_boutique_modifier, name='vendeur_boutique_modifier'),

    # ── AJAX ─────────────────────────────────────────────────────────────────
    path('ajax/communes/<int:ville_id>/',   views.communes_par_ville,    name='communes_par_ville'),
    path('ajax/quartiers/<int:commune_id>/', views.quartiers_par_commune, name='quartiers_par_commune'),
    path('ajax/marches/<int:commune_id>/',   views.marches_par_commune,   name='marches_par_commune'),
]
