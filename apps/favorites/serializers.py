from rest_framework import serializers
from .models import Favorite

class FavoriteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'project', 'created_at')
        read_only_fields = ('id', 'created_at')


class FavoriteListSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title')
    project_category = serializers.CharField(source='project.category')

    class Meta:
        model = Favorite
        fields = (
            'id',
            'project',
            'project_title',
            'project_category',
            'created_at'
        )
