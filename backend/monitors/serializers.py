from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import Organization, Membership, Monitor, CheckResult, Incident, AlertChannel

class RegisterSerializer(serializers.Serializer):
    org_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,min_length=8)
    
    def validate_email(self,value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self,validated_data):
        user= User.objects.create_user(
            username = validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        base_slug = slugify(validated_data["org_name"])
        slug=base_slug
        while Organization.objects.filter(slug=slug).exists():
            n += 1
            slug = f"{base_slug}-{n}"
        org = Organization.objects.create(name=validated_data["org_name"], slug=slug)
        Membership.objects.create(organization=org, user=user, role="owner")
        token, _ = Token.objects.get_or_create(user=user)
        return {"token": token.key, "organization": org.name}
    
class AddOrgMemberSerializer(serializers.Serializer):
    username = serializers.EmailField()
    class Meta:
        model = Membership
        fields=["organization","user","role"]
        read_only_fields=["role"]
    
    def validate_username(self,value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Email doesn't exist!")
        return value
    
    def create(self, validated_data):
        validated_data["organization"]= self.context["organization"]
        return super.create(validated_data)
    
    
class MonitorSerializer(serializers.Serializer):
    class Meta:
        model = Monitor
        fields=["id", "name", "url", "check_interval_seconds", "expected_status_code",
            "timeout_seconds", "consecutive_failure_threshold", "current_status",
            "consecutive_failures", "is_active", "next_check_at", "created_at",]
        read_only_fields = ["current_status", "consecutive_failures", "next_check_at", "created_at"]
        
    def create(self, validated_data):
        validated_data["next_check_at"]= timezone.now()
        validated_data["organization"]= self.context["organization"]
        return super().create(validated_data)
    
class CheckResultSerializer(serializers.Serializer):
    class Meta:
        model = CheckResult
        fields=["id", "checked_at", "response_time_ms", "status_code", "is_success", "error_message"]
        
class IncidentSerializer(serializers.Serializer):
    monitor_name = serializers.CharField(source="monitor.name", read_only =True)
    
    class Meta:
        model = Incident
        fields=["id", "monitor", "monitor_name", "started_at", "resolved_at", "cause_summary"]
        
class AlertChannelSerializer(serializers.Serializer):
    class Meta:
        model = AlertChannel
        fields=["id", "channel_type", "destination"]
        
    def create(self, validated_data):
        validated_data["organization"]= self.context["organization"]
        return super.create(validated_data)