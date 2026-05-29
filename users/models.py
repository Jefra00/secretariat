from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = [
        ('client', 'Client'),
        ('admin', 'Administrateur'),
        ('employe', 'Employé'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='client')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    langue = models.CharField(max_length=5, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')
    pays = models.CharField(max_length=100, blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)
    statut = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_client(self):
        return self.role == 'client'

    def is_employe(self):
        return self.role == 'employe'

    def is_admin(self):
        return self.role == 'admin'

    def total_commandes(self):
        from orders.models import Order
        return Order.objects.filter(client=self).count()

    def save(self, *args, **kwargs):
        if self.telephone:
            self.telephone = self.telephone.replace(" ", "").replace("-", "")
        self.username = self.username.lower()
        super().save(*args, **kwargs)
    
    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return static('images/default-avatar.png')

    class Meta:
        ordering = ['-date_inscription']
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
