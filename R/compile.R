library(RPostgreSQL)
library(DBI)
library(reshape2)
library(plyr)
library(ggplot2)
library(scales)
library(knitr)
library(Hmisc)

source("generate_report.R")
knit2pdf("minimal.Rnw")
school_name_no_space <- gsub("\\s","",School_Name)
file.rename("minimal.pdf",paste("Reports/",
                                paste(school_name_no_space,".pdf",sep=""),
                                sep=""))


