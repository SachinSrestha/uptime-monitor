from rest_framework import permissions
from .models import Membership

class IsOrgMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        org = getattr(obj,"organization", None) or getattr(obj.monitor, "organization", None)
        return Membership.objects.filter(organization=org, user =request.user).exists()