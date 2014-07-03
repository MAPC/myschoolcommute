library(RPostgreSQL)
library(DBI)
library(reshape2)
library(plyr)
library(ggplot2)
library(scales)
library(knitr)
library(Hmisc)

# date1 = "2012-06-01"
# date2 = "2013-06-01"
source("generate_report.R")

# test with 1 response
# ORG_CODE = "06450310"
# source("generate_report.R")
# test with more than 10 responses
# ORG_CODE = "02480014"
# source("generate_report.R")
# test with missing org code
# ORG_CODE = "05160002"
# source("generate_report.R")


