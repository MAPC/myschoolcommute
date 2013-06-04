# b_dft is b_df with buffers as column headings
# b_dft will be passed to latex function
# Columns:
# Buffer levels: 0.5, 1.0, 1.5, 2.0, 2.0+
# Rows: 
# Surveyed Students
# Estimates Total
# Percent of Students: Estiamtes sudents per buffer as percent of Total Estimates

# 1:
# Calculate
# Column
# Pct = Buffer Estimate as percent of Total Students
b_df$Pct <- round(100*b_df$Estimate/(sum(b_df$Estimate)))

# 2:
# create b_dft as transpose of b_df
b_dft <- as.data.frame(t(b_df[c("Estimate","Count","Pct")]))


# 3:
# convert columns to characters
# apply addPct to bottom row
b_dft[1,] <- round(b_dft[1,],0)
b_dft[nrow(b_dft),] <- addPct(b_dft[nrow(b_dft),])
b_dft <- as.data.frame(lapply(b_dft,as.character))
b_dft <- cbind(c("Estimated Total","Surveyed Students","Percent of Students"),b_dft)
names(b_dft) <- c("",levels(b_df$Buffer))



