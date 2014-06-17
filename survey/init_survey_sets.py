#!/usr/bin/env python
from __future__ import division
import os, sys
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler
from random import randrange
import math
from numpy import array, argwhere
from datetime import datetime, date

if __name__ == '__main__':
    sys.path.append(os.path.realpath(".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myschoolcommute.settings")


from survey.models import School, District, Survey, SurveySet
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

def make_clusters(data):
    data = [[float(d), 0.0] for d in data]
    X = StandardScaler().fit_transform(data)

    db = DBSCAN(eps=0.3, min_samples=3).fit(X)
    core_samples = db.core_sample_indices_
    labels = db.labels_

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    clusters = [[] for i in range(len(set(labels)))]
    for cluster_idx, l in enumerate(set(labels)):
        members = [idx[0] for idx in argwhere(labels == l)]
        samples = [idx for idx in  core_samples if labels[idx] == l]
        for i in members:
            x = data[i]
            core = i in samples and l != -1
            #clusters[cluster_idx].append([x, core, l])
            #if not core:
            #    print date.fromtimestamp(x[0])
            clusters[cluster_idx].append(x[0])
    return clusters



def init_survey_sets():
    schools = School.objects.exclude(survey=None)
    for school in schools:
        surveys = Survey.objects.filter(school=school).order_by("modified").all()
        print "%s:\t%d" % (str(school), surveys.count())

        dates = []
        for s in surveys:
            dates.append(int(s.modified.date().strftime('%s')))

        try:
            cs = make_clusters(dates)
        except IndexError:
            cs = [dates]
        print "Clusters: " + str(len(cs))
        #print cs
        for cluster in cs:
            begin = surveys[dates.index(cluster[0])].modified
            end = surveys[dates.index(cluster[-1])].modified

            ss = SurveySet(begin=begin, end=end, school=school)
            ss.save()

if __name__ == '__main__':

    init_survey_sets()
