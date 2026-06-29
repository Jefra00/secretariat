from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0015_dishrating'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LivreurProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matricule_moto', models.CharField(max_length=50)),
                ('photo_url', models.CharField(blank=True, max_length=500)),
                ('latitude', models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('disponible', models.BooleanField(default=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='livreur_profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='livreur',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='livraisons',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='livreur_reserved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
