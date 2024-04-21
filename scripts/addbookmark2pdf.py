# coding: utf-8

explain = """Ajout d'une liste de signets (bookmarks) à un fichier PDF"""

from PyPDF2 import PdfReader, PdfWriter

from stdf import *


def addbookmarks(pdfname, dict_bookmarks):
    # dict_bookmarks : dictionnaire avec numéro de page: nom du signet
    pdf_name_output = pdfname.replace(".pdf", "_signets.pdf")
    writer = PdfWriter()
    reader = PdfReader(pdfname)
    print(len(reader.pages))
    for page_number in range(len(reader.pages)):
        writer.add_page(reader.pages[page_number])
        if page_number+1 in dict_bookmarks:
            writer.add_outline_item(dict_bookmarks[page_number+1], page_number+1)
    outputStream = open(pdf_name_output, "wb")
    writer.write(outputStream)
    outputStream.close()
    



if __name__ == "__main__":
    fname = input("Nom du fichier en entrée : ")
    bookmarks_name = input("Fichier contenant les signets (2 colonnes : n° page - nom du signet) : ")
    bookmarks = file2list(bookmarks_name, all_cols=True)
    dict_bookmarks = {int(el[0]): el[1] for el in bookmarks}
    addbookmarks(fname, dict_bookmarks)