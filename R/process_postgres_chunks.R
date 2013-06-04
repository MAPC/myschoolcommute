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
                      y = "Students")
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
                      y = "Students")
sByB4 <- sByB3 + scale_fill_manual("",
                                   values = c("#D9A09A","#C5C9C9"),
                                   labels = c("Surveyed", "Estimated"))
sByB5 <- sByB4 + theme_minimal()
sByB5

## @knitr b_dft
bufferDF_latex <- latex(b_dft,
                        file="",
                        headings = c("",buffers),
                        first.hline.double = FALSE,
                        rowname = NULL,
                        where="H",
                        col.just=c("l",rep("r",5)),
                        caption="Surveyed and Estimated Total Students by Walkshed")
                       
## @knitr mByBuffer
mByBuffer1 <- ggplot(data = mSb_df,
                            aes(x = Buffer,
                                y = Estimate,
                                fill = Mode))
mByBuffer2 <- mByBuffer1 + geom_bar(stat = "identity")
mByBuffer3 <- mByBuffer2 + labs(title = paste("Students by Walkshed and Morning Travel Mode\n",
                                    School_Name,sep=""),
                                y = "Estimated Number of Trips, Morning Commute")
mByBuffer4 <- mByBuffer3 + scale_fill_manual("",
                                             values = c("#D9A09A","#F2E8A5","#A3BAA7"),
                                             labels = c("Auto", "School Bus", "Walk"))
mByBuffer5 <- mByBuffer4 + theme_minimal()
mByBuffer5
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
modeByBufferTable <- latex(mSb_df_wide,
                           file="",
                           cgroup = c("",
                                      "Trips by Walkshed",
                                      "Percents"),
                           n.cgroup = c(1,5,5),
                           first.hline.double = FALSE,
                           rowname = NULL,
                           where="!htbp",
                           col.just=c("l",rep("r",10))
                           )
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
m1 <- ggplot(data = mt_df,
             aes(x = Mode,
                 y = Pct,
                 fill = reorder(Time,rep(1:2,times=nrow(mt_df)/2))))
m2 <- m1 + geom_bar(stat = "identity",
                    position = "dodge")
m3 <- m2 +
  scale_y_continuous(labels = percent) +
  scale_fill_manual(values = colors)
m4 <- m3 + labs(title = paste("Morning and Afternoon Mode Choices\n",
                              School_Name,sep=""),
                fill = "",
                x = "",
                y = "")
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
                                             "studentsEst",
                                             "ghgEst",
                                             "ghgEstPerCap",
                                             "PctTotGHGprint")],
                        file="",
                        colheads = c("Buffer",
                                     "Students",
                                     "Total GHG",
                                     "GHG Per Capita",
                                     "Percent Total GHG"),
                        where="H",
                        first.hline.double = FALSE,
                        caption = paste("GHG Emissions by Walkshed, ",
                            paste(School_Name,".",sep="")),
                        col.just=c("l",rep("r",4)),
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
                                      "Percent Within 1 Mile",
                                      "1.0 Mile Walk Share",
                                      "GHG Per Student"),
                         where="H",
                         first.hline.double = FALSE,
                         caption = paste("1.0 Mile walk share and GHG emissions: ",
                                         School_Name,
                                         " versus peer schools. Peer schools are those 
                                         whose share of students within 1.0 mile of 
                                         school is within 10\\% of the share at your 
                                         school.",
                                         sep=""),
                              col.just=c("l",rep("r",3)),
                              rowname = NULL)