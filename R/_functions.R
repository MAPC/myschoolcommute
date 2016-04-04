## convert date1 and date2 into date strings
get_dates = function(date1, date2) {
  # assumes date1 and date2 are date strings in the format YYYY-MM-DD
  start_date = as.Date(date1)
  start_month <- format(start_date, format = "%B")
  start_year <- format(start_date, format = "%Y")
  end_date = as.Date(date2)
  end_month <- format(end_date, format = "%B")
  end_year <- format(end_date, format = "%Y")
  return(list(start_date=start_date,
              start_month=start_month,
              start_year=start_year,
              end_date=end_date,
              end_month=end_month,
              end_year=end_year))
}

## get enrollment data from start date
get_enrollment_df = function(start_date) {
  if (start_date < as.Date("2011-07-30")) {
    df = enrollment10_11
  }
  else if (start_date < as.Date("2012-07-30")) {
    df = enrollment11_12
  }
  else if (start_date < as.Date("2013-07-30")) {
    df = enrollment12_13
  }
  else if (start_date < as.Date("2014-07-30")) {
    df = enrollment13_14
  }
  else if (start_date < as.Date("2015-07-30")) {
    df = enrollment14_15
  }
  else if (start_date < as.Date("2016-07-30")) {
    df = enrollment15_16
  }
  else {
    df = enrollment15_16
  }
  return(df)
}

## get enrollment date from start date
get_enrollment_date = function(start_date) {
  if (start_date < as.Date("2011-07-30")) {
    df = "2010-2010"
  }
  else if (start_date < as.Date("2012-07-30")) {
    df = "2011-2012"
  }
  else if (start_date < as.Date("2013-07-30")) {
    df = "2012-2013"
  }
  else if (start_date < as.Date("2014-07-30")) {
    df = "2013-2014"
  }
  else if (start_date < as.Date("2015-07-30")) {
    df = "2014-2015"
  }
  else if (start_date < as.Date("2016-07-30")) {
    df = "2015-2016"
  }
  else {
    df = "2015-2016"
  }
  return(df)
}

## left-pad ORG.CODE column to be 8 characters
left_pad = function(str, len = 8) {
  length_diff = len - nchar(str)
  zeros = paste(rep("0", length_diff), collapse = "")
  return(paste(zeros, str, sep = ""))
}

pad_org_code = function(org_column) {
  sapply(org_column, left_pad)
}
