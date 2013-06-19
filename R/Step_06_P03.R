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
gmSbse_df <- gmbse_df_create() 

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
                                "lower","higher")
carMorningvAfternoon <- ifelse(carTripMorningPct > carTripAfternoonPct,
                                "lower","higher")

carTripMorningPct <- paste(round(100*(carTripMorningCount-carTripAfternoonCount)/carTripMorningCount,1),"\\%",sep="")
modeByTimeText <- ifelse(walkMorningvAfternoon == "higher" & carMorningvAfternoon == "lower",
                         paste("The auto share is lower in the afternoon, indicating that as many as ",
                               carTripMorningPct,
                               " of those who are driven to school in the morning get home by other means in the afternoon.",sep=""))
