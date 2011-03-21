from survey.models import School, Survey, Child
# from django.contrib import admin
from django.contrib.gis import admin

class SchoolAdmin(admin.GeoModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(School, SchoolAdmin)