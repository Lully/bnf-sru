library(RCurl)
library(XML)
firstpage <- xmlParse(getURLContent("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.anywhere%20adj%20%22la%20fabrique%22&recordSchema=unimarcxchange&maximumRecords=10&startRecord=1"))
nb_of_results = strtoi(xpathSApply(firstpage, "//srw:numberOfRecords", xmlValue))
xmlToDataFrame(nodes = getNodeSet(firstpage, "//mxc:record"))

