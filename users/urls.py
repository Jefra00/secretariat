from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .views import PhoneTokenObtainPairView

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription_client, name='inscription_client'),
    path('connexion/', views.connexion_client, name='connexion_client'),
    path('deconnexion/', views.deconnexion_client, name='deconnexion_client'),
    path('espace/', views.espace_client, name='espace_client'),
    path('espace_admin/', views.espace_admin, name='espace_admin'),
    path('comptes/', views.comptes, name='comptes'),
    path('completer_compte/', views.creer_ou_completer_compte, name='completer_compte'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('apropo/', views.apropos, name='apropo'),
    path('marche/', include('marche.urls', namespace='marche')),
    path('shopping/', include('shopping.urls', namespace='shopping')),
    path('perruque/', include('perruque.urls', namespace='perruque')),
    path('location/', include('location.urls', namespace='location')),
    path('voiture/', include('voiture.urls', namespace='voiture')),
    path('immobilier/', include('immobilier.urls', namespace='immobilier')),
    path('quicaillerie/', include('quicaillerie.urls', namespace='quicaillerie')),
    path('resto/', include('resto.urls')),
    path("auth/registere/", views.registere_user),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/login/", PhoneTokenObtainPairView.as_view()),
    path("auth/me/", views.me),
    path("auth/my-orders/", views.my_orders),
    path("auth/fcm-token/", views.save_fcm_token),
    path('api/', views.api, name='api'),

    # ── Géolocalisation ───────────────────────────────────────────────────────
    path('api/update-location/',                        views.update_location,        name='update-location'),

    # ── Admin : suivi positions temps réel ───────────────────────────────────
    path('admin-panel/positions/',                      views.admin_positions,        name='admin_positions'),
    path('admin-panel/api/positions/',                  views.api_positions,          name='api_positions'),
    path('admin-panel/api/positions/<int:user_id>/trail/', views.api_position_trail, name='api_position_trail'),

    # ── Interface Web Livreur ─────────────────────────────────────────────────
    path('connexion/livreur/', views.livreur_connexion, name='livreur_connexion'),
    path('inscription/livreur/', views.livreur_inscription, name='livreur_inscription'),
    path('livreur/dashboard/', views.livreur_dashboard,  name='livreur_dashboard'),
    path('livreur/profil/',    views.livreur_profil,     name='livreur_profil'),
    path('livreur/reserver/<int:order_id>/', views.livreur_reserver_web, name='livreur_reserver'),
    path('livreur/deconnexion/', views.livreur_deconnexion, name='livreur_deconnexion'),

    # ── Interface Web Vendeur ─────────────────────────────────────────────────
    path('vendeur/connexion/',                      views.vendeur_connexion,         name='vendeur_connexion'),
    path('vendeur/deconnexion/',                    views.vendeur_deconnexion,        name='vendeur_deconnexion'),
    path('vendeur/dashboard/',                      views.vendeur_dashboard,          name='vendeur_dashboard'),
    path('vendeur/commandes/',                      views.vendeur_commandes,          name='vendeur_commandes'),
    path('vendeur/boutiques/',                      views.vendeur_boutiques,          name='vendeur_boutiques'),
    path('vendeur/boutiques/switch/<int:pk>/',      views.vendeur_switch_boutique,    name='vendeur_switch_boutique'),
    path('vendeur/produits/',                       views.vendeur_produits,           name='vendeur_produits'),
    path('vendeur/produits/ajouter/',               views.vendeur_ajouter_produit,    name='vendeur_ajouter_produit'),
    path('vendeur/produits/<str:section>/<str:pk>/detail/',    views.vendeur_detail_produit,    name='vendeur_detail_produit'),
    path('vendeur/produits/<str:section>/<str:pk>/modifier/',  views.vendeur_modifier_produit,  name='vendeur_modifier_produit'),
    path('vendeur/produits/<str:section>/<str:pk>/images/',    views.vendeur_images_produit,    name='vendeur_images_produit'),
    path('vendeur/produits/<str:section>/<str:pk>/supprimer/', views.vendeur_supprimer_produit, name='vendeur_supprimer_produit'),
    path('vendeur/profil/',                         views.vendeur_profil,             name='vendeur_profil'),
    path('vendeur/paiements/',                      views.vendeur_paiements,          name='vendeur_paiements'),
    path('vendeur/paiements/<int:pk>/',             views.vendeur_paiement_detail,    name='vendeur_paiement_detail'),

    # ── Admin : créer un vendeur ──────────────────────────────────────────────
    path('admin-panel/creer-vendeur/',               views.admin_creer_vendeur,        name='admin_creer_vendeur'),

    # ── Admin Panel complet ───────────────────────────────────────────────────
    path('admin-panel/',                            views.admin_panel_dashboard,      name='admin_panel_dashboard'),
    path('admin-panel/utilisateurs/',               views.admin_panel_utilisateurs,   name='admin_panel_utilisateurs'),
    path('admin-panel/vendeurs/',                   views.admin_panel_vendeurs,        name='admin_panel_vendeurs'),
    path('admin-panel/commandes/',                  views.admin_panel_commandes,       name='admin_panel_commandes'),
    path('admin-panel/boutiques/',                  views.admin_panel_boutiques,       name='admin_panel_boutiques'),
    path('admin-panel/livreurs/',                   views.admin_panel_livreurs,        name='admin_panel_livreurs'),

    # ── Admin Panel — Produits ────────────────────────────────────────────────
    path('admin-panel/produits/',              views.admin_produits_hub,          name='admin_produits_hub'),
    path('admin-panel/produits/marche/',       views.admin_produits_marche,       name='admin_produits_marche'),
    path('admin-panel/produits/shopping/',     views.admin_produits_shopping,     name='admin_produits_shopping'),
    path('admin-panel/produits/perruque/',     views.admin_produits_perruque,     name='admin_produits_perruque'),
    path('admin-panel/produits/quicaillerie/', views.admin_produits_quicaillerie, name='admin_produits_quicaillerie'),
    path('admin-panel/produits/voiture/',      views.admin_produits_voiture,      name='admin_produits_voiture'),
    path('admin-panel/produits/immobilier/',   views.admin_produits_immobilier,   name='admin_produits_immobilier'),

    # ── Paiement / Checkout ───────────────────────────────────────────────────
    path('paiement/',                               views.paiement_checkout,          name='paiement_checkout'),
    path('paiement/confirmation/<int:pk>/',         views.paiement_confirmation,      name='paiement_confirmation'),
    path('paiement/suivi/<int:pk>/',                views.suivi_livraison,            name='suivi_livraison'),
    path('paiement/suivi/<int:pk>/position/',       views.suivi_position_api,         name='suivi_position_api'),

    # ── Livreur — missions ────────────────────────────────────────────────────
    path('livreur/missions/',                       views.livreur_mes_missions,       name='livreur_mes_missions'),
    path('livreur/missions/<int:pk>/',              views.livreur_mission_detail,     name='livreur_mission_detail'),
    path('livreur/missions/<int:pk>/accepter/',     views.livreur_accepter_mission,   name='livreur_accepter_mission'),
    path('livreur/missions/<int:pk>/statut/',       views.livreur_maj_statut,         name='livreur_maj_statut'),
    path('livreur/missions/<int:pk>/otp/',          views.livreur_valider_otp,        name='livreur_valider_otp'),
    path('livreur/missions/<int:pk>/map-api/',      views.livreur_mission_map_api,    name='livreur_mission_map_api'),
    path('livreur/position/',                       views.livreur_update_position,    name='livreur_update_position'),

    # ── Vendeur — statut préparation ──────────────────────────────────────────
    path('vendeur/commandes/<int:pk>/preparation/', views.vendeur_marquer_commande,   name='vendeur_marquer_commande'),
    path('paiement/<int:pk>/assigner-livreur/',    views.assigner_livreur_page,      name='assigner_livreur_page'),
    path('paiement/<int:pk>/livreurs-proches/',    views.api_livreurs_proches,        name='api_livreurs_proches'),

    # ── Espace Client (profil + commandes) ────────────────────────────────────
    path('client/profil/',                          views.client_profil,              name='client_profil'),
    path('client/commandes/',                       views.client_commandes,           name='client_commandes'),
    path('client/commandes/<int:pk>/',              views.client_commande_detail,     name='client_commande_detail'),

    # ── API Mobile — Checkout générique ──────────────────────────────────────
    path('api/paiement/creer/',                     views.api_paiement_creer,         name='api_paiement_creer'),

    # ── API Mobile — Client ───────────────────────────────────────────────────
    path('api/client/commandes/',                   views.api_client_commandes,       name='api_client_commandes'),

    # ── API Mobile — Livreur ──────────────────────────────────────────────────
    path('api/livreur/livraisons/',                 views.api_livreur_livraisons,     name='api_livreur_livraisons'),
    path('api/livreur/livraisons/<int:pk>/accepter/', views.api_livreur_accepter,     name='api_livreur_accepter'),
    path('api/livreur/livraisons/<int:pk>/statut/', views.api_livreur_statut,         name='api_livreur_statut'),
    path('api/livreur/livraisons/<int:pk>/map/',    views.api_livreur_mission_map,    name='api_livreur_mission_map'),
    path('api/livreur/livraisons/<int:pk>/otp/',    views.api_livreur_valider_otp,    name='api_livreur_valider_otp'),

    # ── AJAX polling ─────────────────────────────────────────────────────────
    path('api/livreur/missions-poll/',              views.api_livreur_missions_poll,  name='api_livreur_missions_poll'),
    path('api/vendeur/commandes-poll/',             views.api_vendeur_commandes_poll, name='api_vendeur_commandes_poll'),
]
