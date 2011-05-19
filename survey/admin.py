from walkboston.survey.models import School, Survey, Child, District
# from django.contrib import admin
from django.contrib.gis import admin

class DistrictAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class SchoolAdmin(admin.GeoModelAdmin):
    fieldsets = [
        (None, 
            {'fields': ['name', 'slug', 'survey_active', 'district', 'survey_incentive']}),
        ('School Database Attributes', 
            {'fields': ['school_id', 'address', 'municipality', 'state', 'zip', 'principal', 'phone', 'fax', 'grades', 'type']}),
        ('Map',
            {'fields': ['location', ]}),
    ]    
    list_filter = ['survey_active']
    list_display = ('name', 'survey_count', 'municipality', 'grades', 'principal','phone',)
    search_fields = ['name', 'municipality']
    ordering = ['municipality']
    prepopulated_fields = {'slug': ('name',)}
    
    def survey_count(self, obj):
        return obj.survey_set.count()
    
class SurveyAdmin(admin.GeoModelAdmin):
    list_display = ('pk','school')
    search_fields = ['school__name']

class ChildAdmin(admin.ModelAdmin):
    list_display = ('pk','survey')

admin.site.register(District, DistrictAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Child, ChildAdmin)