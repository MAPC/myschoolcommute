from survey.models import School, Survey, Child, District
# from django.contrib import admin
from django.contrib.gis import admin

class SchoolAdmin(admin.GeoModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    
class SurveyAdmin(admin.GeoModelAdmin):
    list_display = ('pk','school')

class ChildAdmin(admin.ModelAdmin):
    list_display = ('pk','survey')

admin.site.register(District)
admin.site.register(School, SchoolAdmin)
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Child, ChildAdmin)