from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    RegisterView, MonitorListCreateView, MonitorDetailView,
    MonitorResultsView, MonitorUptimeView, IncidentListView,
    AlertChannelListCreateView, AlertChannelDetailView, AlertChannelTestView, AddOrgMemberView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", obtain_auth_token),
    
    path("member/add", AddOrgMemberView.as_view()),
    
    path("monitors/", MonitorListCreateView.as_view()),
    path("monitors/<int:monitor_id>/", MonitorDetailView.as_view()),
    path("monitors/<int:monitor_id>/results/", MonitorResultsView.as_view()),
    path("monitors/<int:monitor_id>/uptime/", MonitorUptimeView.as_view()),
    
    path("incidents/", IncidentListView.as_view()),
    
    path("alert-channels/",AlertChannelListCreateView.as_view()),
    path("alert-channels/<int:channel_id>/",AlertChannelDetailView.as_view()),
    path("alert-channels/<int:channel_id>/test/",AlertChannelTestView.as_view()),
]
