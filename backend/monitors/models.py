from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug= models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    

class Membership(models.Model):
    ROLE_CHOICES = [("owner","Owner"), ("member","Member")]
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default="member")
    
    class Meta:
        unique_together = ("organization", "user")
        
    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"
    
    
class Monitor(models.Model):
    STATUS_CHOICES = [("up","Up"),("suspicious","Suspicious"),("down","Down")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="monitors")
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=2000)
    check_interval_seconds = models.PositiveIntegerField(default=300)
    expected_status_code= models.PositiveSmallIntegerField(default=200)
    timeout_seconds = models.PositiveSmallIntegerField(default=10)
    consecutive_failure_threshold = models.PositiveSmallIntegerField(default=3)
    current_status= models.CharField(max_length=20, choices=STATUS_CHOICES, default="up")
    consecutive_failures= models.PositiveSmallIntegerField(default=0)
    is_active= models.BooleanField(default=True)
    next_check_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class CheckResult(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="results")
    checked_at = models.DateTimeField(db_index=True)
    response_time_ms = models.PositiveIntegerField(null=True)
    status_code = models.PositiveSmallIntegerField(null=True)
    is_success = models.BooleanField()
    error_message = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-checked_at"]


class Incident(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="incidents")
    started_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    cause_summary = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-started_at"]


class AlertChannel(models.Model):
    CHANNEL_CHOICES = [("email", "Email"), ("slack", "Slack Webhook")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="alert_channels")
    channel_type = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    destination = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.channel_type}: {self.destination}"