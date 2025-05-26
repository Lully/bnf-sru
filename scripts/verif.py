import sru
import re

def controle_lien_auteur(string):
    string = str(string)
    res = "OK"
    test_ark = "https://catalogue\.bnf\.fr/ark:/12148/cb1\d\d\d\d\d\d\d[a-z0-9]"
    test_nna  = "1\d\d\d\d\d\d\d"
    
    search_ark = re.fullmatch(test_ark, string)
    search_nna = re.fullmatch(test_nna, string)
 
    if (search_ark is None and search_nna is None) :
        res = "l'ark ou le nna proposé n'a pas la bonne forme"
        
    elif search_ark is not None:
        
        ark = string[25:]
        record_aut = sru.SRU_result(f"aut.persistentid any {ark}", parametres = {"recordSchema":"intermarcxchange"}).firstRecord
        if record_aut is None:
            record_aut = sru.SRU_result(f" aut.status all 'sparse' and aut.persistentid any {ark}", parametres = {"recordSchema":"intermarcxchange"}).firstRecord
            
            if record_aut is not None :
                res = "l'ark renvoie vers une notice d'autorité élémentaire"
            else :
                res = "l'ark n'existe pas dans le catalogue général ou ne renvoie pas à une autorité"
        else :
            
            type_aut = sru.record2fieldvalue(record_aut, "000")[9]           
            if type_aut not in ("c", "p"):
                res = "KO - l'ark renvoie vers une notice qui n'est pas un agent"
            
    elif search_nna is not None:
        record_aut =  sru.SRU_result(f"aut.recordid any {string}", parametres = {"recordSchema":"intermarcxchange"}).firstRecord
        
        if record_aut is None:
            print(string)
            record_aut = sru.SRU_result(f"aut.status any sparse and aut.recordid any {string}", parametres = {"recordSchema":"intermarcxchange"}).firstRecord
            test = sru.SRU_result(f"aut.status any sparse and aut.recordid any {string}", parametres = {"recordSchema":"intermarcxchange"}).url
            print(test)
            if record_aut is not None :
                res = "KO - Le NNA renvoie vers une notice d'autorité élémentaire"
            else :
                res = "KO - le NNA n'existe pas dans le catalogue général"
        else :
            type_aut = sru.record2fieldvalue(record_aut, "000")[9]
            
            if type_aut not in ("c", "p"):
                
                res = "KO - le NNA renvoie vers une notice qui n'est pas un agent"
            #else : vérifier que ça correspond au type indiqué dans le tableau (pas d'incohérence personne/collectivité)

      
    return res

if __name__ == "__main__":
    nna = input("NNA : ")
    result = controle_lien_auteur(nna)
    print(result)