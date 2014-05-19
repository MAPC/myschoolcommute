#!/usr/bin/env python
from __future__ import division
import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.realpath(".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myschoolcommute.settings")


from survey.models import School, District, Survey, SurveySet
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

def make_clusters(data):
    from numpy import ndarray, array
    from scipy.cluster import vq

    features = array(data)
    whitened = vq.whiten(features)
    book = array((whitened[0],whitened[2]))
    centers, _ = vq.kmeans(whitened, book)
    cluster, _ = vq.vq(whitened, centers)

    clusters = {}
    for data_idx, cluster_idx in enumerate(cluster):
        items = clusters.get(cluster_idx, [])
        items.append(features[data_idx])
        clusters[cluster_idx] = items

    return clusters.values()


def init_survey_sets():
    schools = School.objects.exclude(survey=None)
    for school in schools:
        surveys = Survey.objects.filter(school=school).order_by("modified").all()
        print "%s:\t%d" % (str(school), surveys.count())

        dates = [int(s.modified.strftime('%s')) for s in surveys]
        try:
            cs = make_clusters(dates)
            print len(cs)
        except IndexError:
            cs = [dates]

if __name__ == '__main__':

    init_survey_sets()
