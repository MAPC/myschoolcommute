#!/usr/bin/env python

import os, sys
import rpy2.robjects as r

def RunR(rdir, wdir, org_code, date1, date2):
    from local_settings import DATABASES

    os.chdir(rdir)
    #print settings.DATABASES
    r.r("dbname <- '%s'" % DATABASES['default']['NAME'])
    r.r("dbuser <- '%s'" % DATABASES['default']['USER'])
    r.r("dbpasswd <- '%s'" % DATABASES['default']['PASSWORD'])
    r.r("ORG_CODE <- '%s'" % org_code)
    r.r("DATE1 <- '%s'" % date1)
    r.r("DATE2 <- '%s'" % date2)
    r.r("WORKDIR <- '%s'" % wdir)
    #r.r("BUFF_DIST <- '%s'" % 1)

    r.r("load('.RData')")
    r.r("print(ORG_CODE)")
    r.r("source('compile.R')")

if __name__ == '__main__':
    rdir = sys.argv[1]
    wdir = sys.argv[2]
    org_code = sys.argv[3]
    date1 = sys.argv[4]
    date2 = sys.argv[5]

    proj_path = os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            '../myschoolcommute'
        )
    )
    print proj_path
    sys.path.append(proj_path)

    RunR(rdir, wdir, org_code, date1, date2)
    sys.exit()
