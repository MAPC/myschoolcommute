# buffers
buffers <- c("0.5","1.0","1.5","2.0","2.0+")
grades <- c("p","k","1","2","3","4","5","6","7","8","9","10","11","12")
modes <- c("Bike","Carpool","Family Vehicle","School Bus","Transit","Walk")
modeSimple <- c("Auto","School Bus","Walk")
times <- c("Morning","Afternoon")

# grade_order
# inputs: DF$grades
# outpus: DF$grades, with factor levels in correct order
grade_reorder <- function(x){
  grade_ordered <- factor(x,
                     levels=grades)
  grade_ordered <- droplevels(grade_ordered)
  return(grade_ordered)
}

# enroll_df creates a data frame to store enrollment data for 
# graphing 
enroll_df <- function(){
  data.frame(Grade = grades,
             Surveyed = 0,
             Enroll = 0,
             Pct = 0)
}

# creates data frame with
# columns:
# Grade
# Buffer
# Survey
# Enroll
gbse_df_create <- function(){
  gbse_df <- data.frame(Grade = rep(grades, times = 5),
                        Buffer = rep(buffers,each=length(grades)),
                        Surveyed = 0,
                        NotSurveyed = 0,
                        Enroll = 0,
                        Pct = 0)
  gbse_df$Grade <- grade_reorder(gbse_df$Grade)
  return(gbse_df)
}

# creates data frame with
# columns:
# Grade
# Mode
# Time
# Enroll
gmbse_df_create <- function(){
  gmbse_df <- data.frame(Grade = rep(grades, times = length(times)*length(buffers)*length(modes)),
                         Buffer = rep(rep(rep(buffers,each=length(grades)),times=length(modes)),times=length(times)),
                         Mode = rep(rep(modes,each=length(buffers)*length(grades)),times=length(times)),
                         Time = rep(times,each = length(buffers)*length(grades)*length(modes)),
                         Surveyed = 0,
                         Enroll = 0,
                         Pct = 0)
  return(gmbse_df)
}

# creates data frame with
# columns:
# Grade
# Mode
# Time
# Enroll
gmSbse_df_create <- function(){
  gmbse_df <- data.frame(Grade = rep(grades, times = length(buffers)*length(modeSimple)),
                         Buffer = rep(rep(buffers,each=length(grades)),times=length(modeSimple)),
                         Mode = rep(modeSimple,each=length(buffers)*length(grades)),
                         Surveyed = 0,
                         Enroll = 0,
                         Pct = 0)
  return(gmbse_df)
}
enroll_totals <- function(x=Enrollment,school_code = ORG_CODE){
  enrollment <- melt(x[x$ORG.CODE == school_code,
                       c(grep("SCHOOL",names(x)),
                         grep("PK",names(x)):
                           grep("X12",names(x)))],
                     id = "SCHOOL")
  enrollment$variable <- c("p","k",1:12)
  return(enrollment)
}

# mode_labels
# inputs: required: DF$to_school or DF$from_school
# output: factor with original levels replaced with new levels
mode_labels <- function(x){
  require(car)
  x_recode <- car::recode(x,"'b' = 'Bike';
                          'cp' = 'Carpool';
                          'fv' = 'Family Vehicle';
                          'sb' = 'School Bus';
                          't' = 'Transit';
                          'w' = 'Walk'")
  return(x_recode)
}

# mode_simple
# Inputs: DF$to_school or DF$from_school
# Output: factor with original levels replaced with fewer, simpler levels
mode_simple <- function(x){
  require(car)
  x_recode <- car::recode(x,"  
                        'Bike' = 'Walk';
                        'Carpool' = 'Auto';
                        'Family Vehicle' = 'Auto';
                        'School Bus' = 'School Bus';
                        'Transit' = 'School Bus';
                        'Walk' = 'Walk'
                     ")
  return(x_recode)
}

##### Mode Choice and Proximity to School ##############

# create_mode_by_buffer_df
# Inputs: None
# Outputs: mode_by_buffer_df, a data frame that will hold data for 
#          tables on page 2 of report
create_mode_by_buffer_df <- function(){
  mode_by_buffer_df <- data.frame(Mode = rep(c("Auto","School Bus","Walk"),
                                             each = 5),
                                  Buffer = rep(c("0.5","1.0","1.5","2.0","2.0+"), times = 3),
                                  Freq = rep(0,times=15))
  return(mode_by_buffer_df)
}

## MergeDF takes in two data frames. It merges them based 
## on the by.x and by.y variables; it then adds data.column1
## and data.column2 and saves the result to data.column1
## It returns a data.frame with the original columns of df1

mergeDF <- function(df1,
                    df2,
                    data.column1 = "Freq",
                    data.column2 = "freq",
                    by.x = c("Mode","Buffer"),
                    by.y = c("ModeTo","Buffer")){
  merged <- merge(df1,df2,by.x=by.x,by.y=by.y,all.x=TRUE)[c(names(df1),data.column2)]
  merged[data.column1] <- rowSums(merged[c(data.column1,
                                           data.column2)],
                                  na.rm = T)
  merged <- merged[names(df1)]
  return(merged)
}

## Calculate percents by column
pctByCol <- function(v,den=length(v)){
  100*v/v[den]
}

## Apply pctByCol and return data frame
pctByColDF <- function(DF){
  namesDF <- names(DF)
  DFpct <- as.data.frame(lapply(DF,pctByCol))
  names(DFpct) <- namesDF
  return(DFpct)
}

## Add percent to vector elements
addPct <- function(v,n=0){
  paste(round(v,n),"\\%",sep="")
}

## Apply pctByCol and return data frame
pctFormat <- function(DF){
  namesDF <- names(DF)
  DFpct <- as.data.frame(lapply(DF,addPct))
  names(DFpct) <- names(DF)
  return(DFpct)
}


## create graphing theme for ggplot
theme_minimal <- function(){
  theme_bw(base_size = 12,base_family="") %+replace%
    theme(plot.title = element_text(size = 16,
                                    hjust = 0),
          panel.border = element_blank(),
          axis.line = element_line(color="grey50", size = 0.1),
          panel.grid.major.x = element_blank(),
          panel.grid.major.y = element_line(size=.1),
          axis.ticks = element_line(color="grey50", size=0.1),
          legend.position = "bottom",
          legend.direction = "horizontal")
}

  
  
       
