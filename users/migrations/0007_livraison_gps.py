from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_userpositionlog'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Champs GPS + statut préparation sur Paiement
        migrations.AddField(
            model_name='paiement',
            name='gps_lat',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True, verbose_name='GPS Latitude'),
        ),
        migrations.AddField(
            model_name='paiement',
            name='gps_lng',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True, verbose_name='GPS Longitude'),
        ),
        migrations.AddField(
            model_name='paiement',
            name='statut_preparation',
            field=models.CharField(
                choices=[('recu', 'Reçu'), ('en_preparation', 'En préparation'), ('pret', 'Prêt à livrer')],
                default='recu', max_length=20, verbose_name='Préparation',
            ),
        ),
        # Modèle Livraison
        migrations.CreateModel(
            name='Livraison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(
                    choices=[
                        ('attente_livreur', 'En attente de livreur'),
                        ('assigne',         'Livreur assigné'),
                        ('accepte',         'Accepté par le livreur'),
                        ('en_recuperation', 'En récupération'),
                        ('en_route',        'En route vers le client'),
                        ('livree',          'Livrée'),
                        ('echouee',         'Échouée'),
                    ],
                    default='attente_livreur', max_length=30,
                )),
                ('otp_code',    models.CharField(blank=True, max_length=6, verbose_name='Code OTP')),
                ('otp_valide',  models.BooleanField(default=False)),
                ('assigned_at', models.DateTimeField(blank=True, null=True)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('picked_at',   models.DateTimeField(blank=True, null=True)),
                ('delivered_at',models.DateTimeField(blank=True, null=True)),
                ('notes',       models.TextField(blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('paiement', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='livraison', to='users.paiement',
                )),
                ('livreur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='missions_livraison',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Livraison',
                'verbose_name_plural': 'Livraisons',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['statut'], name='livraison_statut_idx'),
                    models.Index(fields=['livreur', 'statut'], name='livraison_livreur_statut_idx'),
                ],
            },
        ),
    ]
