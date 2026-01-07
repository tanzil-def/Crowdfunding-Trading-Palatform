from django.urls import path
from .views import (
    FavoriteCreateView,
    FavoriteListView,
    FavoriteDeleteView
)

urlpatterns = [
    path('', FavoriteCreateView.as_view()),
    path('list/', FavoriteListView.as_view()),
    path('<uuid:id>/', FavoriteDeleteView.as_view()),
]
