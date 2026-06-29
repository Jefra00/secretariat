"""
Context processor vendeur : injecte `active_boutique` et `boutiques_list`
dans tous les templates rendu par un utilisateur de rôle vendeur.
Permet au switcher de boutique dans la sidebar d'être disponible partout
sans avoir à modifier chaque vue individuellement.
"""
from boutique.models import Boutique

_TYPE_ICONS = {
    'marche':        '🛒',
    'shopping':      '🛍️',
    'quincaillerie': '🔨',
    'perruque':      '💇',
    'voiture':       '🚗',
    'immobilier':    '🏠',
    'restaurant':    '🍽️',
    'electronique':  '📱',
    'mode':          '👗',
    'pharmacie':     '💊',
    'elevage':       '🐄',
}


def vendeur_boutique(request):
    """
    Injecte dans le contexte template :
      - active_boutique : la boutique sélectionnée en session (ou la 1ère par défaut)
      - boutiques_list  : toutes les boutiques du vendeur (pour le switcher)
    Ne s'exécute que pour les vendeurs authentifiés.
    """
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, 'role', None) not in ('vendeur', 'admin'):
        return {}

    try:
        boutiques = list(Boutique.objects.filter(user=request.user).order_by('nom'))
        if not boutiques:
            return {'active_boutique': None, 'boutiques_list': []}

        # Enrichir chaque boutique avec son icône de type
        for b in boutiques:
            b.type_icon = _TYPE_ICONS.get(b.type_commerce, '🏪')

        # Résoudre la boutique active depuis la session
        bid = request.session.get('active_boutique_id')
        active = None
        if bid is not None:
            active = next((b for b in boutiques if b.pk == int(bid)), None)
        if active is None:
            active = boutiques[0]

        return {
            'active_boutique': active,
            'boutiques_list': boutiques,
        }
    except Exception:
        return {}
