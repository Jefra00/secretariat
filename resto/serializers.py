from rest_framework import serializers
from .models import Dish, Ingredient, Category, DishIngredient,Restaurant, RestaurantImage


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "price_delta", "time_minutes_delta", "is_allergen"]


class DishIngredientWriteSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    default_included = serializers.BooleanField(required=False, default=False)
    price_override = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    time_minutes_override = serializers.IntegerField(required=False, allow_null=True)


class DishSerializer(serializers.ModelSerializer):
    ingredients = DishIngredientWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Dish
        fields = [
            "title",
            "slug",
            "short_description",
            "description",
            "image",
            "base_price",
            "base_time_minutes",
            "category",
            "ingredients",
        ]


    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients", [])
        dish = Dish.objects.create(**validated_data)

        for ing in ingredients_data:
            DishIngredient.objects.create(
                dish=dish,
                ingredient_id=ing["ingredient_id"],
                default_included=ing.get("default_included", False),
                price_override=ing.get("price_override"),
                time_minutes_override=ing.get("time_minutes_override")
            )

        return dish

class RestaurantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantImage
        fields = ['image', 'type_image', 'titre']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'price_delta', 'time_minutes_delta', 'is_allergen']

class DishSerializer1(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Dish
        fields = [
            'id', 'title', 'short_description', 'description', 'image',
            'base_price', 'base_time_minutes', 'category', 'category_name', 'ingredients'
        ]
        extra_kwargs = {
            'base_price': {'source': 'base_price'},
            'base_time_minutes': {'source': 'base_time_minutes'},
        }

class RestaurantDetailSerializer(serializers.ModelSerializer):
    banners = serializers.SerializerMethodField()
    dishes = DishSerializer1(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            'id', 'nom', 'description', 'type_cuisine', 'adresse', 'ville', 'code_postal',
            'pays', 'latitude', 'longitude', 'telephone', 'email', 'site_web', 'photo_principale',
            'banners', 'dishes'
        ]

    def get_banners(self, obj):
        # On prend uniquement les 3 premières images de type banner
        banners = obj.images.filter(type_image='banner')[:3]
        return [b.image for b in banners]
