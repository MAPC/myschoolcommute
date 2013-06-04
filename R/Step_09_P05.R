############### Begin GHG Section ###################
source("calculate_GHG.R")

ghgBufferDFgeneric <- data.frame(Buffer = buffers,
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

ghgBufferDFgeneric$studentsEst <- round(enrollTotal*ghgBufferDFgeneric$Students/(sum(ghgBufferDFgeneric$Students)),0)
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

## Peer School Comparison Section

## calculate range within one mile for peer schools
## pSdF == %peer %School %data %Frame
oneMileSchoolRatio <- pctWithinOneMile/100
walkSchoolOneMile <- sum(mSb_df$Estimate[mSb_df$Buffer %in% c("0.5","1.0") & mSb_df$Mode == "Walk"])
walkSchoolOneMileRatio <- walkSchoolOneMile/estWithinOneMile
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