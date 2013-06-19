## Convert NEAR_DIST to miles from meters
DF$NEAR_DIST <- DF$NEAR_DIST/1609.34

## Corresponds to Step 1 (page C6) from Kids Are Commuters Too
## Estimate travel distance to school based on walkshed
## For 0.0 < walkshed <= 0.5 miles, distance = 0.33
## For 0.5 < walkshed <= 1.0 miles, distance = 0.75
## For 1.0 < Walkshed < 1.5 miles, distance = 1.25
## For 1.5 < walkshed, distance = 1.25 + 1.25*(distance to 1.5 mile walkshed)
distEst <- ifelse(DF$BUFF_DIST == "0.0", 0.0,
									ifelse(DF$BUFF_DIST == "0.5", 0.33,
												 ifelse(DF$BUFF_DIST == "1.0", 0.75,
                                ifelse(DF$BUFF_DIST == "1.5", 1.25,
                                       ifelse(DF$BUFF_DIST == "2.0", 1.75,
                                              2 + DF$NEAR_DIST*1.25)))))

## Corresponds to Step 1 (page C7) from Kids Are Commuters Too
## Modify travel distance from Step 1 based on whether 
## student is dropped off on the way to another activity
## If PickUp = Yes and walkshed = 
## 0.5 miles, then distance to school = 0.26
## 1.0 miles, then distance to school = 0.595
## 1.5 miles, then distance to school = 0.99
## > 1.5 miles, then
##    - the expression 0.7928932*distEst is the expected value of the extra distance that is
##    - driven, which is given by 3*distEst - (2^.5)distEst)/2
## Otherwise, distance TO school is the estimated distance from Step 1

distEstTo <- ifelse(DF$BUFF_DIST == "0.5" & DF$DropOff == "yes", 0.26,
										ifelse(DF$BUFF_DIST == "1" & DF$DropOff == "yes", 0.595,
													 ifelse(DF$BUFF_DIST == "1.5" & DF$DropOff == "yes", 0.99,
													 			 ifelse(DF$BUFF_DIST == "1.5+" & DF$DropOff == "yes",0.7928932*distEst, 2*distEst))))


distEstFrom <- ifelse(DF$BUFF_DIST == "0.5" & DF$PickUp == "yes", 0.26,
										ifelse(DF$BUFF_DIST == "1" & DF$PickUp == "yes", 0.595,
													 ifelse(DF$BUFF_DIST == "1.5" & DF$PickUp == "yes", 0.99,
													 			 ifelse(DF$BUFF_DIST == "1.5+" & DF$PickUp == "yes",0.7928932*distEst, 2*distEst))))


## Corresponds to Step 2 (page C7) from Kids Are Commuters Too
## Calculate VMT TO and FROM school based on whether or not 
## student carpools. If student carpools, carpool size is assumed to be two,
## and vmtTo = 0.5*distEstTo and vmtFrom = 0.5*distEstFrom. If student does not
## carpool, vmtTo = distEstTo and vmtFrom = distEstFrom

vmtTo <- ifelse(DF$ModeTo == "Carpool", 0.5*distEstTo,
								ifelse(DF$ModeTo == "Family Vehicle", distEstTo, 0))

vmtFrom <- ifelse(DF$ModeFrom == "Carpool", 0.5*distEstFrom,
									ifelse(DF$ModeFrom == "Family Vehicle", distEstFrom, 0))

## Corresponds to Steps 4 and 5 (page C7) from Kids Are Commuters Too
## Calculate Gas Consumed from VMT estimates
## Fuel efficiency estimates from the EPA were used:
## 23.9 mpg for passenger cars and 17.4 for trucks
## These were then reduced to 21.0 and 17.0 to account for city MPG
## Per USDOT estimates, vehicle mix was assumed to be
## 63.4% passenger cars and 36.6% trucks
## So, gallons consumed = VMT/(21.0*0.634 + 17.0*0.366)
## This was then multiplied by 1.8 to account for cold starts 

gallonsTo <- 1.8*vmtTo/(21.0*0.634 + 17.0*0.366)
gallonsFrom <- 1.8*vmtFrom/(21.0*0.634 + 17.0*0.366)


## Corresponds to Step 6 (page C7) from Kids Are Commuters Too
## Calculate GHG emissions
## Per EPA estimates, GHG emissions (in kilograms) are 8.8 kg per gallon consumed
## So ghg (kg) = 8.8*gallons

CO2_To <- 8.8*gallonsTo
CO2_From <- 8.8*gallonsFrom

## Corresponds to Step 7 (page C7) from Kids Are Commuters Too
## Estimate other GHG emissions as (C02 emissions)/19

ghg_Other_To <- CO2_To/19
ghg_Other_From <- CO2_From/19

## Corresponds to Step 8 (page C7) from Kids Are Commuters Too
## Estimate cold start additivles

cold_start_To <- ifelse(CO2_To > 0.0, 0.035,CO2_To)
cold_start_From <- ifelse(CO2_From > 0.0, 0.035, CO2_From)

## Corresponds to Step 9 (page C7) from Kids Are Commuters Too
# Calculate Total GHG Emissions

ghg_Total_To <- CO2_To + ghg_Other_To + cold_start_To
ghg_Total_From <- CO2_From + ghg_Other_From + cold_start_From
ghg_Total = ghg_Total_To + ghg_Total_From

## Add GHG calculations to DF

DF <- as.data.frame(cbind(DF,distEst,ghg_Total_To,ghg_Total_From, ghg_Total))
