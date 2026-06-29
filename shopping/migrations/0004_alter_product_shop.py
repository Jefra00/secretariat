import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('shopping', '0003_shop_boutique'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE shopping_product ALTER COLUMN shop_id DROP NOT NULL; "
                "UPDATE shopping_product SET shop_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
            ),
        ),
    ]
