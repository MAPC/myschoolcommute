from survey.models import School, Survey, SurveySet, Child, District
# from django.contrib import admin
from django.contrib.gis import admin


class DistrictAdmin(admin.OSMGeoAdmin):
    prepopulated_fields = {'slug': ('distname',)}


class SchoolAdmin(admin.OSMGeoAdmin):
    fieldsets = [
        (None,
            {'fields': ['name', 'slug', 'districtid', 'survey_incentive']}),
        ('School Database Attributes',
            {'fields': ['schid', 'address', 'town', 'state', 'zip', 'principal', 'phone', 'fax', 'grades', 'schl_type']}),
        ('Map',
            {'fields': ['geometry', ]}),
    ]
    #list_filter = ['survey_active']
    list_display = ('name', 'survey_count', 'town', 'grades', 'principal', 'phone',)
    search_fields = ['name', 'districtid__distname']
    ordering = ['districtid__distname']
    prepopulated_fields = {'slug': ('name',)}

    def survey_count(self, obj):
        return obj.survey_set.count()


class SurveyAdmin(admin.OSMGeoAdmin):
    list_display = (
        'pk', 'school', 'location', 'distance', 'user', 'created', 'modified',
    )
    search_fields = ['school__name', 'street', 'cross_st']
    ordering = ['-modified', '-created', 'school__name']
    massadmin_exclude = ['location', ]

class SurveyInline(admin.TabularInline):
    model = Survey
    can_delete = False


class SurveySetAdmin(admin.ModelAdmin):
    # inlines = (SurveyInline,)
    list_display = ('__unicode__', 'school', 'begin', 'end', 'surveys_count',)
    ordering = ['-begin', 'end']
    search_fields = ['school__name', 'begin', 'end']
    list_filter = ['begin', 'end']


class ChildAdmin(admin.ModelAdmin):
    list_display = ('pk', 'survey')


admin.site.register(District, DistrictAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveySet, SurveySetAdmin)
admin.site.register(Child, ChildAdmin)
