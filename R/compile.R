library(RPostgreSQL)
library(DBI)
library(reshape2)
library(plyr)
library(ggplot2)
library(scales)
library(knitr)
library(Hmisc)

for (ORG_CODE in ORG_CODES){
  if (ORG_CODE == "01760068") next
  source("generate_report.R")
  School_Name <- enrollmentDF[enrollmentDF$ORG.CODE==ORG_CODE,"SCHOOL"]
  school_name_no_space <- gsub("\\s","",School_Name)
  knit2pdf("minimal.Rnw", compiler = "xelatex")
  file.rename("minimal.pdf",paste("Reports/",
                                  paste(school_name_no_space,".pdf",sep=""),
                                  sep=""))
}


