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
                dbname=dbname,
                user=dbuser,
                password=dbpasswd)
DF <- dbSendQuery(ch,"select * from survey_child_survey")
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
#ORG_CODE <- 1859
# 1)
# add fake buffer column to DF
#buffers <- c("0.5","1.0","1.5","2.0","2.0+")
#DF$BUFF_DIST <- as.factor(sample(buffers,nrow(DF),
#                                 prob = c(.40,.20,.20,.15,0.05),
#                                 replace=TRUE))

# 2)
# add fake NEAR_DIST data
#num_15_plus <- sum(DF$BUFF_DIST=="2.0+",na.rm=T) # num_15_plus = number of 2.0+ records
#near_dist_rand <- runif(num_15_plus,min=0.01,max=4) # NEAR_DIST values for 2.0+ buffer values
#DF$NEAR_DIST <- vector(length = nrow(DF),mode = "numeric") # create numeric column callued NEAR_DIST
#DF[DF$BUFF_DIST=="2.0+" & !is.na(DF$BUFF_DIST),"NEAR_DIST"] <- near_dist_rand # add NEAR_DIST values > 0 to records in 1.5+ buffer
#DF$Licenses <- vector(length = nrow(DF),mode = "numeric")
#DF$Licenses <- sample(c(0:4,""),nrow(DF),replace = TRUE)
#DF$Vehicles <- vector(length = nrow(DF),mode = "numeric")
#DF$Vehicles <- sample(c(0:4,""),nrow(DF),replace = TRUE)
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

## Closes connection

dbDisconnect(ch)


