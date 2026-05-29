from django import template

register = template.Library()

@register.filter
def endswith(value, suffix):
    """Permet d'utiliser 'endswith' dans les templates."""
    if not value:
        return False
    return str(value).lower().endswith(str(suffix).lower())
