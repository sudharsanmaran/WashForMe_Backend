from rest_framework import serializers

from core.models import Shop, Review


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class ShopReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['created_at', 'updated_at', 'user']
        read_only_fields = ['id']
