from django.contrib.gis.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.urlresolvers import reverse

# lazy translation
from django.utils.translation import ugettext_lazy as _

# south introspection rules
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.PointField'])
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.MultiPolygonField'])
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.MultiLineStringField'])
except ImportError:
    pass

from datetime import datetime, timedelta


class District(models.Model):
    """ School Districts """
    districtid = models.IntegerField(primary_key=True)
    distname = models.CharField(max_length=35)
    slug = models.SlugField(max_length=35, unique=True)
    startgrade = models.CharField(max_length=2)
    endgrade = models.CharField(max_length=2)
    distcode4 = models.CharField(max_length=4)
    distcode8 = models.CharField(max_length=8)

    geometry = models.MultiPolygonField(srid=26986)
    objects = models.GeoManager()

    @property
    def name(self):
        return self.distname

    def __unicode__(self):
        return self.distname

    class Meta:
        ordering = ['distname']


class CustomManager(models.GeoManager):
    def get_query_set(self):
        qs = super(CustomManager, self).get_query_set()
        return qs.defer('shed_05', 'shed_10', 'shed_15', 'shed_20', 'geometry')


class School(models.Model):
    """ School """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)

    schid = models.CharField('School ID', max_length=8, blank=True, null=True, unique=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    town_mail = models.CharField(max_length=25, blank=True, null=True)
    town = models.CharField(max_length=25, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    principal = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    fax = models.CharField(max_length=15, blank=True, null=True)
    grades = models.CharField(max_length=70, blank=True, null=True)
    schl_type = models.CharField(max_length=3, blank=True, null=True)
    districtid = models.ForeignKey('District', blank=True, null=True)

    survey_incentive = models.TextField(blank=True, null=True)
    # Renamed to disable for now
    _active = models.BooleanField('Is survey active? (Disabled)', db_column='survey_active')

    # GeoDjango
    geometry = models.PointField(srid=26986)
    shed_05 = models.MultiPolygonField(srid=26986, null=True, blank=True)
    shed_10 = models.MultiPolygonField(srid=26986, null=True, blank=True)
    shed_15 = models.MultiPolygonField(srid=26986, null=True, blank=True)
    shed_20 = models.MultiPolygonField(srid=26986, null=True, blank=True)
    objects = CustomManager()

    def __unicode__(self):
        return self.name

    @property
    def survey_active(self):
        return SurveySet.objects.filter(
            Q(school=self) &
            Q(begin__lte=datetime.now()) &
            Q(end__gte=datetime.now())
        ).count() > 0

    @property
    def district(self):
        return self.districtid

    @permalink
    def get_absolute_url(self):
        return ('survey_school_form', None, {'school_slug': self.slug, 'district_slug': self.districtid.slug})

    def get_intersections(self):
        # school_circle = self.geometry.buffer(5000)
        # intersections = Intersection.objects.filter(geometry__intersects=school_circle)
        relation = SchoolTown.objects.get(schid=self.schid)
        intersections = Intersection.objects.filter(town_id=relation.town_id)
        return intersections

    def update_sheds(self):
        from maps import get_sheds
        sheds = get_sheds(self.id)

        shed_05 = GEOSGeometry(sheds[0.5])
        if type(shed_05) == Polygon:
            shed_05 = MultiPolygon(shed_05)

        shed_10 = GEOSGeometry(sheds[1.0])
        if type(shed_10) == Polygon:
            shed_10 = MultiPolygon(shed_10)

        shed_15 = GEOSGeometry(sheds[1.5])
        if type(shed_15) == Polygon:
            shed_15 = MultiPolygon(shed_15)

        shed_20 = GEOSGeometry(sheds[2.0])
        if type(shed_20) == Polygon:
            shed_20 = MultiPolygon(shed_20)

        shed_20_ring = shed_20.difference(shed_15)
        if type(shed_20_ring) == Polygon:
            shed_20_ring = MultiPolygon(shed_20_ring)
        try:
            self.shed_20 = shed_20_ring
        except TypeError:
            if shed_20_ring.area == 0:
                self.shed_20 = None

        shed_15_ring = shed_15.difference(shed_10)
        if type(shed_15_ring) == Polygon:
            shed_15_ring = MultiPolygon(shed_15_ring)
        try:
            self.shed_15 = shed_15_ring
        except TypeError:
            if shed_15_ring.area == 0:
                self.shed_15 = None

        shed_10_ring = shed_10.difference(shed_05)
        if type(shed_10_ring) == Polygon:
            shed_10_ring = MultiPolygon(shed_10_ring)
        try:
            self.shed_10 = shed_10_ring
        except TypeError:
            if shed_10_ring.area == 0:
                self.shed_10 = None

        if type(shed_05) == Polygon:
            shed_05 = MultiPolygon(shed_05)
        self.shed_05 = shed_05

    def save(self, *args, **kwargs):
        self.update_sheds()
        super(School, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name']


class SchoolTown(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    schid = models.CharField(max_length=8, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200)
    town_id = models.IntegerField(db_column='muni_id')

    class Meta:
        db_table = 'school_muni'


class Street(models.Model):
    """
    Streets to be returned as type-ahead in street-fields
    to limit the variety of street names and make geocoding
    more accurate.
    """
    name = models.CharField(max_length=240)
    districtid = models.ForeignKey('District', blank=True, null=True)

    geometry = models.MultiLineStringField(srid=26986)
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name


class Intersection(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    geometry = models.GeometryField(null=True, blank=True, srid=26986)
    st_name_1 = models.CharField(max_length=50, blank=True)
    st_name_2 = models.CharField(max_length=50, blank=True)
    town = models.CharField(max_length=50, blank=True)
    town_id = models.IntegerField(null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True, db_column='long')

    objects = models.GeoManager()

    class Meta:
        db_table = 'survey_intersection'

    def __unicode__(self):
        return "%s - %s" % (self.st_name_1, self.st_name_2, )


class Survey(models.Model):
    """
    Survey base questions.
    """
    school = models.ForeignKey(School)
    street = models.CharField(max_length=50, blank=True, null=True)
    cross_st = models.CharField(
        'Cross street', max_length=50, blank=True, null=True
    )
    nr_vehicles = models.IntegerField(
        'Number of Vehicles', blank=True, null=True
    )
    nr_licenses = models.IntegerField(
        'Number of License', blank=True, null=True
    )
    ip = models.IPAddressField('IP Address', blank=True, null=True)
    # Mile, shortest driving distance, not walk/bike distance
    distance = models.FloatField(null=True)
    created = models.DateTimeField(null=True)
    modified = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(User, null=True)
    # GeoDjango
    location = models.PointField(
        geography=True, blank=True, null=True, default='POINT(0 0)'
    )
    # default SRS 4326
    objects = models.GeoManager()

    def __unicode__(self):
        return u'%s' % (self.id)

    def update_location(self):
        if len(self.street) > 0 and len(self.cross_st) > 0:
            school_cross = self.school.get_intersections()
            crosses = school_cross.filter(
                Q(
                    Q(st_name_1__iexact=self.street) &
                    Q(st_name_2__iexact=self.cross_st)
                ) |
                Q(
                    Q(st_name_2__iexact=self.street) &
                    Q(st_name_1__iexact=self.cross_st)
                )
            )
            crosses = list(crosses)
            if len(crosses):
                self.location = crosses[0].geometry
                self.location.transform(4326)
            else:
                print 'No Intersection'

    def update_distance(self):
        from maps import get_driving_distance

        try:
            self.distance = get_driving_distance(
                self.school.geometry, self.location
            )
        except:
            pass


class SurveySet(models.Model):
    """
    This class represents a set of surveys collected within a set data range
    """
    school = models.ForeignKey(School)
    begin = models.DateTimeField()
    end = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "Surveys: %s for %s - %s" % (
            self.school, self.begin.strftime("%D"), self.end.strftime("%D"),
        )

    def report_url(self):
        return reverse(
            "school_report",
            kwargs={
                'school_id': self.school.pk,
                'start': str(self.begin.date()),
                'end': str(self.end.date())
            }
        )

    def surveys(self):
        return Survey.objects.filter(
            Q(school=self.school) &
            Q(created__gte=self.begin.date()) &
            Q(created__lt=self.end.date() + timedelta(days=1))
        )

    def surveys_count(self):
        return self.surveys().count()

CHILD_GRADES = (
    ('', '--'),
    ('p', 'Pre-K'),
    ('k', 'K'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
    ('10', '10'),
    ('11', '11'),
    ('12', '12'),
)

CHILD_MODES = (
    ('', '--'),
    ('fv', _('Family Vehicle (only children in your family)')),
    ('b', _('Bicycle')),
    ('sb', _('School Bus')),
    ('cp', _('Carpool (with children from other families)')),
    ('w', _('Walk')),
    ('t', _('Transit (city bus, subway, etc.)')),
    ('o', _('Other (skateboard, scooter, inline skates, etc.)'))
)

MODE_DICT = {
    'w': 'Walk',
    'b': 'Bicycle',
    'sb': 'School Bus',
    'fv': 'Family Vehicle (only children in your family)',
    'cp': 'Carpool (with children from other families)',
    't': 'Transit (city bus, subway, etc.)',
    'o': 'Other (skateboard, scooter, inline skates, etc.)',
    'none': "Not specified"
}

CHILD_DROPOFF = (
    ('', '--'),
    ('yes', _('Yes')),
    ('no', _('No')),
)


class Child(models.Model):
    survey = models.ForeignKey('Survey')
    grade = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_GRADES)
    to_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)
    dropoff = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)
    from_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)
    pickup = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)

    class Meta:
        verbose_name_plural = 'Children'

    def __unicode__(self):
        return u'%s' % (self.id)
