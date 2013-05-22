## Generate the data frame (df) that will be 
## used to genertae all subsequent data frames
## data frame naming convention:
## <first letters of variables cross_tabbed in df>_df
## b = BUFF_DIST mT = ModeTo mF = ModeFrom
## mTM = ModeToMod mFM = ModeFromMod
gbmTmFmTMmFM_df <- count(DF,
                  .(grade,
                    BUFF_DIST,
                    ModeTo,
                    ModeFrom,
                    ModeToMod,
                    ModeFromMod))