from django import forms
from django.contrib.gis.geos import GEOSGeometry
from .models import Ville, Commune, Quartier


class _GeoMixin:
    """Mixin: parse position_json / contour_json → PostGIS objects."""

    def _apply_geo(self, instance):
        pos     = self.cleaned_data.get('position_json', '').strip()
        contour = self.cleaned_data.get('contour_json', '').strip()
        if pos:
            instance.position = GEOSGeometry(pos, srid=4326)
        if contour:
            instance.contour = GEOSGeometry(contour, srid=4326)
        return instance

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._apply_geo(instance)
        if commit:
            instance.save()
        return instance


class VilleForm(_GeoMixin, forms.ModelForm):
    position_json = forms.CharField(required=False, widget=forms.HiddenInput)
    contour_json  = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model  = Ville
        fields = ['nom', 'pays', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Ex : Brazzaville'}),
            'pays': forms.TextInput(attrs={'placeholder': 'Ex : Congo'}),
        }


class CommuneForm(_GeoMixin, forms.ModelForm):
    position_json = forms.CharField(required=False, widget=forms.HiddenInput)
    contour_json  = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model  = Commune
        fields = ['nom', 'ville', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Ex : Bacongo'}),
        }


class QuartierForm(_GeoMixin, forms.ModelForm):
    position_json = forms.CharField(required=False, widget=forms.HiddenInput)
    contour_json  = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model  = Quartier
        fields = ['nom', 'commune', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Ex : Plateau des 15 ans'}),
        }
