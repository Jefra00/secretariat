from django.db import migrations

TYPES = [
    (1,  'Congolaise'),
    (2,  'Africaine'),
    (3,  'Fast-food'),
    (4,  'Grillades'),
    (5,  'Poissons & fruits de mer'),
    (6,  'Pizzeria'),
    (7,  'Burgers'),
    (8,  'Poulet & volailles'),
    (9,  'Cuisine de rue'),
    (10, 'Végétarienne'),
    (11, 'Libanaise'),
    (12, 'Asiatique'),
    (13, 'Italienne'),
    (14, 'Française'),
    (15, 'Camerounaise'),
    (16, 'Sénégalaise'),
    (17, 'Ivoirienne'),
    (18, 'Internationale'),
    (19, 'Boulangerie & Pâtisserie'),
    (20, 'Autre'),
]


def seed_types(apps, schema_editor):
    TypeCuisine = apps.get_model('resto', 'TypeCuisine')
    for ordre, nom in TYPES:
        TypeCuisine.objects.get_or_create(nom=nom, defaults={'ordre': ordre})


def unseed_types(apps, schema_editor):
    TypeCuisine = apps.get_model('resto', 'TypeCuisine')
    TypeCuisine.objects.filter(nom__in=[n for _, n in TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('resto', '0018_typecuisine_restaurant_types_cuisine'),
    ]

    operations = [
        migrations.RunPython(seed_types, reverse_code=unseed_types),
    ]
