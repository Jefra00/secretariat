from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0019_seed_types_cuisine'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='est_ouvert',
            field=models.BooleanField(default=True, verbose_name='Ouvert'),
        ),
    ]
