import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('marche', '0006_vendeur_boutique'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE marche_produit ALTER COLUMN vendeur_id DROP NOT NULL; "
                "UPDATE marche_produit SET vendeur_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='produit',
            name='vendeur',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='produits',
            ),
        ),
    ]
