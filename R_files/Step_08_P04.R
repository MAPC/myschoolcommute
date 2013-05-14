## converts mSb_df into mSb_df_wide to pass to latex function
mSb_df_wide <- modeDFwideFunction(mSb_df)
mSb_df_wide[,2:6] <- round(mSb_df_wide[,2:6],0)
mSb_df_wide[,2:6] <- lapply(mSb_df_wide[,2:6],as.character)