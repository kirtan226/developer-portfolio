from django.urls import path

from .views import HomeView, profile_detail_api, social_links_api

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('api/profile/', profile_detail_api, name='profile_detail_api'),
    path('api/social-links/', social_links_api, name='social_links_api'),
]
