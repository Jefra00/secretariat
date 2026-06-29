import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('quicaillerie', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE quicaillerie_produitquincaillerie ALTER COLUMN boutique_id DROP NOT NULL; "
                "UPDATE quicaillerie_produitquincaillerie SET boutique_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='produitquincaillerie',
            name='boutique',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='produits_quincaillerie',
            ),
        ),
    ]
