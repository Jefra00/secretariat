from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0014_order_qr_code_order_qr_validated_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DishRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='resto.dish')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dish_ratings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('dish', 'user')},
            },
        ),
    ]
