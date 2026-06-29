from django.contrib.gis.db import models


class Ville(models.Model):
    nom        = models.CharField(max_length=200, unique=True)
    pays       = models.CharField(max_length=100, default='Congo')
    position   = models.PointField(null=True, blank=True, srid=4326,
                                   help_text='Point central (centroïde)')
    contour    = models.PolygonField(null=True, blank=True, srid=4326,
                                     help_text='Délimitation exacte du territoire')
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Ville'
        verbose_name_plural = 'Villes'

    def __str__(self):
        return self.nom

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None

    @property
    def contour_geojson(self):
        return self.contour.geojson if self.contour else None

    @property
    def bbox(self):
        """Bounding box [minLng, minLat, maxLng, maxLat]"""
        if self.contour:
            ext = self.contour.extent  # (xmin, ymin, xmax, ymax)
            return {'minLng': ext[0], 'minLat': ext[1], 'maxLng': ext[2], 'maxLat': ext[3]}
        return None


class Commune(models.Model):
    nom        = models.CharField(max_length=200)
    ville      = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name='communes')
    position   = models.PointField(null=True, blank=True, srid=4326)
    contour    = models.PolygonField(null=True, blank=True, srid=4326)
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ville__nom', 'nom']
        unique_together = ['nom', 'ville']
        verbose_name = 'Commune'
        verbose_name_plural = 'Communes'

    def __str__(self):
        return f'{self.nom} ({self.ville.nom})'

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None

    @property
    def contour_geojson(self):
        return self.contour.geojson if self.contour else None

    @property
    def bbox(self):
        if self.contour:
            ext = self.contour.extent
            return {'minLng': ext[0], 'minLat': ext[1], 'maxLng': ext[2], 'maxLat': ext[3]}
        return None


class Quartier(models.Model):
    nom        = models.CharField(max_length=200)
    commune    = models.ForeignKey(Commune, on_delete=models.CASCADE, related_name='quartiers')
    position   = models.PointField(null=True, blank=True, srid=4326)
    contour    = models.PolygonField(null=True, blank=True, srid=4326)
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['commune__ville__nom', 'commune__nom', 'nom']
        unique_together = ['nom', 'commune']
        verbose_name = 'Quartier'
        verbose_name_plural = 'Quartiers'

    def __str__(self):
        return f'{self.nom} — {self.commune.nom}'

    @property
    def position_geojson(self):
        return self.position.geojson if self.position else None

    @property
    def contour_geojson(self):
        return self.contour.geojson if self.contour else None

    @property
    def bbox(self):
        if self.contour:
            ext = self.contour.extent
            return {'minLng': ext[0], 'minLat': ext[1], 'maxLng': ext[2], 'maxLat': ext[3]}
        return None
