from django.contrib import admin
from .models import ExtractedRelation, Source

# Register your models here.
admin.site.register(ExtractedRelation)
admin.site.register(Source)