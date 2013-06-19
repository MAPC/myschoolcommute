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
et_df <- enroll_totals(Enrollment,ORG_CODE)

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
g_df$Grade <- droplevels(g_df$Grade)

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

# Factoids
sampleSize <- sum(g_df$Surveyed)
enrollTotal <- sum(g_df$Enroll)
surveyPct <- round(100*sampleSize/enrollTotal,0)
