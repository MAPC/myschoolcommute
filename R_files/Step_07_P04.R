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
gbmTS_df_temp <- count(DF,.(grade,BUFF_DIST,ModeToMod))

# 3 
# fill in Surveyed column in gbse_df

gmSbse_df <- mergeDF(gmSbse_df,
                     gbmTS_df_temp,
                     data.column1 = "Surveyed",
                     data.column2 = "freq",
                     by.x = c("Grade","Buffer","Mode"),
                     by.y = c("grade","BUFF_DIST","ModeToMod"))

# 3: 
# Add Column:
# Grade_Surveyed = Total Students Surveyed By Grade
gmSbse_df <- ddply(gmSbse_df,
                   .(Grade),
                   transform,
                   Grade_Surveyed = sum(Surveyed))

# 4: 
# Merge gmSbse_df with et_df: Enrollment by Grade
# Fills
# Column
# Enroll
gmSbse_df <- mergeDF(gmSbse_df,
                     et_df,
                     data.column1 = "Enroll",
                     data.column2 = "value",
                     by.x = "Grade",
                     by.y = "variable")

gmSbse_df <-  subset(gmSbse_df,Enroll > 0)
gmSbse_df <-  droplevels(gmSbse_df)


# 6:
# Sum students by buffer
mSb_df <- ddply(gmSbse_df,
                .(Mode,Buffer),
                summarise,
                Estimate = sum(Surveyed*Enroll/Grade_Surveyed,na.rm=T))


