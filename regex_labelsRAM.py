# coding utf-8

import pandas as pd
import re


def liste_subfields(field):
    liste_subfields = []
    for e in field.split("$"):
        if e:
            liste_subfields.append((e[0], e[1:].strip()))
    return liste_subfields

def marcfield2label(field):
    if field:
        repetitions = {"a": " -- ",
                    "x": " -- ",
                    "y": " -- ",
                    "l": " / ",
                    "d": " ; "}
        for char in repetitions:
            if re.search(f"\${char}([^$]+) \${char}", field) is not None:
                field = re.sub(f"\${char}([^$]+) \${char}", f"${char}\\1 {repetitions[char]}", field)
            if re.search(f"\${char}([^$]+) \${char}", field) is not None:
                field = re.sub(f"\${char}([^$]+) \${char}", f"${char}\\1 {repetitions[char]}", field)
        rules_multi = {"d k j": "(d-k-j)",
                       "f e": "f e"}  # date précise
        rules = {"a": "a",
                "b": ". b",
                "c": " c",
                "x": " -- x",
                "y": " -- y",
                "5": " -- 5",
                "i": " (i)",
                "k": "-k",
                "j": "-j",
                "d": " d",
                "h": " h",
                "t": " t",
                "l": " (l)",
                "m": ". m",
                "n": ". n",
                "z": " -- z",
                "f": " (f)",
                "v": " (v)"
        }
        for rule in rules_multi:
            chars = rules_multi[rule].split(" ")
            if len(chars) == 2:
                if re.search(f"\${chars[0]}([^$]+) \${chars[1]}([^$]+)", field) is not None:
                    field = re.sub(f"\${chars[0]}([^$]+) \${chars[1]}([^$]+)", r"(\1 ; \2)", field)
            if len(chars) == 3:
                if re.search(f"\${chars[0]}([^$]+) \${chars[1]}([^$]+) \${chars[2]}([^$]+)", field) is not None:
                    field = re.sub(f"\${chars[0]}([^$]+) \${chars[1]}([^$]+) \${chars[2]}([^$]+)( ?)", r"(\1-\2-\3)\4", field)
        field = liste_subfields(field)

        i = 0
        
        for subfield in field:
            try:
                rule = rules[subfield[0]]
            except KeyError:
                rule = f" -- {subfield[0]}"
            
            if ("(" in rule and "(" in subfield[1]) or (")" in rule and ")" in subfield[1]):
                rule = f" {subfield[0]}"
            # print(70, re.sub(f"\${char}([^$]+)", rule.replace(subfield[0], subfield[1]), subfield[1]))
            field[i] = rule.replace(subfield[0], subfield[1])
            
            i += 1
        field = "".join(field)
        field = field.replace("( ", "(").replace(" )", ")")
        field = field.replace(")(", ' ; ')
        field = field.replace(" ;; ", ' ; ').replace(" ; ; ", ' ; ')
        field = field.replace(";)", ')')
        field = field.replace("((", '(').replace("))", ")")
        while "  " in field:
            field = field.replace("  ", " ")
        if re.search("\$[\w]", field) is not None:
            field = re.sub("\$[\w]", " ¤¤ ", field)
    field = field.strip()
    
    return field

if __name__ == "__main__":
    fname = input("Nom du fichier tabulé à traiter : ")
    col = input("Colonne Excel contenant la chaîne d'indexation : ")
    df = pd.read_csv(fname, encoding="utf-8", delimiter="\t")
    df = df.fillna("")
    new_vals = []
    for i, row in df.iterrows():
        new_vals.append(marcfield2label(row[col]))
    df[col + " label"] = new_vals
    df.to_excel(fname.split(".")[0] + "-modifié.xlsx", index=None)
