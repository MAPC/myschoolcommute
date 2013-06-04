## process_allSch.R reads in survey data
## and recodes the ModeTo and ModeFrom columns
## and saves results to ModeToMod and ModeFromMod


allSch <- read.csv("All_Surveys_w_GHG_5072_records_FINAL.csv",
                   header=T)

allSch$BUFF_DIST <- with(allSch,
                         ifelse(BUFF_DIST == 0 |
                                  BUFF_DIST == 0.5, "0.5",
                                ifelse(BUFF_DIST == 1, "1.0",
                                       ifelse(BUFF_DIST == 1.5 &
                                                NEAR_DIST == 0,"1.5",
                                              "1.5+"))))

## Add modified mode variables to allSch. These will be used when making some of the plots
allSch$ModeToMod <- with(allSch,
                         ifelse(ModeTo=="Carpool (with children from other families)" |
                                  ModeTo=="Family Vehicle (only children in your family)",
                                "Auto",
                                ifelse(ModeTo=="Walk" |
                                         ModeTo=="Other (skateboard, scooter, inline skates, etc.)" |
                                         ModeTo=="Bike", "Walk",
                                       ifelse(ModeTo=="School Bus" |
                                                ModeTo=="Transit (city bus, subway, etc.)" |
                                                ModeTo=="School Bus","School Bus",
                                              ifelse(ModeTo == "" |
                                                       ModeTo == "Missing",
                                                     "Missing",
                                                     ModeTo)))))

allSch$ModeFromMod <- with(allSch,
                           ifelse(ModeFrom=="Carpool (with children from other families)" |
                                    ModeFrom=="Family Vehicle (only children in your family)",
                                  "Auto",
                                  ifelse(ModeFrom=="Walk" |
                                           ModeFrom=="Other (skateboard, scooter, inline skates, etc.)" |
                                           ModeFrom=="Bike", "Walk",
                                         ifelse(ModeFrom=="School Bus" |
                                                  ModeFrom=="Transit (city bus, subway, etc.)" |
                                                  ModeFrom=="School Bus","School Bus",
                                                ifelse(ModeFrom == "" |
                                                         ModeFrom == "Missing",
                                                       "Missing",
                                                       ModeFrom)))))

allSch <- allSch[allSch$ModeToMod!="Missing" & allSch$ModeFromMod!="Missing",]