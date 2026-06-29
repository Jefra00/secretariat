from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0017_livreurprofile_location_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypeCuisine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('ordre', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Type de cuisine',
                'verbose_name_plural': 'Types de cuisine',
                'ordering': ['ordre', 'nom'],
            },
        ),
        migrations.AddField(
            model_name='restaurant',
            name='types_cuisine',
            field=models.ManyToManyField(
                blank=True,
                related_name='restaurants',
                to='resto.TypeCuisine',
                verbose_name='Types de cuisine',
            ),
        ),
    ]
