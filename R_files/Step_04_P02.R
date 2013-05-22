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
gbse_df$NotSurveyed <- max(gbse_df$Enroll - gbse_df$Surveyed,
                           0)
gbse_df$Pct <- ifelse(gbse_df$Grade_Surveyed > 0,
                      gbse_df$Surveyed/gbse_df$Grade_Surveyed,
                      NA)

# 6:
# Sum students by buffer
b_df <- ddply(gbse_df,
              .(Buffer),
              summarise,
              Estimate = sum((Surveyed/Grade_Surveyed)*Enroll),
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
pctWithinOneMile <- round(100*estWithinOneMile/enrollTotal,0)
pctWithinTwoMile <- round(100*estWithinTwoMile/enrollTotal,0)
avgDistToSchool <- round(mean(DF$distEst,na.rm=TRUE),digits = 1)








