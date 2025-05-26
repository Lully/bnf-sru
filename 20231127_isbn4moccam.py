from stdf import *
from csv import reader
import SRUextraction as sru

fnames = ["20231120_stockBFL-report30900.txt", "20231120_stockBFL-report20000.txt"]

arks = set()
isbn4moccam = set()

for fname in fnames:
    with open(fname, encoding="utf-8") as file:
        content = reader(file, delimiter="\t")
        next(content)
        for row in content:
            ark = row[0]
            if ark not in arks:
                arks.add(ark)
                source_ext = row[3]
                if "'sudoc': 'non'" in source_ext:
                    new_record = row[5].split("¤")
                    xml_record = sru.seq2xml_record(new_record, True, True, "xml")
                    isbn = sru.record2fieldvalue(xml_record, "020$a")
                    isbn4moccam.add(isbn)
report = create_file("20231127_isbn4moccam.txt")
for isbn in isbn4moccam:
    line2report([isbn], report)