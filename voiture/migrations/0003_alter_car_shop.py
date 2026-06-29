import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boutique', '0001_initial'),
        ('voiture', '0002_carcategory_alter_car_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE voiture_car ALTER COLUMN shop_id DROP NOT NULL; "
                "UPDATE voiture_car SET shop_id = NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='car',
            name='shop',
            field=models.ForeignKey(
                'boutique.boutique',
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='voiture',
                verbose_name='Agence / Propriétaire',
            ),
        ),
    ]
