############### Read Data from PostGres database ###################
# 1) read PostGres table 'survey_child' into data frame 'df_all'
# 2) remove tuples with NA values for grade, to_school, dropoff, from_school, pickup, schid, distance
# 3) create table that contains only tuples that match ORG_CODE; assign this table to variable 'df'
# 4) check if ORG_CODE is in Enrollment table; if not, generate pdf with error message to user, 'ORG_CODE.pdf'
#    and terminate
# 5) Relabel columns to match 'legacy' code:
#    - to_school as ModeTo,
#    - from_school as ModeFrom,
#    - dropoff as DropOff
#    - pickup as PickUp
# 6) create BUFF_DIST column based on distance column
# 7) relabel the values in ModeTo and ModeFrom columns (e.g. fv -> Family Vehicle)
# 8) create ModeToMod and ModeFromMod from the ModeTo and ModeFrom columns, respectively
# 9) assign 'df' to the variable 'DF'

library(RPostgreSQL)

# 1)
# establish connection to PostgreSQl;
# fetch survey table and write to variable df
# ch <- odbcConnect("PostgreSQL30",pwd = "max1max2")
# df <- sqlFetch(ch,"survey_child")

drv <- dbDriver("PostgreSQL")
ch <- dbConnect(drv, 
                host='localhost',
                port='5432', 
                dbname=dbname,
                user=dbuser,
                password=dbpasswd)
df_all <- dbSendQuery(ch,"select * from temp_child")
df_all <- fetch(df_all,n=-1)
dbDisconnect(ch) # disconnect from PostGres database

# 2)
# cols_needed contains variables that cannot be NA 
cols_needed <- c("grade","to_school","dropoff","from_school","pickup","schid","distance")
df_all <- df_all[complete.cases(df_all[cols_needed]),] # remove any tuples that contain NA values in the cols_needed columns
df_all <- droplevels(df_all)

# 3)
# select records that match ORG_CODE
df <- df_all[df_all$schid == ORG_CODE,]

# 3a) 
# choose enrollment table based on date of created column
start_date = survey_dates(df,"created", "current_time")$start_date
if (start_date < as.Date("2012-07-30")){
  enrollmentDF = enrollment11_12
  enrollmentDate = "2011-2012"
} else {
  enrollmentDF = enrollment12_13
  enrollmentDate = "2012-2013"
}


# 4)
# check if Enrollment table contains ORG_CODE; if not
# create pdf 'ORG_CODE.pdf' with error message to user
# and terminate application
if (!(ORG_CODE %in% enrollmentDF$ORG.CODE)){
  knit2pdf("compile_no_school_code.Rnw")
  file.rename("compile_no_school_code.pdf",paste("Reports/",paste(ORG_CODE,".pdf",sep=""),sep=""))
  stop()
}


# 5) Relabel columns to match 'legacy' code
names(df)[grep("to_school",names(df))] <- "ModeTo"
names(df)[grep("from_school",names(df))] <- "ModeFrom"
names(df)[grep("dropoff",names(df))] <- "DropOff"
names(df)[grep("pickup",names(df))] <- "PickUp"

# 6) create BUFF_DIST column based on distance column
df$BUFF_DIST <- ifelse(df$shed == 0, "2.0+",
                       ifelse(df$shed == 1, "0.5",
                              ifelse(df$shed == 2, "1.0",
                                     ifelse(df$shed == 3, "1.5",
                                            "2.0"))))

# 7) relabel the values in ModeTo and ModeFrom columns (e.g. fv -> Family Vehicle)
df$ModeTo <- mode_labels(df$ModeTo)
df$ModeFrom <- mode_labels(df$ModeFrom)

# 8) create ModeToMod and ModeFromMod from the ModeTo and ModeFrom columns, respectively
df$ModeToMod <- mode_simple(df$ModeTo)
df$ModeFromMod <- mode_simple(df$ModeFrom)

# Reorder df$grades
df$grade <- grade_reorder(df$grade)

## create grade ranges 
lowGrades = c("p", "k", as.character(1:3))
midGrades = as.character(4:7)
highGrades = as.character(8:12)
df$gradeRanges = ifelse(df$grade %in% lowGrades, "low",
                     ifelse(df$grade %in% midGrades, "mid",
                            "high"))

# 9) assign 'df' to the variable 'DF'
DF <- df
DF <- DF[DF$grade %in% getGrades(enrollmentDF,ORG_CODE),]


############### End Read Data from PostGres database ###################

############### Get Survey Dates #######################
# survey start and end dates are based on the created and current_time columns
# start_date is the minimum value in created column
# end_date is the maximum value in current_time column
date_list <- survey_dates(DF,"created","current_time")
start_date <- date_list$start_date
start_month <- date_list$start_month
start_year <- date_list$start_year
end_date <- date_list$end_date
end_month <- date_list$end_month
end_year <- date_list$end_year
############### End Get Survey Dates #######################

############### Begin Calculate GHG Emissions ###################
# This section addes the following columns to DF:
# - distEst, the distance to school
# - ghg_Total_To, estimated GHG emissions to school in the moring
# - ghg_Total_From, esitmated GHG emissions from school school in the afternon


## Assign distance column to variable distEst to conform to 
## 'legacy' code
distEst <- DF$distance

# Corresponds to Step 1 (page C7) from Kids Are Commuters Too
# Modify travel distance from Step 1 based on whether 
# student is dropped off on the way to another activity
# If PickUp = Yes then
# the expression 0.7928932*distEst is the expected value of the extra distance that is
# driven, which is given by 3*distEst - (2^.5)distEst)/2
# Otherwise, distance is 2*distEst (the roundtrip distance)
# same reasoning applied to distEstFrom

distEstTo <- ifelse(DF$DropOff == "yes", 0.7928932*distEst, 2*distEst)
distEstFrom <- ifelse(DF$PickUp == "yes", 0.7928932*distEst, 2*distEst)


## Corresponds to Step 2 (page C7) from Kids Are Commuters Too
## Calculate VMT TO and FROM school based on whether or not 
## student carpools. If student carpools, carpool size is assumed to be two,
## and vmtTo = 0.5*distEstTo and vmtFrom = 0.5*distEstFrom. If student does not
## carpool, vmtTo = distEstTo and vmtFrom = distEstFrom

vmtTo <- ifelse(DF$ModeTo == "Carpool", 0.5*distEstTo,
                ifelse(DF$ModeTo == "Family Vehicle", distEstTo, 0))

vmtFrom <- ifelse(DF$ModeFrom == "Carpool", 0.5*distEstFrom,
                  ifelse(DF$ModeFrom == "Family Vehicle", distEstFrom, 0))

## Corresponds to Steps 4 and 5 (page C7) from Kids Are Commuters Too
## Calculate Gas Consumed from VMT estimates
## Fuel efficiency estimates from the EPA were used:
## 23.9 mpg for passenger cars and 17.4 for trucks
## These were then reduced to 21.0 and 17.0 to account for city MPG
## Per USDOT estimates, vehicle mix was assumed to be
## 63.4% passenger cars and 36.6% trucks
## So, gallons consumed = VMT/(21.0*0.634 + 17.0*0.366)
## This was then multiplied by 1.8 to account for cold starts 

gallonsTo <- 1.8*vmtTo/(21.0*0.634 + 17.0*0.366)
gallonsFrom <- 1.8*vmtFrom/(21.0*0.634 + 17.0*0.366)


## Corresponds to Step 6 (page C7) from Kids Are Commuters Too
## Calculate GHG emissions
## Per EPA estimates, GHG emissions (in kilograms) are 8.8 kg per gallon consumed
## So ghg (kg) = 8.8*gallons

CO2_To <- 8.8*gallonsTo
CO2_From <- 8.8*gallonsFrom

## Corresponds to Step 7 (page C7) from Kids Are Commuters Too
## Estimate other GHG emissions as (C02 emissions)/19

ghg_Other_To <- CO2_To/19
ghg_Other_From <- CO2_From/19

## Corresponds to Step 8 (page C7) from Kids Are Commuters Too
## Estimate cold start additivles

cold_start_To <- ifelse(CO2_To > 0.0, 0.035,CO2_To)
cold_start_From <- ifelse(CO2_From > 0.0, 0.035, CO2_From)

## Corresponds to Step 9 (page C7) from Kids Are Commuters Too
# Calculate Total GHG Emissions

ghg_Total_To <- CO2_To + ghg_Other_To + cold_start_To
ghg_Total_From <- CO2_From + ghg_Other_From + cold_start_From
ghg_Total = ghg_Total_To + ghg_Total_From

## Add GHG calculations to DF

DF <- as.data.frame(cbind(DF,distEst,ghg_Total_To,ghg_Total_From, ghg_Total))

School_Name <- enrollmentDF[enrollmentDF$ORG.CODE==ORG_CODE,"SCHOOL"]

############### End Calculate GHG Emissions ###################

############### Begin Survey Statistics ###################

# This section calculates survey participation by grade level

# g_df will have three columns
# Grade = Grade levels p, k, 1 to 12
# Surveyed = Students surveyed
# NotSurveyed = Students not surveyed
# Enroll = Students enrolled
# Pct = percent of enrolled students surveyed
# Steps
# 1: 
# Count students by grade.
# Columns:
# Grade = grade level
# freq = count of students
g_df_temp <- count(DF,.(grade))

# 2:
# Create empty data frame
g_df <- enroll_df()

# 2:
# fill Surveyed column of g_df
g_df <- mergeDF(g_df, g_df_temp,
                data.column1 = "Surveyed",
                data.column2 = "freq",
                by.x = "Grade",
                by.y = "grade")

# 3:
# et_df
# Columns:
# SCHOOL = School name (form: <District> - <School>)
# variable = grade level PK, K, 1 to 12
# value = enrollment
et_df <- enroll_totals(enrollmentDF,ORG_CODE)

# 4:
# fill Enroll column of g_df
g_df <- mergeDF(g_df, et_df,
                data.column1 = "Enroll",
                data.column2 = "value",
                by.x = "Grade",
                by.y = "variable")

# 5: 
# remove rows with zero enrollment
g_df <- subset(g_df,Enroll > 0)

# 6: 
# calculate Pct
g_df$Pct <- round(100*g_df$Surveyed/g_df$Enroll,0)

# 7: 
# calculate NotSurveyed
g_df$NotSurveyed <- g_df$Enroll - g_df$Surveyed
g_df$NotSurveyed <- ifelse(g_df$NotSurveyed < 0,0,
                           g_df$NotSurveyed)

# 8:
# "melt" g_df from wide to long format for graphing
g_dfg <- melt(g_df,
              measure.vars = c("Surveyed",
                               "NotSurveyed"))

g_dfg$Grade <- factor(g_dfg$Grade,
                      levels = c("p","k", 1:12))

# Factoids
sampleSize <- sum(g_df$Surveyed)
enrollTotal <- sum(g_df$Enroll)
surveyPct <- round(100*sampleSize/enrollTotal,0)

############### End Survey Statistics ###################

############### Begin Student Proximity  ###################

# this section calculates survey parcipation by walkshed
# it estimates the number of students by walkshed

# b_df will have three columns
# Columns:
# BUFF_DIST: 0.5, 1.0, 1.5, 2.0, 2.0+
# Surveyed: Number of Students Surveyed
# Enroll: Students enrolled
# NotSurveyed: Number of Students Not Surveyed

# Steps
# 1: 
# Create empty data frame to hold 
# data by buffer and grade
gbse_df <- gbse_df_create()

# 2:
# Count students by grade and buffer.
# Columns:
# Grade = grade level
# BUFF_DIST = Buffer 
# freq = count of students
gb_df_temp <- count(DF,.(grade,BUFF_DIST))

# 3 
# fill in Surveyed column in gbse_df

gbse_df <- mergeDF(gbse_df,
                   gb_df_temp,
                   data.column1 = "Surveyed",
                   data.column2 = "freq",
                   by.x = c("Grade","Buffer"),
                   by.y = c("grade","BUFF_DIST"))
# 3: 
# Add Column:
# Grade_Surveyed = Total Students Surveyed By Grade
gbse_df <- ddply(gbse_df,
                 .(Grade),
                 transform,
                 Grade_Surveyed = sum(Surveyed))

# 4: 
# Merge gbse_df with et_df: Enrollment by Grade
# Fills
# Column
# Enroll
gbse_df <- mergeDF(gbse_df,
                   et_df,
                   data.column1 = "Enroll",
                   data.column2 = "value",
                   by.x = "Grade",
                   by.y = "variable")

gbse_df <-  subset(gbse_df,Enroll > 0)


# 5: 
# Calculate
# Columns
# NotSurveyed
# Pct
gbse_df$NotSurveyed <- gbse_df$Enroll - gbse_df$Surveyed

gbse_df$Pct <- ifelse(gbse_df$Grade_Surveyed > 0,
                      gbse_df$Surveyed/gbse_df$Grade_Surveyed,
                      0)

# 6:
# Sum students by buffer
b_df <- ddply(gbse_df,
              .(Buffer),
              summarise,
              Estimate = sum((Surveyed/Grade_Surveyed)*Enroll, na.rm=T),
              Count = sum(Surveyed))

b_df$NotSurveyed <- b_df$Estimate - b_df$Count
b_df$NotSurveyed <- ifelse(b_df$NotSurveyed < 0, 0, b_df$NotSurveyed)

# 8:
# "melt" g_df from wide to long format for graphing
b_dfg <- melt(b_df,
              measure.vars = c("Count",
                               "NotSurveyed"))

# Factoids
estWithinOneMile <- sum(b_df$Estimate[b_df$Buffer %in% c("0.5","1.0")])
estWithinTwoMile <- sum(b_df$Estimate[b_df$Buffer %in% c("0.5","1.0","1.5","2.0")])
estBeyondOneMile <- sum(b_df$Estimate[b_df$Buffer %in% c("1.5","2.0","2.0+")])
pctWithinOneMile <- round(100*estWithinOneMile/sum(b_df$Estimate),0)
pctWithinTwoMile <- round(100*estWithinTwoMile/sum(b_df$Estimate),0)
avgDistToSchool <- round(mean(DF$distance,na.rm=TRUE),digits = 1)


# b_dft is b_df with buffers as column headings
# b_dft will be passed to latex function
# Columns:
# Buffer levels: 0.5, 1.0, 1.5, 2.0, 2.0+
# Rows: 
# Surveyed Students
# Estimates Total
# Percent of Students: Estiamtes sudents per buffer as percent of Total Estimates

# 1:
# Calculate
# Column
# Pct = Buffer Estimate as percent of Total Students
b_df$Pct <- round(100*b_df$Estimate/(sum(b_df$Estimate)))

# 2:
# create b_dft as transpose of b_df
b_dft <- as.data.frame(t(b_df[c("Estimate","Count","Pct")]))


# 3:
# convert columns to characters
# apply addPct to bottom row
b_dft[1,] <- round(b_dft[1,],0)
b_dft[nrow(b_dft),] <- addPct(b_dft[nrow(b_dft),])
b_dft <- as.data.frame(lapply(b_dft,as.character))
b_dft <- cbind(c("Est Total","Surveyed","Percent"),b_dft)
names(b_dft) <- c("",levels(b_df$Buffer))

############### End Student Proximity ###################

############### Student Travel Choices ###################

# this section estimates:
# 1) student travel mode by morning and afternoon, and
# 2) student travel mode by morning and afternoon and buffer
# 3) if reported grades do not overlap at all with grades in enrollment table
#    the application will return an error message in pdf form and terminate

# mt_df will have three columns
# Columns:
# Mode: "Bike","Carpool","Family Vehicle","School Bus","Transit","Walk"
# Time: "Morning","Afternoon"
# Surveyed: Number of Students Surveyed
# Enroll: Students enrolled

# Steps
# 1: 
# Create empty data frame to hold 
# data by grade, buffer, mode, and time
gmbse_df <- gmbse_df_create() 

# 2:
# Count students by grade, buffer, and ModeTo/ModeFrom.
# Columns:
# Grade = grade level
# BUFF_DIST = Buffer 
# ModeTo = Mode to school
# freq = count of students
gbmT_df_temp <- count(DF,.(grade,BUFF_DIST,ModeTo))
gbmF_df_temp <- count(DF,.(grade,BUFF_DIST,ModeFrom))

# 3 
# fill in Surveyed column in gbse_df

gmbse_df[gmbse_df$Time=="Morning",] <- mergeDF(gmbse_df[gmbse_df$Time=="Morning",],
                                               gbmT_df_temp,
                                               data.column1 = "Surveyed",
                                               data.column2 = "freq",
                                               by.x = c("Grade","Buffer","Mode"),
                                               by.y = c("grade","BUFF_DIST","ModeTo"))

gmbse_df[gmbse_df$Time=="Afternoon",] <- mergeDF(gmbse_df[gmbse_df$Time=="Afternoon",],
                                                 gbmF_df_temp,
                                                 data.column1 = "Surveyed",
                                                 data.column2 = "freq",
                                                 by.x = c("Grade","Buffer","Mode"),
                                                 by.y = c("grade","BUFF_DIST","ModeFrom"))

# 3: 
# Add Column:
# Grade_Surveyed = Total Students Surveyed By Grade
gmbse_df <- ddply(gmbse_df,
                  .(Grade,Time),
                  transform,
                  Grade_Surveyed = sum(Surveyed))

# 4: 
# Merge gmbse_df with et_df: Enrollment by Grade
# Fills
# Column
# Enroll
gmbse_df <- mergeDF(gmbse_df,
                    et_df,
                    data.column1 = "Enroll",
                    data.column2 = "value",
                    by.x = "Grade",
                    by.y = "variable")

gmbse_df <-  subset(gmbse_df,Enroll > 0)
gmbse_df <-  droplevels(gmbse_df)

# create vector of just those grades that exist in Enrollment
grades_exist <- unique(gmbse_df$Grade)

# 6:
# Sum students by buffer
mt_df <- ddply(gmbse_df,
               .(Mode,Time),
               summarise,
               Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))

mt_df <- ddply(mt_df,
               .(Time),
               transform,
               Pct = Estimate/sum(Estimate))

mt_df <- ddply(mt_df,
               .(Mode),
               transform,
               Mean = mean(Estimate))

mt_df$Mode <- reorder(mt_df$Mode,-1*mt_df$Mean)


# Factoids
carTripMorningCount <- sum(mt_df$Estimate[mt_df$Time == "Morning" & mt_df$Mode %in% c("Carpool","Family Vehicle")])
carTripAfternoonCount <- sum(mt_df$Estimate[mt_df$Time == "Afternoon" & mt_df$Mode %in% c("Carpool","Family Vehicle")])
walkTripMorningCount <- sum(mt_df$Estimate[mt_df$Time == "Morning" & mt_df$Mode %in% c("Walk","Bike")])
walkTripAfternoonCount <- sum(mt_df$Estimate[mt_df$Time == "Afternoon" & mt_df$Mode %in% c("Walk","Bike")])

carTripCount <- carTripMorningCount + carTripAfternoonCount
walkTripCount <- walkTripMorningCount + walkTripAfternoonCount
totalTripCount <- sum(mt_df$Estimate)
carTripMorningPct <- round(100*carTripMorningCount/(totalTripCount/2),1)
carTripAfternoonPct <- round(100*carTripAfternoonCount/(totalTripCount/2),1)
walkTripMorningPct <- round(100*walkTripMorningCount/(totalTripCount/2),1)
walkTripAfternoonPct <- round(100*walkTripAfternoonCount/(totalTripCount/2),1)
carTripPct <- round(100*carTripCount/totalTripCount,0)
walkTripPct <- round(100*walkTripCount/totalTripCount,0)

walkMorningvAfternoon <- ifelse(walkTripMorningPct > walkTripAfternoonPct,
                                "lower",
                                ifelse(walkTripMorningPct == walkTripAfternoonPct,
                                       "equal", "higher"))
carMorningvAfternoon <- ifelse(carTripMorningPct < carTripAfternoonPct,
                               "lower",
                               ifelse(carTripMorningPct == carTripAfternoonPct,
                                      "equal", "higher"))

carTripMorningPct <- paste(round(100*(carTripMorningCount-carTripAfternoonCount)/carTripMorningCount,1),"\\%",sep="")
modeByTimeText <- ifelse(walkMorningvAfternoon == "higher" & carMorningvAfternoon == "higher",
                         paste("The auto share is lower in the afternoon, indicating that as many as ",
                               carTripMorningPct,
                               " of those who are driven to school in the morning get home by other means in the afternoon.",sep=""),
                         "")



# mb_df will have three columns
# Columns:
# Buffer: 0.5, 1.0, 1.5, 2.0, 2.0+
# Mode: "Auto" "School Bus" "Walk"
# Surveyed: Number of Students Surveyed
# Enroll: Students enrolled

gmSbse_df <- gmSbse_df_create()

# 2:
# Count students by grade, buffer, and ModeToMod/ModeFromMod.
# Columns:
# Grade = grade level
# BUFF_DIST = Buffer 
# ModeTo = Mode to school
# freq = count of students
gbmTS_df_temp_morning <- count(DF,.(grade,BUFF_DIST,ModeToMod))
gbmTS_df_temp_afernoon <- count(DF,.(grade,BUFF_DIST,ModeFromMod))
# 3 
# fill in Surveyed column in gbse_df
gmSbse_df_morning <- gmSbse_df
gmSbse_df_afternoon <- gmSbse_df

gmSbse_df_morning <- mergeDF(gmSbse_df_morning,
                             gbmTS_df_temp_morning,
                             data.column1 = "Surveyed",
                             data.column2 = "freq",
                             by.x = c("Grade","Buffer","Mode"),
                             by.y = c("grade","BUFF_DIST","ModeToMod"))

gmSbse_df_afternoon <- mergeDF(gmSbse_df_afternoon,
                               gbmTS_df_temp_afernoon,
                               data.column1 = "Surveyed",
                               data.column2 = "freq",
                               by.x = c("Grade","Buffer","Mode"),
                               by.y = c("grade","BUFF_DIST","ModeFromMod"))
# 3: 
# Add Column:
# Grade_Surveyed = Total Students Surveyed By Grade
gmSbse_df_morning <- ddply(gmSbse_df_morning,
                           .(Grade),
                           transform,
                           Grade_Surveyed = sum(Surveyed))

gmSbse_df_afternoon <- ddply(gmSbse_df_afternoon,
                             .(Grade),
                             transform,
                             Grade_Surveyed = sum(Surveyed))

# 4: 
# Merge gmSbse_df with et_df: Enrollment by Grade
# Fills
# Column
# Enroll
gmSbse_df_morning <- mergeDF(gmSbse_df_morning,
                             et_df,
                             data.column1 = "Enroll",
                             data.column2 = "value",
                             by.x = "Grade",
                             by.y = "variable")

gmSbse_df_afternoon <- mergeDF(gmSbse_df_afternoon,
                               et_df,
                               data.column1 = "Enroll",
                               data.column2 = "value",
                               by.x = "Grade",
                               by.y = "variable")

gmSbse_df_morning <-  subset(gmSbse_df_morning,Enroll > 0)
gmSbse_df_morning <-  droplevels(gmSbse_df_morning)
gmSbse_df_afternoon <-  subset(gmSbse_df_afternoon,Enroll > 0)
gmSbse_df_afternoon <-  droplevels(gmSbse_df_afternoon)

# 5.5 check if reported grades match actual grades:
if (sum(gmSbse_df_morning$Grade_Surveyed) == 0){
  knit2pdf("compile_no_school_code.Rnw")
  school_name_no_space <- gsub("\\s","",School_Name)
  file.rename("compile_no_school_code.pdf",paste("Reports/",paste(school_name_no_space,".pdf",sep=""),sep=""))
  stop()
}

# 6:
# Sum students by buffer
# mSb_df_morning <- ddply(gmSbse_df_morning,
#                         .(Mode,Buffer),
#                         summarise,
#                         Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))

mSb_df_morning <- ddply(gmSbse_df_morning,
                        .(Mode,Buffer),
                        summarise,
                        Estimate = sum(ifelse(Grade_Surveyed > 0, 
                                              Surveyed*Enroll/Grade_Surveyed,
                                              0)))

mSb_df_afternoon <- ddply(gmSbse_df_afternoon,
                          .(Mode,Buffer),
                          summarise,
                          Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))

mSb_df_morning$time <- "Morning"
mSb_df_afternoon$time <- "Afternoon"

mSb_df <- rbind(mSb_df_morning,mSb_df_afternoon)

##### Begin New Code #####
# create table of mode by morning/afternoon and walkshed
mSb_df_for_latex <- 
  rbind(aggregate(mSb_df_morning$Estimate,
                  by=list(mSb_df_morning$Mode),
                  t),
        aggregate(mSb_df_afternoon$Estimate,
                  by=list(mSb_df_morning$Mode),
                  t))
mSb_df_for_latex <- as.data.frame(lapply(as.data.frame(round(mSb_df_for_latex$x,0)),
                                         as.character))

##### End New Code #####


############### End Student Travel Choices ###################

############### Begin Greenhouse Gas Emissions ###################

## converts mSb_df into mSb_df_wide to pass to latex function
mSb_df_wide_morning <- modeDFwideFunction(mSb_df[mSb_df$time=="Morning",c("Mode","Buffer","Estimate")])
mSb_df_wide_morning[,2:6] <- round(mSb_df_wide_morning[,2:6],0)
mSb_df_wide_morning[,2:6] <- lapply(mSb_df_wide_morning[,2:6],as.character)
mSb_df_wide_morning_pct <- mSb_df_wide_morning[,c(1,7:11)]

mSb_df_wide_afternoon <- modeDFwideFunction(mSb_df[mSb_df$time=="Afternoon",c("Mode","Buffer","Estimate")])
mSb_df_wide_afternoon[,2:6] <- round(mSb_df_wide_afternoon[,2:6],0)
mSb_df_wide_afternoon[,2:6] <- lapply(mSb_df_wide_afternoon[,2:6],as.character)
mSb_df_wide_afternoon_pct <- mSb_df_wide_afternoon[,c(1,7:11)]


ghgBufferDFgeneric <- data.frame(Buffer = buffers,
                                 Students = 0,
                                 Ghg_Total = 0)

ghgBufferDF <- ddply(DF,
                     .(BUFF_DIST, grade),
                     summarise,
                     students = length(id),
                     ghg_Total = 180*sum(ghg_Total))

ghgBufferDF <- subset(ghgBufferDF, grade %in% grades_exist)
ghgBufferDF <- droplevels(ghgBufferDF)

ghgBufferDF <- ddply(ghgBufferDF,
                     .(BUFF_DIST),
                     summarise,
                     students = sum(students),
                     ghg_Total = sum(ghg_Total))

ghgBufferDF <- ghgBufferDF[!is.na(ghgBufferDF$BUFF_DIST) & ghgBufferDF$BUFF_DIST != "",]
ghgBufferDFgeneric <-   mergeDF(ghgBufferDFgeneric,
                                ghgBufferDF,
                                data.column1 = "Students",
                                data.column2 = "students",
                                by.x = "Buffer",
                                by.y = "BUFF_DIST")

ghgBufferDFgeneric <-   mergeDF(ghgBufferDFgeneric,
                                ghgBufferDF,
                                data.column1 = "Ghg_Total",
                                data.column2 = "ghg_Total",
                                by.x = "Buffer",
                                by.y = "BUFF_DIST")

ghgBufferDFgeneric$studentsEst <- round(enrollTotal*ghgBufferDFgeneric$Students/(sum(ghgBufferDFgeneric$Students)),0)
ghgBufferDFgeneric$ghgEst <- ifelse(ghgBufferDFgeneric$Students > 0,
                                    ghgBufferDFgeneric$studentsEst*ghgBufferDFgeneric$Ghg_Total/ghgBufferDFgeneric$Students,
                                    0)
ghgBufferDFgeneric$ghgEstPerCap <- ifelse(ghgBufferDFgeneric$studentsEst > 0,
                                          ghgBufferDFgeneric$ghgEst/ghgBufferDFgeneric$studentsEst,
                                          0)
totGhGest <- sum(ghgBufferDFgeneric$ghgEst,na.rm=T)
if (totGhGest > 0){
  ghgBufferDFgeneric$PctTotGHG <- ghgBufferDFgeneric$ghgEst/totGhGest
} else {ghgBufferDFgeneric$PctTotGHG <- 0}

ghgPerCap10Buffer <- ifelse(sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")],na.rm=T) > 0,
                            (sum(ghgBufferDFgeneric$ghgEstPerCap[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")]*ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")],na.rm=T))/
                              sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")],na.rm=T),
                            0)

ghgPerCap10PlusBuffer <- ifelse(sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")],na.rm=T) > 0,
                                (sum(ghgBufferDFgeneric$ghgEstPerCap[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")]* ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")],na.rm=T)/
                                   sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")],na.rm=T)),
                                0)

ghgPerCap <- ifelse(sum(ghgBufferDFgeneric$studentsEst,na.rm=T) > 0,
                    sum(ghgBufferDFgeneric$ghgEst,na.rm=T)/sum(ghgBufferDFgeneric$studentsEst,na.rm=T),
                    0)


ghgBufferDFgeneric$PctTotGHGprint <- addPct(100*ghgBufferDFgeneric$PctTotGHG)
ghgBufferDFgeneric$ghgEst <- round(ghgBufferDFgeneric$ghgEst,0)
ghgBufferDFgeneric$ghgEstPerCap <- round(ghgBufferDFgeneric$ghgEstPerCap,0)
ghgBufferDFgeneric[,2:6] <- lapply(ghgBufferDFgeneric[,2:6],as.character)

################### End  Greenhouse Gas Emissions ########################

################### Begin  How Your School Compares ########################

## calculate range within one mile for peer schools
## pSdF == %peer %School %data %Frame
oneMileSchoolRatio <- pctWithinOneMile/100
walkSchoolOneMile <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("0.5","1.0") & mSb_df$Mode == "Walk"])
estWithinOneMile <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("0.5","1.0")])
estBeyondOneMile <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("1.5","2.0", "2.0+")])
schoolBusBeyondOneMile <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("1.5","2.0", "2.0+") & mSb_df$Mode == "School Bus"])
pctWalkSchoolOneMile  <-   ifelse(estWithinOneMile > 0,
                                  round(100*walkSchoolOneMile/estWithinOneMile),
                                  0)
walkSchoolOneMileRatio <- pctWalkSchoolOneMile/100
pctSchoolBusBeyondOneMile  <- ifelse(estBeyondOneMile > 0,
                                     round(100*schoolBusBeyondOneMile/estBeyondOneMile),
                                     0)

estWithinOneMileMorningAfternoon <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("0.5","1.0")])
pSdF <- compareSchTable(allSchComp,.27)
## pSdF == %peer %School %aggregation
pSagg <- compSchoolsData(pSdF)
pSagg <- rbind(c(oneMileSchoolRatio,
                 walkSchoolOneMileRatio,
                 ghgPerCap),pSagg)
pSagg <- cbind(c("Your School","Peer Schools"),pSagg)
names(pSagg)[1] <- ""
pSaggLatex <- pSagg
pSaggLatex$PctMile <- addPct(100*pSagg$PctMile)
pSaggLatex$PctWalkMile <- addPct(100*pSagg$PctWalkMile)
pSaggLatex$ghgPerCap <- as.character(round(pSaggLatex$ghgPerCap,0))

# create DF that has count of students in each gradeRange and Buffer
# including those with no students 

rangeBufferDF = aggregate(mSb_df_morning$Estimate,
          by=list(mSb_df_morning$Mode),t)

rangeBufferDF[,2] = rangeBufferDF[,2] +
  aggregate(mSb_df_afternoon$Estimate,
            by=list(mSb_df_afternoon$Mode),t)[,2]

rangeBufferDFMorning = ddply(mSb_df_morning,
                      .(Mode, Buffer),
                      summarise,
                      Estimate = sum(Estimate))

rangeBufferDFAfternoon = ddply(mSb_df_afternoon,
                             .(Mode, Buffer),
                             summarise,
                             Estimate = sum(Estimate))

rangeBufferDF = rangeBufferDFMorning
rangeBufferDF$Estimate = rangeBufferDF$Estimate + rangeBufferDFAfternoon$Estimate

rangeBufferDF = ddply(rangeBufferDF,
                      .(Buffer),
                      transform,
                      BufferTotal = sum(Estimate))

rangeBufferDF$bufferShare = ifelse(rangeBufferDF$BufferTotal > 0,
                                   100*rangeBufferDF$Estimate/rangeBufferDF$BufferTotal,
                                   0)

gradeRangeBufferDF = mergeDF(gradeRangeBuffer(),
                             count(DF,.(gradeRanges,BUFF_DIST)),
                             by.x = c("gradeRange", "Buffer"),
                             by.y = c("gradeRanges", "BUFF_DIST"),
                             data.column1 = "Count",
                             data.column2 = "freq")

gradeRangeBufferDF$Count = 2*gradeRangeBufferDF$Count

gradeRangeBufferDF$average = 0

gradeRangeBufferDF = mergeDF(gradeRangeBufferDF,
                             surveysGradeBuffer,
                             by.x = c("gradeRange", "Buffer"),
                             by.y = c("gradeRanges", "BUFF_DIST"),
                             data.column1 = "average",
                             data.column2 = "Expected")

gradeRangeBufferDF$Expected = gradeRangeBufferDF$Count*gradeRangeBufferDF$average

bufferByModeDF = ddply(gradeRangeBufferDF,
                       .(Buffer),
                       summarise,
                       count = sum(Count),
                       expected = sum(Expected))

bufferByModeDF$actual = 0 

bufferByModeDF = mergeDF(bufferByModeDF,
                         count(DF[DF$ModeToMod == "Walk",],
                               .(BUFF_DIST)),
                         by.x = c("Buffer"),
                         by.y = c("BUFF_DIST"),
                         data.column1 = "actual",
                         data.column2 = "freq")

bufferByModeDF$expectedPct = ifelse(bufferByModeDF$count > 0,
                                    100*bufferByModeDF$expected/bufferByModeDF$count,
                                    0)

bufferByModeDF$actualPct = rangeBufferDF[rangeBufferDF$Mode == "Walk","bufferShare"]

bufferByModeDFLatex = as.data.frame(t(bufferByModeDF[,c("actualPct","expectedPct")]))
row.names(bufferByModeDFLatex) = c("Actual", "Expected")

## create scenarios for How Your School Compares
# total trips per buffer
bufferByModeDF$bufferTotal = rangeBufferDF[rangeBufferDF$Mode == "Auto","BufferTotal"]

if(sum(bufferByModeDF$expectedPct > bufferByModeDF$actualPct) > 0){
  # calculate extra walk trips needed to achieve expected walk share 
  # if walk share is already above expected, return 0
  bufferByModeDF$extraWalk = ifelse(bufferByModeDF$expectedPct > bufferByModeDF$actualPct,
                                    (bufferByModeDF$expectedPct - bufferByModeDF$actualPct)*bufferByModeDF$bufferTotal/100,
                                    0)
  # add auto share
  bufferByModeDF$autoTotal = rangeBufferDF[rangeBufferDF$Mode == "Auto","Estimate"]
  # calculate reduction in auto trips if walk share rose 
  # to expected levels
  bufferByModeDF$autoReduced = ifelse(bufferByModeDF$autoTotal > bufferByModeDF$extraWalk,
                                      bufferByModeDF$extraWalk,
                                      bufferByModeDF$autoTotal)
  
  dailyAutoReduce = round(sum(bufferByModeDF$autoReduce))
  newWalkers = sum(bufferByModeDF$extraWalk)/2
  totalMinutesWalking = sum(bufferByModeDF$extraWalk*(7.5*1:5))
  avgMinutesWalking = round(totalMinutesWalking/newWalkers)
  
  ghgReductionLowHigh = ghgReduction(bufferByModeDF$autoReduced)
  annualGHGreductionLow = ghgReductionLowHigh$ghgLow*180
  annualGHGreductionHigh = ghgReductionLowHigh$ghgHigh*180
  annualGHGreductionLowPct = 100*annualGHGreductionLow/totGhGest
  annualGHGreductionHighPct = 100*annualGHGreductionHigh/totGhGest
  annualGHGreductionLowText = thousands_sep(ghgReductionLowHigh$ghgLow*180)
  annualGHGreductionHighText = thousands_sep(ghgReductionLowHigh$ghgHigh*180)
  
  
  extraWalkTotal = sum(bufferByModeDF$extraWalk)
  
  scenarioText = 'If your school achieved the "expected" values described 
                  above based on grade specific averages for each walkshed, 
                  it would:'
}

if(sum(bufferByModeDF$expectedPct > bufferByModeDF$actualPct) == 0){
  # calculate extra walk trips needed to achieve expected walk share 
  # if walk share is already above expected, return 0
  bufferByModeDF$extraWalk = ifelse(bufferByModeDF$actualPct + 25 < 100,
                                    25*bufferByModeDF$bufferTotal/100,
                                    (100 - bufferByModeDF$actualPct)*bufferByModeDF$bufferTotal/100)
  # add auto share
  bufferByModeDF$autoTotal = rangeBufferDF[rangeBufferDF$Mode == "Auto","Estimate"]
  # calculate reduction in auto trips if walk share rose 
  # by 25%
  bufferByModeDF$autoReduced = ifelse(bufferByModeDF$autoTotal > bufferByModeDF$extraWalk,
                                      bufferByModeDF$extraWalk,
                                      bufferByModeDF$autoTotal)
  
  dailyAutoReduce = round(sum(bufferByModeDF$autoReduce))
  newWalkers = sum(bufferByModeDF$extraWalk)/2
  totalMinutesWalking = sum(bufferByModeDF$extraWalk*(7.5*1:5))
  avgMinutesWalking = totalMinutesWalking/newWalkers
  
  ghgReductionLowHigh = ghgReduction(bufferByModeDF$autoReduced)
  annualGHGreductionLow = ghgReductionLowHigh$ghgLow*180
  annualGHGreductionHigh = ghgReductionLowHigh$ghgHigh*180
  annualGHGcurrent = sum(as.numeric(ghgBufferDFgeneric$ghgEst))
  annualGHGreductionLowPct = 100*annualGHGreductionLow/totGhGest
  annualGHGreductionHighPct = 100*annualGHGreductionHigh/totGhGest
  annualGHGreductionLowText = thousands_sep(ghgReductionLowHigh$ghgLow*180)
  annualGHGreductionHighText = thousands_sep(ghgReductionLowHigh$ghgHigh*180)
  
  extraWalkTotal = sum(bufferByModeDF$extraWalk)
  
  scenarioText = "If you school increase walk\\textbackslash bikeshare rates by 25\\% in each 
  walkshed, it would:"
}


# calculate GHG emission reduction

bufferByModeDF = mergeDF(bufferByModeDF,
                         count(DF[DF$ModeFromMod == "Walk",],
                               .(BUFF_DIST)),
                         by.x = c("Buffer"),
                         by.y = c("BUFF_DIST"),
                         data.column1 = "actual",
                         data.column2 = "freq")



################### End  How Your School Compares ########################

#save.image()





