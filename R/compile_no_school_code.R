
knit2pdf("compile_no_school_code.Rnw")
file.rename("minimal.pdf",paste("Reports/",paste(ORG_CODE,".pdf",sep=""),sep=""))