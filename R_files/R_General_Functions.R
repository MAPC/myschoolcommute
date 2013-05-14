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

## walkPotential creates walkPotentialDF
## DF needs to be a data frame with columns
## School = school names  (factor)
## BUFF_DIST = buffer (factor with values c("0.5","1.0","1.5","1.5+"))
## ModeToMod = mode to school (factor with values c("Auto","School bus","Walk"))
## ModeFromMod = mode from school (factor with values c("Auto","School bus","Walk"))
walkPotential <- function(DF){
  require(plyr)
  allSchoolCount <- count(DF,
                          .(School))
  
  allSchoolNearCount <- 
    count(DF[DF$BUFF_DIST %in% c("0.5","1.0"),],
          .(School))
  
  allSchoolWalkToCount <- 
    count(DF[DF$ModeToMod == "Walk",],
          .(School))
  
  allSchoolWalkFromCount <- 
    count(DF[DF$ModeFromMod == "Walk",],
          .(School))
  
  allSchoolWalkCount <- merge(allSchoolWalkToCount,
                              allSchoolWalkFromCount,
                              by.x = "School",
                              by.y = "School")
  
  allSchoolWalkCount$WalkCount <- round(apply(allSchoolWalkCount[,2:3],1,sum)/2,0)
  
  walkPotential <- merge(allSchoolCount,
                         allSchoolNearCount,
                         by.x="School",
                         by.y="School")
  names(walkPotential)[2:3] <- c("Total","MileCount")
  
  walkPotentialNames <- names(walkPotential)
  walkPotential <- merge(walkPotential,
                         allSchoolWalkCount,
                         by.x="School",
                         by.y="School")[c(walkPotentialNames,"WalkCount")]
  
  walkPotential$MilePct <- walkPotential$MileCount/walkPotential$Total
  walkPotential$WalkPct <- walkPotential$WalkCount/walkPotential$Total
  
  return(walkPotential)
}

## combine school walk potential with all school walk potential to 
## get walk potential for plot WalkPotentialForPlot

walkPotentialDFforPlot <- function(modeDF,walkPotentialDF){
  withinOneMile <- sum(modeDF$Freq)[modeDF$Buffer %in% c("0.5","1.0")]
  Total <- sum(modeDF$Freq)
  WalkCount <- sum(modeDF$Freq)[modeDF$Mode == "Walk"]
  MilePct <- withinOneMile/Total
  WalkPct <- WalkCount/Total
  walkPotentialForPlot <- rbind(c(School_Name,Total,withinOneMile,WalkCount,MilePct,WalkPct),
                                WalkPotentialSchool)
  return(walkPotentialForPlot)
}

## 
roundToNearest <- function(x,n){
  return(x - x%%n)
}

## Rename ModeTo/ModeFrom levels
## renameMode takes in a ModeTo/ModeFrom column
## it then renames the levels to "Carpool", "Family Vehicle",
## "Other", "School bus", "Transit", "Walk"

renameMode <- function(x){
  x[grep("Carpool",x)] <- "Carpool"
  x[grep("Family",x)] <- "Family vehicle"
  x[grep("Other",x)] <- "Other"
  x[grep("School",x)] <- "School bus"
  x[grep("Transit",x)] <- "Transit"
  x[grep("Walk",x)] <- "Walk"
  return(x)
}


## modeDFwideFunction creates the modeDFwide table that 
## shows counts and percentages of mode by buffer

modeDFwideFunction <- function(df){
  modeDFWide <- dcast(melt(mSb_df, id.vars=c("Mode", "Buffer")),
                    Mode ~ Buffer,
                    subset = .(variable == "Estimate"))
  modeDFWide$Mode <- as.character(modeDFWide$Mode)
  numBuffers <- length(buffers)
  modeDFWide <- rbind(modeDFWide,c("Total",sapply(modeDFWide[,buffers],sum)))
  modeDFWide[,2:(numBuffers + 1)] <- lapply(modeDFWide[,2:(numBuffers + 1)],as.numeric)
  modeDFWidePct <- pctByColDF(modeDFWide[,2:(numBuffers+1)])
  modeDFWidePct <- pctFormat(modeDFWidePct)
  modeDFWide <- cbind(modeDFWide,modeDFWidePct)
  names(modeDFWide)[1] <- ""
  return(modeDFWide)
}

## compareSchTable
## Input: allSchComp data frame
## Output: data frame with only schools whose proportion
## of students within one mile walk zone is within .1 of 
## the proportion for study school
compareSchTable <- function(DF,maxRange){
  mileMaxPct <- oneMileSchoolRatio + .1
  mileMinPct <- oneMileSchoolRatio + -.1
  maxRange <- c(mileMinPct,mileMaxPct)
  compSchools <- DF[DF$PctMile<maxRange[2] &
                      DF$PctMile>maxRange[1],]
  return(compSchools)
}

compSchoolsData <- function(DF){
  PctMile <- sum(DF$Count1Mile)/sum(DF$Students)
  PctWalkMile <- sum(DF$WalkToCount1Mile)/sum(DF$Count1Mile)
  ghgPerCap = sum(DF$ghgPerCap*DF$Students)/sum(DF$Students)
  DF <- data.frame(PctMile = PctMile,
                   PctWalkMile = PctWalkMile,
                   ghgPerCap=ghgPerCap)
  return(DF)     
}


