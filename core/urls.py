from django.urls import path

from .views import (
    HomeView,
    contact_submit_api,
    profile_detail_api,
    site_visit_duration_api,
    social_links_api,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('api/profile/', profile_detail_api, name='profile_detail_api'),
    path('api/social-links/', social_links_api, name='social_links_api'),
    path('api/contact/submit/', contact_submit_api, name='contact_submit_api'),
    path('api/site-visit/duration/', site_visit_duration_api, name='site_visit_duration_api'),
]
