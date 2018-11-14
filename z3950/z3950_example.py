# coding: utf-8
"""
Simple script to search a Z39.50 target using Python
and PyZ3950. 
"""

from PyZ3950 import zoom


ISBNs = ['978-1-905017-60-7', '2-86377-125-6']

conn = zoom.Connection ('z3950.bnf.fr', 2211)
conn.databaseName = 'TOUT'
conn.preferredRecordSyntax = 'UNIMARC'

for isbn in ISBNs:
    query = zoom.Query('CQL', 'find @attr 1=7 ' + isbn)
    print(query)
    res = conn.search(query)
    for r in res:
        print (str(r))

conn.close ()