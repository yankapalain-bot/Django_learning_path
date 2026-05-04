from django.contrib import admin
from district.models import Doctor, Hospital, Patient

admin.site.register(Hospital)
admin.site.register(Doctor)
admin.site.register(Patient)