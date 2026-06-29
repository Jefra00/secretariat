from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0020_restaurant_est_ouvert'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_lat',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_lng',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True),
        ),
    ]
