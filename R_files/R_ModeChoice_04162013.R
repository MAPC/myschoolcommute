library(plyr)
library(reshape2)
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

modeDF <- mergeDF(modeDF,
                  t2,
                  data.column1 = "Freq",
                  data.column2 = "freq",
                  by.x = c("Mode","Buffer"),
                  by.y = c("ModeFromMod","BUFF_DIST"))

modeDF$Est <- round(modeDF$Freq*Enroll_Total/sum(modeDF$Freq),digits=0)

modeDFWide <- dcast(melt(modeDF, id.vars=c("Mode", "Buffer")),
                    Mode ~ Buffer,
                    subset = .(variable == "Est"))
modeDFWide$Mode <- as.character(modeDFWide$Mode)
modeDFWide <- rbind(modeDFWide,
                    c("Total",sapply(modeDFWide[,2:5],sum)))
modeDFWide[,2:5] <- lapply(modeDFWide[,2:5],as.numeric)
modeDFWidePct <- pctByColDF(modeDFWide[,2:5])
modeDFWidePct <- pctFormat(modeDFWidePct)

modeDFWide <- cbind(modeDFWide,modeDFWidePct)
names(modeDFWide)[1] <- ""

print(latex(modeDFWide,
            file="",
            cgroup = c("",
                       "Counts",
                       "Percents"),
            n.cgroup = c(1,4,4),
            rowname = NULL,
            where="!htbp",
            caption = paste("Counts and percentages of student travel mode by walkshed,", paste(School_Name,".",sep="")),
            col.just=rep("r",9)
            )
      )

 




            


