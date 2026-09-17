from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status,permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
import requests
from .models import Membership, Monitor, Incident, AlertChannel
from .serializers import (
    RegisterSerializer, MonitorSerializer, CheckResultSerializer,
    IncidentSerializer, AlertChannelSerializer, AddOrgMemberSerializer
)
# from .tasks import send_alert

def _parse_since(param, default_hours=24):
    if not param:
        return timezone.now() - timedelta(hours=default_hours)
    unit = param[-1]
    value = int(param[:-1])
    if unit == "h":
        return timezone.now() - timedelta(hours=value)
    if unit == "d":
        return timezone.now() - timedelta(days=value)
    return timezone.now() - timedelta(hours=default_hours)


def _user_org(request):
    membership = Membership.objects.filter(user=request.user).select_related("organization").first()
    return membership.organization if membership else None


def _get_org_monitor(request, monitor_id):
    org = _user_org(request)
    return get_object_or_404(Monitor, id=monitor_id, organization=org)

def _get_org_alert_channel(request, channel_id):
    org = _user_org(request)
    return get_object_or_404(AlertChannel, id=channel_id, organization=org)



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self,request):
        serializer = RegisterSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)
    
class AddOrgMemberView(APIView):
    def post(self, request):
        org = _user_org(request)
        serializer = AddOrgMemberSerializer(data=request.data,context={"organization": org})
        serializer.is_valid(raise_exception=True)
        result= serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
class MonitorListCreateView(APIView):
    def get(self, request):
        org = _user_org(request)
        monitors = Monitor.objects.filter(organization=org).order_by("-created_at")
        return Response(MonitorSerializer(monitors, many=True).data)
    
    def post(self, request):
        org = _user_org(request)
        if org is None:
            return Response({"detail":"No organization found"}, status=400)
        serializer=MonitorSerializer(data=request.data, context={"organization":org})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MonitorDetailView(APIView):
    def get(self, request,monitor_id):
        monitor = _get_org_monitor(request, monitor_id)
        return Response(MonitorSerializer(monitor).data)
    
    def patch(self, request, monitor_id):
        monitor = _get_org_monitor(request, monitor_id)
        serializer = MonitorSerializer(monitor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def delete(self, request, monitor_id):
        monitor = _get_org_monitor(request, monitor_id)
        monitor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class MonitorResultsView(APIView):
    def get(self,request,monitor_id):
        monitor = _get_org_monitor(request, monitor_id)
        since = _parse_since(request.query_params.get("since","24h"))
        results = monitor.results.filter(checked_at__gte=since)
        return Response(CheckResultSerializer(results,many=True).data)
    

class MonitorUptimeView(APIView):
    def get(self, request, monitor_id):
        monitor = _get_org_monitor(request, monitor_id)
        since = _parse_since(request.query_params.get("period", "30d"), default_hours=30 * 24)
        results = monitor.results.filter(checked_at__gte=since)
        total = results.count()
        if total == 0:
            return Response({"uptime_percentage": None})
        successes = results.filter(is_success=True).count()
        return Response({"uptime_percentage": round((successes / total) * 100, 2)})
    
class IncidentListView(APIView):
    def get(self, request):
        org = _user_org(request)
        qs = Incident.objects.filter(monitor__organization=org) if org else Incident.objects.none()

        resolved = request.query_params.get("resolved")
        if resolved == "true":
            qs = qs.exclude(resolved_at__isnull=True)
        elif resolved == "false":
            qs = qs.filter(resolved_at__isnull=True)

        monitor_id = request.query_params.get("monitor")
        if monitor_id:
            qs = qs.filter(monitor_id=monitor_id)

        return Response(IncidentSerializer(qs, many=True).data)


class AlertChannelListCreateView(APIView):
    def get(self, request):
        org = _user_org(request)
        channels = AlertChannel.objects.filter(organization=org) if org else AlertChannel.objects.none()
        return Response(AlertChannelSerializer(channels, many=True).data)

    def post(self, request):
        org = _user_org(request)
        if org is None:
            return Response({"detail": "No organization found for this user."}, status=400)
        serializer = AlertChannelSerializer(data=request.data, context={"organization": org})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AlertChannelDetailView(APIView):
    def delete(self, request, channel_id):
        channel = _get_org_alert_channel(request, channel_id)
        channel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlertChannelTestView(APIView):
    def post(self, request, channel_id):
        channel = _get_org_alert_channel(request, channel_id)
        message = f"Test alert from {channel.organization.name} — this channel is working."
        if channel.channel_type == "email":
            send_mail("Uptime Monitor test alert", message, None, [channel.destination])
        elif channel.channel_type == "slack":
            requests.post(channel.destination, json={"text": message}, timeout=5)
        return Response({"status": "sent"})