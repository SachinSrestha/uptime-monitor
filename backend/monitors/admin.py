from django.contrib import admin
from .models import Organization, Membership, Monitor, CheckResult, Incident, AlertChannel

admin.site.register(Organization)
admin.site.register(Membership)
admin.site.register(Monitor)
admin.site.register(CheckResult)
admin.site.register(Incident)
admin.site.register(AlertChannel)
