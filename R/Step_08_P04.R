## converts mSb_df into mSb_df_wide to pass to latex function
mSb_df_wide_morning <- modeDFwideFunction(mSb_df[mSb_df$time=="Morning",c("Mode","Buffer","Estimate")])
mSb_df_wide_morning[,2:6] <- round(mSb_df_wide_morning[,2:6],0)
mSb_df_wide_morning[,2:6] <- lapply(mSb_df_wide_morning[,2:6],as.character)
mSb_df_wide_morning_pct <- mSb_df_wide_morning[,c(1,7:11)]

mSb_df_wide_afternoon <- modeDFwideFunction(mSb_df[mSb_df$time=="Afternoon",c("Mode","Buffer","Estimate")])
mSb_df_wide_afternoon[,2:6] <- round(mSb_df_wide_afternoon[,2:6],0)
mSb_df_wide_afternoon[,2:6] <- lapply(mSb_df_wide_afternoon[,2:6],as.character)
mSb_df_wide_afternoon_pct <- mSb_df_wide_afternoon[,c(1,7:11)]