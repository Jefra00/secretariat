import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('perruque', '0002_wigproduct_promo_debut_wigproduct_promo_fin'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE perruque_wigproduct ALTER COLUMN shop_id DROP NOT NULL; "
                "UPDATE perruque_wigproduct SET shop_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='wigproduct',
            name='shop',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='product',
            ),
        ),
    ]
