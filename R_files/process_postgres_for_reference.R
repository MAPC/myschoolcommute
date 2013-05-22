############### Begin Process PostGres Section ###################
# process_postgres reads postGres table to data frame DF
# It relabels the to_school and from_school columns; 
# creates the to_school_simple and from_school_simple columns

library(RPostgreSQL)

# establish connection to PostgreSQl;
# fetch survey table and write to variable DF
# ch <- odbcConnect("PostgreSQL30",pwd = "max1max2")
# DF <- sqlFetch(ch,"survey_child")
drv <- dbDriver("PostgreSQL")
ch <- dbConnect(drv, 
                host='localhost',
                port='5432', 
                dbname='postgres',
                user='postgres',
                password='max1max2')
DF <- dbSendQuery(ch,"select * from survey_child")
DF <- fetch(DF,n=-1)

## Rename columns to match previous code
names(DF)[grep("to_school",names(DF))] <- "ModeTo"
names(DF)[grep("from_school",names(DF))] <- "ModeFrom"
names(DF)[grep("dropoff",names(DF))] <- "DropOff"
names(DF)[grep("pickup",names(DF))] <- "PickUp"

########### Temporary Section ###############
# The following code should not be necessary once 
# schema is finalized with developer; this section adds
# 0) ORG_CODE
# 1) BUFF_DIST column with fake buffers and
# 2) NEAR_DIST column with fake distances
# 3) Licenses colum with fake number of licensed drivers
# 4) Vehicles column with fake number of vehicles

# 0) ORG_CODE <- ORG_CODE
ORG_CODE <- ORG_CODE
# 1)
# add fake buffer column to DF
buffers <- c("0.5","1.0","1.5","2.0","2.0+",NA)
DF$BUFF_DIST <- as.factor(sample(buffers,nrow(DF),
                                 prob = c(.40,.20,.20,.10,0.10,0),
                                 replace=TRUE))

# 2)
# add fake NEAR_DIST data
num_15_plus <- sum(DF$BUFF_DIST=="2.0+",na.rm=T) # num_15_plus = number of 2.0+ records
near_dist_rand <- runif(num_15_plus,min=0.01,max=4) # NEAR_DIST values for 2.0+ buffer values
DF$NEAR_DIST <- vector(length = nrow(DF),mode = "numeric") # create numeric column callued NEAR_DIST
DF[DF$BUFF_DIST=="2.0+" & !is.na(DF$BUFF_DIST),"NEAR_DIST"] <- near_dist_rand # add NEAR_DIST values > 0 to records in 1.5+ buffer
DF$Licenses <- vector(length = nrow(DF),mode = "numeric")
DF$Licenses <- sample(c(0:4,""),nrow(DF),replace = TRUE)
DF$Vehicles <- vector(length = nrow(DF),mode = "numeric")
DF$Vehicles <- sample(c(0:4,""),nrow(DF),replace = TRUE)
# DF$ModeTo <- sample(levels(DF$ModeTo),nrow(DF),replace = TRUE)
# DF$ModeFrom <- sample(levels(DF$ModeFrom),nrow(DF),replace = TRUE)
# DF$PickUp <- sample(levels(DF$PickUp),nrow(DF),replace = TRUE)
# DF$DropOff <- sample(levels(DF$DropOff),nrow(DF),replace = TRUE)
############### End Temporary Section ##############

# Relabel the levels of ModeTo and ModeFrom
DF$ModeTo <- mode_labels(DF$ModeTo)
DF$ModeFrom <- mode_labels(DF$ModeFrom)

# Create ModeToMod and ModeFromMod
DF$ModeToMod <- mode_simple(DF$ModeTo)
DF$ModeFromMod <- mode_simple(DF$ModeFrom)

# Reorder DF$grades
DF$grade <- grade_reorder(DF$grade)
# End Reorder DF$grades

############### End Process PostGres Section ###################

############### Begin Participation by Grade Section ###################
enrollDF <- enroll_df()
enrollTotals  <- enroll_totals(Enrollment,ORG_CODE)
enrollDF <- mergeDF(enrollDF,
                    count(DF,.(grade)),
                    data.column1 = "Surveyed",
                    data.column2 = "freq",
                    by.x = c("Grade"),
                    by.y = c("grade"))
enrollDF <- mergeDF(enrollDF,
                    enrollTotals,
                    data.column1 = "Enroll",
                    data.column2 = "value",
                    by.x = c("Grade"),
                    by.y = c("variable"))
enrollDF <- enrollDF[enrollDF$Enroll!=0,]
enrollDF$Grade <- droplevels(enrollDF$Grade)
enrollDF$Pct <- 100*enrollDF$Surveyed/enrollDF$Enroll

enrollDF$NotSurveyd <- enrollDF$Enroll - enrollDF$Surveyed
enrollDFmelt <- melt(enrollDF,
                     measure.vars=c("Surveyed","NotSurveyd"))

############### Begin Mode Choice Section ###################
############### Begin Mode Choice And Proximity to School Section ###################
## Create data frame modeDF count tables t1 and t2 
t1 <- count(DF,.(ModeToMod,BUFF_DIST))
t2 <- count(DF,.(ModeFromMod,BUFF_DIST))

modeDF <- create_mode_by_buffer_df()

## Add counts from t1 and t2 to Freq column of modeDF

modeDF <- mergeDF(modeDF,
                  t1,
                  data.column1 = "Freq",
                  data.column2 = "freq",
                  by.x = c("Mode","Buffer"),
                  by.y = c("ModeToMod","BUFF_DIST"))

modeDFMorning <- modeDF
modeDFMorning$Est <- round(modeDFMorning$Freq*Enroll_Total/sum(modeDFMorning$Freq),digits=0)
t(modeDFMorning)
modeDFMorningWide <- modeDFwideFunction(modeDFMorning)
modeDFMorningWideLatex <- cbind(modeDFMorningWide[,1],
                            lapply(modeDFMorningWide[,2:6],as.character),
                            modeDFMorningWide[,7:11])
names(modeDFMorningWideLatex)[1] <- ""
busEligibleDrivenCount <- sum(modeDFMorningWide[1,c("2.0","2.0+")])
busEligibleCount <- sum(modeDFMorningWide[4,c("2.0","2.0+")])
busEligibleDrivenPct <- round(100*busEligibleDrivenCount/busEligibleCount,0)



modeDF <- mergeDF(modeDF,
                  t2,
                  data.column1 = "Freq",
                  data.column2 = "freq",
                  by.x = c("Mode","Buffer"),
                  by.y = c("ModeFromMod","BUFF_DIST"))

modeDF$Freq <- round(modeDF$Freq/2,0)
modeDF$Est <- round(modeDF$Freq*Enroll_Total/sum(modeDF$Freq),digits=0)
modeDF$DiffEstSurvey <- modeDF$Est - modeDF$Freq

modeDFWide <- modeDFwideFunction(modeDF)

## calculate students per buffer

bufferDF <- ddply(modeDF,
                  .(Buffer),
                  summarise,
                  Freq = sum(Freq),
                  DiffEstSurvey = sum(DiffEstSurvey),
                  Est = sum(Est))

bufferDF$Pct = bufferDF$Est/sum(bufferDF$Est)

bufferDFmelt <- melt(bufferDF,measure.var = c("Freq","DiffEstSurvey"))

## convert bufferDF from wide to long for Latex table
bufferDFLatex <- as.data.frame(t(bufferDF[,c("Est","Pct")]))
names(bufferDFLatex) <- buffers[1:(length(buffers)-1)]                      
bufferDFLatex[2,] <- addPct(100*bufferDFLatex[2,])        

## Get numbers for report
Sample_Size <- nrow(DF)
Total_Students <- sum(modeDFWide[4,2:(numBuffers+1)])
ResponsePct <- round(100*Sample_Size/Total_Students,0)
Total_Walk <- sum(modeDFWide[3,2:(numBuffers+1)]) 
oneMileWalk <- sum(modeDFWide[3,2:3]) 
Total_Car <- sum(modeDFWide[1,2:(numBuffers+1)])
oneMileSchool <- sum(modeDFWide[4,c("0.5","1.0")])
oneMileSchoolPct <- round(100*oneMileSchool/Total_Students,0)
oneMileSchoolRatio <- oneMileSchool/Total_Students
twoMileSchool <- sum(modeDFWide[4,c("0.5","1.0","1.5","2.0")])
twoMileSchoolPct <- round(100*twoMileSchool/Total_Students,0)
walkSchoolPct <- round(100*Total_Walk/Total_Students,0)
carSchoolPct <- round(100*Total_Car/Total_Students,0)
walkSchoolOneMileRatio <- oneMileWalk/oneMileSchool
walkSchoolRatio <- Total_Walk/Total_Students
autoOneMileSchoolPct <- round(100*sum(modeDFWide[1,c("0.5","1.0")])/oneMileSchool,0)
autoOneMileSchoolRatio <- sum(modeDFWide[1,c("0.5","1.0")])/oneMileSchool
autoOneMileAllSchoolsPct <- round(100*sum(aSmodeDFWide[1,c("0.5","1.0")])/sum(aSmodeDFWide[4,c("0.5","1.0")]),0)
autoOneMileAllSchoolsRatio <- sum(aSmodeDFWide[1,c("0.5","1.0")])/sum(aSmodeDFWide[4,c("0.5","1.0")])



############### End Mode Choice And Proximity to School Section ###################

############### Begin Walk Potential Classification Section ###################
highProxhighWalk <- 
  "High proximity, high walk share schools are those where more than three quarters of students live within one mile walking distance of their school and at least one third of students walk or bike to school. At schools such as this, the mode shift potential of SRTS programs is somewhat limited because fewer than half of the proximate students are being driven."

UnTapped <- 
  "Untapped walk to school potential exists at schools where three quarters of students live within one mile walking distance, but fewer than a quarter walk to school. Even within a half mile, only 29\\% of students commute by walking or biking, on average. These schools represent the best potential for mode shift as a result of SRTS programs, given the large number of proximate auto commuters. Shifting these trips to  walking or biking could have major effects on school-wide mode share."

DispEnroll <- 
  "At schools with dispersed enrollment and limited walk potential, most students live beyond a mile from school. As a result, the potential walk mode share is very limited, and walk to school programs will be relevant to a minority of students. Infrastructure improvements to expand the reach of the walkshed may have some effect on the size of the proximate student population, but efforts to shift distant commutes from car to bus might be more effective at reducing GHG emissions."
"High proximity, high walk share"

TypeText <- ifelse(oneMileSchoolRatio > .75 & walkSchoolRatio > .33, highProxhighWalk,
                   ifelse(oneMileSchoolRatio > .75 & walkSchoolRatio < .33, UnTapped,
                          DispEnroll))

SchoolTypeSentence <-  ifelse(TypeText == highProxhighWalk,
                              "High proximity, high walk share",
                              ifelse(TypeText == UnTapped, "Untapped Walk Potential",
                                     "Dispersed Enrollment, Limited Walk Potential"))

TypeParagraphFirstSentence <- paste("\\emph{",as.character(School_Name[[1]])," is a ", SchoolTypeSentence," school}.",sep="")
TypeParagraph <- paste(TypeParagraphFirstSentence,
                       TypeText)


############### End Walk Potential Classification Section ###################


############### Begin Walk Potential Graph Section ###################

## create Student Proximity and Walk/Bike Share plot from page 4
## of report

WalkPotentialSchool <- list(School = as.character(School_Name),
                            Total = Total_Students,
                            MileCount = oneMileSchool,
                            WalkCount = Total_Walk,
                            MilePct = oneMileSchoolRatio,
                            WalkPct = walkSchoolRatio)
WalkPotentialForPlot <- rbind(walkPotentialDF,
                              WalkPotentialSchool)
WalkPotentialForPlot$Label <- c(rep(0,times=22),1)

############## 
## find minimum and maximum values for x and y axis
minMilePct <- min(WalkPotentialForPlot$MilePct)
minMilePct <- roundToNearest(minMilePct,.1)
maxWalkPct <- max(WalkPotentialForPlot$WalkPct)
maxWalkPct <- roundToNearest(maxWalkPct,.1) + .1
meanMilePct <- (1-minMilePct)/2
MilePctSchool <- WalkPotentialForPlot$MilePct[WalkPotentialForPlot$Label==1]
##############

############### End Walk Potential Graph Section ###################

############### Begin Mode Choice and Time of Day ###################
## This script generates the data.frame and graph that correspond to 
## page 15 in the SRTS report: mode by time of day

## mode levels is a character vector that contains all of the 
## modes that appear in either ModeTo or ModeFrom (or both)
modeLevels <- union(levels(as.factor(DF$ModeTo)),
                    levels(as.factor(DF$ModeFrom)))

modeByTimeDf <- data.frame(mode = rep(modeLevels,each = 2),
                           time = rep(c("Morning","Afternoon"),
                                      times = length(modeLevels)),
                           count = rep(0,times = 2*length(modeLevels)))

modeByTimeDf[modeByTimeDf$time == "Morning",] <-
  mergeDF(modeByTimeDf[modeByTimeDf$time == "Morning",],
          count(DF,.(ModeTo)),
          by.x = "mode",
          by.y = "ModeTo",
          data.column1 = "count",
          data.column2 = "freq")

modeByTimeDf[modeByTimeDf$time == "Afternoon",] <-
  mergeDF(modeByTimeDf[modeByTimeDf$time == "Afternoon",],
          count(DF,.(ModeFrom)),
          by.x = "mode",
          by.y = "ModeFrom",
          data.column1 = "count",
          data.column2 = "freq")

modeByTimeDf$pct <- modeByTimeDf$count/sum(modeByTimeDf$count/2)
modeByTimeDf <- ddply(modeByTimeDf,
                      .(mode),
                      transform,
                      order = mean(pct))
modeByTimeDf$mode <- reorder(modeByTimeDf$mode,-1*modeByTimeDf$order)

autoMorningPct <- round(sum(100*subset(modeByTimeDf,(mode=="Family Vehicle" | mode=="Carpool") & time =="Morning")$pct))
autoAfternoonPct <- round(sum(100*subset(modeByTimeDf,(mode=="Family Vehicle" | mode=="Carpool") & time =="Afternoon")$pct))
famVehMorningPct <- round(100*subset(modeByTimeDf,mode=="Family Vehicle" & time =="Morning")$pct)
famVehAfternoonPct <- round(100*subset(modeByTimeDf,mode=="Family Vehicle" & time =="Afternoon")$pct)                      
famVehMorningCount <- subset(modeByTimeDf,mode=="Family Vehicle" & time =="Morning")$count
famVehAfternoonCount <- subset(modeByTimeDf,mode=="Family Vehicle" & time =="Afternoon")$count
autoMorningPctNotRounded <- sum(100*subset(modeByTimeDf,(mode=="Family Vehicle" | mode=="Carpool") & time =="Morning")$pct,1)
autoAfternoonPctNotRounded <- sum(100*subset(modeByTimeDf,(mode=="Family Vehicle" | mode=="Carpool") & time =="Afternoon")$pct,1)

autoMorningvAfternoon <- ifelse(autoMorningPctNotRounded > autoAfternoonPctNotRounded,
                                "lower","higher")
walkMorningPct <- round(sum(100*subset(modeByTimeDf,mode=="Walk" & time =="Morning")$pct),1)
walkAfternoonPct <- round(sum(100*subset(modeByTimeDf,mode=="Walk" & time =="Afternoon")$pct),1)
walkMorningCount <- subset(modeByTimeDf,mode=="Walk" & time =="Morning")$count
walkAfternoonCount <- subset(modeByTimeDf,mode=="Walk" & time =="Afternoon")$count
walkDiff <- walkAfternoonCount - walkMorningCount
carToWalkPct <- paste(round(100*(walkDiff/famVehMorningCount),0),"\\%",sep="")
walkMorningPctNotRounded <- sum(100*subset(modeByTimeDf,(mode=="Walk" | mode=="Bike") & time =="Morning")$pct)
walkAfternoonPctNotRounded <- sum(100*subset(modeByTimeDf,(mode=="Walk" | mode=="Bike") & time =="Afternoon")$pct)
walkMorningvAfternoon <- ifelse(walkMorningPctNotRounded > walkAfternoonPctNotRounded,
                                "lower","higher")
modeByTimeText <- ifelse(walkMorningvAfternoon == "higher" & autoMorningvAfternoon == "lower",
                         paste("The auto share is lower in the afternoon, indicating that as many as",
                               carToWalkPct,
                               "of those who are driven to school in the morning walk home in the afternoon."),"")
############### End Mode Choice and Time of Day ###################

############### Begin Trip Chaining  and Time of Day ###################
## Create data frame chainDF to hold data 
## for plotting
time <- rep(c("Morning","Afternoon"),each=2)
chain <- rep(c("no","yes"),times=2)
count <- rep(0,times=4)
chainDF <- data.frame(time = time,
                      chain = chain,
                      count = count)

## create data frame with Drop Off data for 
## joining to chainDF; do the same for PickUp data
dropOffDF <- count(DF,.(DropOff))
dropOffDF$time <- "Morning"
pickUpDF <- count(DF,.(PickUp))
pickUpDF$time <- "Afternoon"

chainDF <- mergeDF(chainDF,
                   dropOffDF,
                   data.column1 = "count",
                   data.column2 = "freq",
                   by.x = c("chain","time"),
                   by.y = c("DropOff","time"))

chainDF <- mergeDF(chainDF,
                   pickUpDF,
                   data.column1 = "count",
                   data.column2 = "freq",
                   by.x = c("chain","time"),
                   by.y = c("PickUp","time"))

chainDF$est <- round(Enroll_Total*chainDF$count/Sample_Size, 0)
chainDF$time <- reorder(chainDF$time,
                        rep(c(2,1),times=2))
chainDF$chain <- revalue(chainDF$chain,
                         c("no" = "Dedicated",
                           "yes" = "En Route"))

enRouteMorningCount <- chainDF$est[chainDF$chain == "En Route" &
                                     chainDF$time == "Morning"]
MorningCount <- sum(chainDF$est[chainDF$time == "Morning"])
enRouteAfternoonCount <- chainDF$est[chainDF$chain == "En Route" &
                                     chainDF$time == "Afternoon"]
AfternoonCount <- sum(chainDF$est[chainDF$time == "Afternoon"])
enRouteMorningPct <- round(100*enRouteMorningCount/MorningCount)
enRouteAfternoonPct <- round(100*enRouteAfternoonCount/AfternoonCount)


############### End Trip Chaining  and Time of Day ###################

############### Begin Mode By Vehicle Available and Time of Day ###################

## create availDF to hold the data for Mode By 
## Time and Vehicle Availability; then copy availDF
## as availLowDF and availHighDF
Time <- rep(c("Morning","Afternoon"),each=7)
ModeList <- c("Family vehicle Dedicated",
              "Family vehicle En Route",
              "Carpool Dedicated",
              "Carpool En Route",
              "School Bus",
              "Transit",
              "Walk")

Mode <- rep(ModeList,
            times=2)

availDF <- data.frame(Time = Time,
                      Mode = as.character(Mode),
                      Count = 0)

availLowDF <- availDF
availHighDF <- availDF
##############################

availToDF <- count(DF,.(Licenses,Vehicles,ModeTo,DropOff))
availToDF <- subset(availToDF,Licenses!="" & Vehicles != "")
availToDF$ModeTo <- as.character(availToDF$ModeTo)
availToDF$Mode <- ifelse(availToDF$ModeTo == "Carpool" & availToDF$DropOff == "no",
                         "Carpool Dedicated",
                         ifelse(availToDF$ModeTo == "Carpool" & availToDF$DropOff == "",
                                NA,
                                ifelse(availToDF$ModeTo == "Carpool" & availToDF$DropOff == "yes",
                                       "Carpool En Route",
                                       ifelse(availToDF$ModeTo == "Family Vehicle" & availToDF$DropOff == "no",
                                              "Family vehicle Dedicated",
                                              ifelse(availToDF$ModeTo == "Family Vehicle" & availToDF$DropOff == "",
                                                     NA,
                                                     ifelse(availToDF$ModeTo == "Family Vehicle" & availToDF$DropOff == "yes",
                                                            "Family vehicle En Route",
                                                            availToDF$ModeTo))))))


availToLowDF <- subset(availToDF,Vehicles == 0 |Licenses > Vehicles)
availToHighDF <- subset(availToDF, Vehicles != 0 & Licenses <= Vehicles)
availToLowDF <- ddply(availToLowDF,
                      .(Mode),
                      summarise,
                      freq = sum(freq))

availToHighDF <- ddply(availToHighDF,
                       .(Mode),
                       summarise,
                       freq = sum(freq))

availFromDF <- count(DF,.(Licenses,Vehicles,ModeFrom,PickUp))
availFromDF <- subset(availFromDF,Licenses!="" & Vehicles != "")
availFromDF$ModeFrom <- as.character(availFromDF$ModeFrom)
availFromDF$Mode <- ifelse(availFromDF$ModeFrom == "Carpool" & availFromDF$PickUp== "no",
                           "Carpool Dedicated",
                           ifelse(availFromDF$ModeFrom == "Carpool" & availFromDF$PickUp== "",
                                  NA,
                                  ifelse(availFromDF$ModeFrom == "Carpool" & availFromDF$PickUp== "yes",
                                         "Carpool En Route",
                                         ifelse(availFromDF$ModeFrom == "Family Vehicle" & availFromDF$PickUp== "no",
                                                "Family vehicle Dedicated",
                                                ifelse(availFromDF$ModeFrom == "Family Vehicle" & availFromDF$PickUp== "",
                                                       NA,
                                                       ifelse(availFromDF$ModeFrom == "Family Vehicle" & availFromDF$PickUp== "yes",
                                                              "Family vehicle En Route",
                                                              availFromDF$ModeFrom))))))

availFromLowDF <- subset(availFromDF,Vehicles == 0 |Licenses > Vehicles)
availFromLowDF <- ddply(availFromLowDF,
                        .(Mode),
                        summarise,
                        freq = sum(freq))
availFromHighDF <- subset(availFromDF, Vehicles != 0 & Licenses <= Vehicles)
availFromHighDF <- ddply(availFromHighDF,
                         .(Mode),
                         summarise,
                         freq = sum(freq))

availLowDF[Time == "Morning",] <-
  mergeDF(availLowDF[Time == "Morning",],
          availToLowDF,
          data.column1 = "Count",
          data.column2 = "freq",
          by.x = "Mode",
          by.y = "Mode")

availLowDF[Time == "Afternoon",] <-
  mergeDF(availLowDF[Time == "Afternoon",],
          availFromLowDF,
          data.column1 = "Count",
          data.column2 = "freq",
          by.x = "Mode",
          by.y = "Mode")


availHighDF[Time == "Morning",] <-
  mergeDF(availHighDF[Time == "Morning",],
          availToHighDF,
          data.column1 = "Count",
          data.column2 = "freq",
          by.x = "Mode",
          by.y = "Mode")

availHighDF[Time == "Afternoon",] <-
  mergeDF(availHighDF[Time == "Afternoon",],
          availFromHighDF,
          data.column1 = "Count",
          data.column2 = "freq",
          by.x = "Mode",
          by.y = "Mode")

##### Add estimate columns
availLowDF <-  ddply(availLowDF,
                     .(Time),
                     transform,
                     est = round(Enroll_Total*Count/sum(Count),0))

availHighDF <-  ddply(availHighDF,
                      .(Time),
                      transform,
                      est = round(Enroll_Total*Count/sum(Count),0))

availLowDF <-   ddply(availLowDF,
                      .(Time),
                      transform,
                      pct = 100*est/sum(est))

availHighDF <-   ddply(availHighDF,
                       .(Time),
                       transform,
                       pct = 100*est/sum(est))

availLowDFwide <- dcast(melt(availLowDF, id.vars=c("Mode", "Time")),
                        Mode ~ Time,
                        subset = .(variable == "pct"))

availHighDFwide <- dcast(melt(availHighDF, id.vars=c("Mode", "Time")),
                        Mode ~ Time,
                        subset = .(variable == "pct"))

availDFwide <- cbind(availLowDFwide[c("Mode","Morning","Afternoon")],
                     availHighDFwide[c("Morning","Afternoon")])

availDFwide$Mode <- reorder(availDFwide$Mode,apply(availDFwide[,2:5],1,sum))
orderRows <- order(apply(availDFwide[,2:5],1,sum,na.rm=T),decreasing=TRUE)
availDFwidePctFormat <- cbind(availDFwide[,1],pctFormat(availDFwide[,2:5]))[orderRows,]
names(availDFwidePctFormat) <- names(availDFwide)

## Get numbers for report
lowVehicleHHs <- sum(availToLowDF$freq)
highVehicleHHs <- sum(availToHighDF$freq)
lowVehicleHHsPct <- round(100*lowVehicleHHs/(lowVehicleHHs + highVehicleHHs)
                          ,0)
lowVehicleWalkPctTo <- sum(availLowDF$pct[availLowDF$Time=="Morning" &
                                            availLowDF$Mode %in% c("School Bus",
                                                                   "Transit",
                                                                   "Walk")])
lowVehicleWalkPctTo <- round(lowVehicleWalkPctTo,0)

lowVehicleWalkPctFrom <- sum(availLowDF$pct[availLowDF$Time=="Afternoon" &
                                            availLowDF$Mode %in% c("School Bus",
                                                                   "Transit",
                                                                   "Walk")])
lowVehicleWalkPctFrom <- round(lowVehicleWalkPctFrom,0)

highVehicleWalkPctTo <- sum(availHighDF$pct[availHighDF$Time=="Morning" &
                                              availHighDF$Mode %in% c("School Bus",
                                                                   "Transit",
                                                                   "Walk")])
highVehicleWalkPctTo <- round(highVehicleWalkPctTo,0)

highVehicleWalkPctFrom <- sum(availHighDF$pct[availHighDF$Time=="Afternoon" &
                                                availHighDF$Mode %in% c("School Bus",
                                                                     "Transit",
                                                                     "Walk")])
highVehicleWalkPctFrom <- round(highVehicleWalkPctFrom,0)


############### End Mode By Vehicle Available and Time of Day ###################

############### Begin GHG Section ###################
source("calculate_GHG.R")

ghgBufferDFgeneric <- data.frame(Buffer = buffers[1:(length(buffers)-1)],
                                 Students = 0,
                                 Ghg_Total = 0)

ghgBufferDF <- ddply(DF,
                     .(BUFF_DIST),
                     summarise,
                     students = length(id),
                     ghg_Total = 180*sum(ghg_Total))

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

ghgBufferDFgeneric$studentsEst <- round(Enroll_Total*ghgBufferDFgeneric$Students/(sum(ghgBufferDFgeneric$Students)),0)
ghgBufferDFgeneric$ghgEst <- ghgBufferDFgeneric$studentsEst*ghgBufferDFgeneric$Ghg_Total/ghgBufferDFgeneric$Students
ghgBufferDFgeneric$ghgEstPerCap <- ghgBufferDFgeneric$ghgEst/ghgBufferDFgeneric$studentsEst
ghgBufferDFgeneric$PctTotGHG <- ghgBufferDFgeneric$ghgEst/sum(ghgBufferDFgeneric$ghgEst)

ghgPerCap10Buffer <-
  (sum(ghgBufferDFgeneric$ghgEstPerCap[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")]*
         ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")]))/
  sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("0.5","1.0")])

ghgPerCap10PlusBuffer <-
  (sum(ghgBufferDFgeneric$ghgEstPerCap[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")]*
         ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")]))/
  sum(ghgBufferDFgeneric$studentsEst[ghgBufferDFgeneric$Buffer %in% c("1.5","2.0","2.0+")])

ghgPerCap <- sum(ghgBufferDFgeneric$ghgEst)/sum(ghgBufferDFgeneric$studentsEst)


ghgBufferDFgeneric$PctTotGHGprint <- addPct(100*ghgBufferDFgeneric$PctTotGHG)
ghgBufferDFgeneric$ghgEst <- round(ghgBufferDFgeneric$ghgEst,0)
ghgBufferDFgeneric$ghgEstPerCap <- round(ghgBufferDFgeneric$ghgEstPerCap,0)
ghgBufferDFgeneric[,2:6] <- lapply(ghgBufferDFgeneric[,2:6],as.character)

## Average Distance To School
avgDistToSchool <- mean(DF$distEst,na.rm=TRUE)

## Peer School Comparison Section

## calculate range within one mile for peer schools
## pSdF == %peer %School %data %Frame
pSdF <- compareSchTable(allSchComp,maxRange)
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

## predict percent 
## Closes connection

dbDisconnect(ch)


