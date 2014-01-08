## @knitr g_dfg
pByG1 <- ggplot(data = g_dfg,
                aes(x=Grade))
pByG2 <- pByG1 + geom_bar(aes(y = value,
                              fill = variable),
                          stat = "identity")
pByG3 <- pByG2 + geom_text(label = paste(g_dfg$Pct,
                                         "%",
                                         sep=""),
                           y=3)
pByG4 <- pByG3 + labs(title = paste("Participation by Grade\n",
                                    School_Name,sep=""),
                      y = "Number of Students")
pByG5 <- pByG4 + scale_fill_manual("",
                                   values = c("#D9A09A","#C5C9C9"),
                                   labels = c("Completed Survey", "No Response Received"))

pByG6 <- pByG5 + theme_minimal()
pByG6

## @knitr b_dfg
sByB1 <- ggplot(data = b_dfg,
                aes(x=Buffer))
sByB2 <- sByB1 + geom_bar(aes(y = value,
                              fill = variable),
                          stat = "identity")
sByB3 <- sByB2 + labs(title = paste("Students by Walkshed\n",
                                    School_Name,sep=""),
                      x = "Walkshed (miles)",
                      y = "Number of Students")
sByB4 <- sByB3 + scale_fill_manual("",
                                   values = c("#D9A09A","#C5C9C9"),
                                   labels = c("Surveyed", "Estimated"))
sByB5 <- sByB4 + theme_minimal()
sByB5

## @knitr b_dft
bufferDF_latex <- latex(b_dft[,2:ncol(b_dft)],
                        file="",
                        colheads = buffers,
                        table.env=FALSE,
                        # colheads = c("Students",buffers),
                        first.hline.double = FALSE,
                        rowname = c("Estimated","Surveyed", "Percent"), # NULL,
                        rowlabel = "Students",
                        where="H",
                        col.just=rep("r",5)) #c("l",rep("r",5))
                       
## @knitr mByBuffer
mSb_df$time <- factor(mSb_df$time,levels=levels(as.factor(mSb_df$time))[c(2:1)])
mByBuffer1 <- ggplot(data = mSb_df,
                     aes(x = Buffer,
                                y = Estimate,
                                fill = Mode))
mByBuffer2 <- mByBuffer1 + geom_bar(stat = "identity")
mByBuffer3 <- mByBuffer2 + facet_grid(. ~ time)
mByBuffer4 <- mByBuffer3 + labs(title = paste("Students by Walkshed and Travel Mode, Morning and Afternoon\n",
                                    School_Name,sep=""),
                                x = "Walkshed (miles)",
                                y = "Estimated Number of Trips")
mByBuffer5 <- mByBuffer4 + scale_fill_manual("",
                                             values = c("#D9A09A","#F2E8A5","#A3BAA7"),
                                             labels = c("Auto", "School Bus", "Walk/Bike"))

mByBuffer6 <- mByBuffer5 + theme_minimal()
mByBuffer6

##### Begin New Code ######
## @knitr mByBuffer_table
mByBuffer_table <-
  sub("^~~",
      "",
      capture.output(latex(mSb_df_for_latex,
                           file="",
                           colheads = buffers,
                           col.just=c(rep("r",length(buffers))),
                           rowlabel = "",
                           table.env=FALSE,
                           rowname = rep(c("Auto","School Bus","Walk"),2),
                           rgroup = c("Morning","Afternoon"),
                           n.rgroup = c(3,3),
                           first.hline.double = FALSE,
                           center="none",
                           where= "H"))
                         )

writeLines(mByBuffer_table)
##### End New Code ######

# 
# ## @knitr modeDFMorningWideTable
# modeDFMorningWideTable <-
#   latex(modeDFMorningWideLatex,
#         file="",
#         cgroup = c("","Counts","Percents"),
#         n.cgroup = c(1,5,5),
#         first.hline.double = FALSE,
#         rowname = NULL,
#         where="!htbp",col.just=c("l",rep("r",10)),
#         caption = paste("Counts and percentages of student travel mode by walkshed, ", 
#                                                 paste(School_Name,".",sep=""))
#         )
## @knitr modeByBufferTable
# modeByBufferTable <- latex(mSb_df_wide,
#                            file="",
#                            cgroup = c("",
#                                       "Trips by Walkshed",
#                                       "Percents"),
#                            n.cgroup = c(1,5,5),
#                            first.hline.double = FALSE,
#                            rowname = NULL,
#                            where="!htbp",
#                            col.just=c("l",rep("r",10))
#                            )
# @knitr modeByBufferTableMorning
modeByBufferTableMorning <- latex(mSb_df_wide_morning_pct,
                           file="",
                           colheads = c("Mode",buffers),
                           first.hline.double = FALSE,
                           rowname = NULL,
                           where="!htbp",
                           col.just=c("l",rep("r",5)),
                                  caption="Morning Mode by Walk/Bikeshed")

# @knitr modeByBufferTableAfternoon
modeByBufferTableAfternoon <- latex(mSb_df_wide_afternoon_pct,
                           file="",
                           colheads = c("Mode",buffers),
                           first.hline.double = FALSE,
                           rowname = NULL,
                           where="!htbp",
                           col.just=c("l",rep("r",5)),
                                    caption = "Afternoon Mode by Walk/Bikeshed")
# ## @knitr modeByBufferTableAllSchools
# modeByBufferTableAllSchools <- latex(aSmodeDFWide[,c(1,6:9)],
#                                      file="",
#                                      rowname = NULL,
#                                      first.hline.double = FALSE,
#                                      where="!htbp",
#                                      col.just=c("l",rep("r",8))
#                                      )
# 
# ## @knitr walkPotentialPlot
# g1 <- ggplot(data = WalkPotentialForPlot,
#              aes(x = MilePct,
#                  y = WalkPct),
#              xlim = c(minMilePct,1),
#              ylim = c(0,maxWalkPct))
# g2 <- g1 + 
#   geom_rect(aes(xmin = minMilePct,
#                 xmax = .70,
#                 ymin = 0,
#                 ymax = .30),
#             fill = "#D9A09A") +# red
#   geom_rect(aes(xmin = .70,
#                 xmax = 1,
#                 ymin = 0,
#                 ymax = .30),
#             fill = "#F2E8A5") + # yellow
#   geom_rect(aes(xmin = .70,
#                 xmax = 1,
#                 ymin = .30,
#                 ymax = maxWalkPct),
#             fill = "#A3BAA7")  # green
# g3 <- g2 + geom_point(colour="#787D7D", # grey
#                       size=c(rep(3,times=22),5),
#                       shape=c(rep(16,times=22),8))
# g4 <- g3 + geom_text(label=ifelse(WalkPotentialForPlot$Label == 1,
#                                   as.character(WalkPotentialForPlot$School),
#                                   ""),
#                      hjust = ifelse(MilePctSchool>meanMilePct,1,0),
#                      vjust = 1)
# g5 <-
#   g4 +
#   scale_x_continuous("Estimated Percent of Students Living within 1.0 Mile Walksed",
#                      labels = percent) +
#   scale_y_continuous("Estimated Walk Share",
#                      labels = percent) +
#   labs(title = paste("Student Proximity and Walk Share\n",School_Name,sep="")) +
#   theme_bw() + theme(plot.title = element_text(size = 12,
#                                                hjust = 0),
#                      panel.border = element_blank(),
#                      axis.line = element_line(color="grey50",
#                                               size = 0.1),
#                      panel.grid.major.x = element_blank(),
#                      panel.grid.major.y = element_line(size=.1),
#                      axis.ticks = element_line(color="grey50",
#                                                size=0.1),
#                      legend.position = "bottom",
#                      legend.direction = "horizontal")
# 
# g5
# 
## @knitr modeByTime

colors <- c("#D98A82","#C5C9C9")
mt_df$Time <- factor(mt_df$Time,levels=levels(mt_df$Time)[c(2:1)])
m1 <- ggplot(data = mt_df,
             aes(x = Mode,
                 y = Pct,
                 fill = Time))
m2 <- m1 + geom_bar(stat = "identity",
                    position = "dodge")
m3 <- m2 +
  scale_y_continuous(labels = percent) +
  scale_fill_manual(values = colors)
m4 <- m3 + labs(title = paste("Morning and Afternoon Mode Choices\n",
                              School_Name,sep=""),
                fill = "",
                x = "Mode Choice",
                y = "Percent of Trips")
m5 <- m4 + theme_minimal()
m5
# 
# ## @knitr chainByTime
# c1 <- ggplot(data = chainDF,
#              aes(x = time,
#                  y = est,
#                  fill = chain))
# c2 <- c1 + geom_bar(stat = "identity",
#                     position = "dodge") +
#   scale_fill_manual(values = colors)
# c3 <-   c2 + labs(title = paste("Morning and Afternoon Trip Chaining\n",School_Name,sep=""),
#                   fill = "",
#                   x = "",
#                   y = "Estimated Number of Trips") +
#   theme_bw() + theme(plot.title = element_text(size = 12,
#                                                hjust = 0),
#                      panel.border = element_blank(),
#                      axis.line = element_line(color="grey50",
#                                               size = 0.1),
#                      panel.grid.major.x = element_blank(),
#                      panel.grid.major.y = element_line(size=.1),
#                      axis.ticks = element_line(color="grey50",
#                                                size=0.1),
#                      legend.position = "bottom",
#                      legend.direction = "horizontal")
# c3
# 
# ## @knitr ChainByTimeAndAvail
# modeByBufferTable <- latex(availDFwidePctFormat,
#                            file="",
#                            cgroup = c("",
#                                       "Low Availability",
#                                       "High Availability"),
#                            n.cgroup = c(1,2,2),
#                            rowname = NULL,
#                            helvetica = TRUE,
#                            first.hline.double = FALSE,
#                            where="H",
#                            caption = paste("Dedicated and En Route Trips by Vehicle Availability and Time of Day,", paste(School_Name,".",sep="")),
#                            col.just=c("l",rep("r",4))
#                            )
# 
## @knitr ghgTableSchool
ghgTableSchool <- latex(ghgBufferDFgeneric[c("Buffer",
                                             "ghgEst",
                                             "ghgEstPerCap",
                                             "PctTotGHGprint")],
                        file="",
                        colheads = c("Buffer",
                                     "Total (kg)",
                                     "Per Student",
                                     "Percent"),
                        where="H",
                        first.hline.double = FALSE,
                        col.just=c("l",rep("r",3)),
                        rowname = NULL)
# 
# ## @knitr ghgTableSchoolAllSch
# ghgTableSchoolAllSch <- latex(ghgBufferAllSchDF[c("BUFF_DIST",
#                                                   "students",
#                                                   "ghg_Total",
#                                                   "ghgEstPerCap",
#                                                   "PctTotGHGprint")],
#                               file="",
#                               colheads = c("Buffer",
#                                            "Students",
#                                            "Total GHG",
#                                            "GHG Per Capita",
#                                            "Percent Total GHG"),
#                               where="H",
#                               first.hline.double = FALSE,
#                               caption = paste("GHG Emissions by Walkshed, ",
#                                               "results from 22 previously surveyed schools.",
#                                               sep=""),
#                               col.just=c("l",rep("r",4)),
#                               rowname = NULL)
# 
## @knitr pSaggLatex
pSaggLatexTable <- latex(pSaggLatex,
                         file="",
                         colheads = c("",
                                      "1 Mile",
                                      "Walk",
                                      "GHG"),
                         where="H",
                         first.hline.double = FALSE,
                         caption = "1.0 Mile walk share and GHG emissions. Peer schools are those 
                                         whose share of students within 1.0 mile of 
                                         school is within 25\\% of the share at your 
                                         school. 1 Mile is the percent of students who
                                         live within one mile of school. Walk is the percent
                                         of students within one mile who walk. GHG
                                         is per-student GHG emissions in kg.",
                              col.just=c("l",rep("r",3)),
                              rowname = NULL)

## @knitr walkExpectedActual
dfLatex = prettyTable(bufferByModeDFLatex,
                      pcts = 1:ncol(bufferByModeDFLatex),
                      digits = 0)
lc=ncol(dfLatex)
bufferByModeDFLatexTable <-
  latex(dfLatex,
        file = "",
        title = "",
        booktabs=TRUE,
        table.env=FALSE,
        col.just= rep("r",lc),
        rowlabel = "",
        colheads = buffers,
        colnamesTexCmd = "bfseries")



