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

# 6:
# Sum students by buffer
mSb_df_morning <- ddply(gmSbse_df_morning,
                        .(Mode,Buffer),
                        summarise,
                        Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))

mSb_df_afternoon <- ddply(gmSbse_df_afternoon,
                          .(Mode,Buffer),
                          summarise,
                          Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))

mSb_df_morning$time <- "Morning"
mSb_df_afternoon$time <- "Afternoon"

mSb_df <- rbind(mSb_df_morning,mSb_df_afternoon)

