#!/usr/bin/python
import os, sys
import fiona
from shapely import geometry

if __name__ == '__main__':
    sys.path.append(os.path.realpath(".."))
    from django.core.management import setup_environ
    from myschoolcommute import settings

    setup_environ(settings)


from survey.models import School, District, Street
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

def update_schools():    
    new_schools = []
    updated_schools = []

    school_ids = []
    
    with fiona.open("data/Schools.shp", "r") as shape:
        for f in shape:
            props = f['properties']

            try:
                obj = School.objects.get(schid=props['schid'])
                school_ids.append(obj.pk)
            except ObjectDoesNotExist, e:
                obj = False
                new_schools.append(f)

            if f['properties']['updated']:
                if obj:
                    updated_schools.append(f)
                    print "Update:", props['name'], props['schid'], props['objectid'], props['status']
                    print "Old:", obj.name, obj.schid, obj.pk

                    #save object id to UPDATE
                    f['properties']['id'] = obj.pk

                else:
                    print "New:", props['name'], props['schid'], props['objectid']

        sid = transaction.savepoint()
        try:
            schools = list(School.objects.exclude(pk__in=school_ids))
            print "Deleted schools: %d" % len(schools)
            for school in schools:
                school.delete()

            print "New schools: %d" % len(new_schools)
            print "Updated schools: %d" % len(updated_schools)
            for f in new_schools+updated_schools:
                props = f['properties']
                del props['updated']
                del props['status']
                del props['objectid']
                school = School(**props)
                shape = geometry.shape(f['geometry'])
                school.geometry = shape.wkt
                school.save()

            transaction.savepoint_commit(sid)
        except Exception, e:
            print str(e)
            transaction.savepoint_rollback(sid)
            print "Database import rolled back"
            
if __name__ == '__main__':

    update_schools()