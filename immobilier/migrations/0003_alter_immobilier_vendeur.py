import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('immobilier', '0002_immobiliercategory_alter_immobilier_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE immobilier_immobilier ALTER COLUMN vendeur_id DROP NOT NULL; "
                "UPDATE immobilier_immobilier SET vendeur_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='immobilier',
            name='vendeur',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='biens',
                verbose_name='Agence / Propriétaire',
            ),
        ),
    ]
