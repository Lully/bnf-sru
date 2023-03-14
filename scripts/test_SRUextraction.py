# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 10:11:59 2018

@author: Lully
"""

import recordid2metas as r

srubnf_url = "http://catalogue.bnf.fr/api/SRU?"


def test_class_sru():
    var1 = r.SRU_result(srubnf_url,{"query":'bib.ark any "ark:/12148/cb12345678x"',"recordSchema":"unimarcxchange"})
    assert var1.url == "http://catalogue.bnf.fr/api/SRU?query=bib.ark%20any%20%22ark%3A/12148/cb12345678x%22&recordSchema=unimarcxchange&version=1.2&operation=searchRetrieve&maximumRecords=1000&startRecord=1"