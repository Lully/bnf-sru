import pdfplumber
import pandas as pd
import re

from tqdm import tqdm
 
def generer_index_pdf(pdf_file, index_file):
    """
    Génère un index de mots à partir d'un fichier PDF et d'un fichier d'index.
    Gère les pages à deux colonnes et affiche les numéros de pages sous forme d'intervalles.
    """
 
    try:
        # Lecture du fichier d'index
        index_df = pd.read_csv(index_file, encoding="utf-8", sep='\t', header=None, names=['mot_a_chercher', 'mot_normalise'],
        dtype="str")
    except FileNotFoundError:
        print(f"Erreur : Fichier d'index introuvable : {index_file}")
        return {}
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier d'index : {e}")
        return {}
 
    try:
        # Lecture du fichier PDF
        with pdfplumber.open(pdf_file) as pdf:
            index = {}
            for mot_a_chercher, mot_normalise in tqdm(zip(index_df['mot_a_chercher'], index_df['mot_normalise'])):
                index[mot_normalise] = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extraction du texte par colonne
                    columns = page.extract_text_lines()
                    text_columns = []
                    if columns:
                        # On suppose que les colonnes sont séparées par une coordonnée x médiane
                        # On extrait le texte brut par colonne
                        left_column = []
                        right_column = []
                        for line in columns:
                            x0, top, x1, bottom, text = line['x0'], line['top'], line['x1'], line['bottom'], line['text']
                            if x0 < page.width / 2:  # Colonne de gauche
                                left_column.append(text)
                            else:  # Colonne de droite
                                right_column.append(text)
                        text_columns.append(" ".join(left_column))
                        text_columns.append(" ".join(right_column))
 
                    # Recherche dans chaque colonne
                    for column_text in text_columns:
                        if column_text:
                            # Recherche insensible à la casse et sur plusieurs lignes
                            pattern = r'\b' + re.escape(mot_a_chercher) + r'\b'
                            matches = re.findall(pattern, column_text, re.IGNORECASE | re.MULTILINE)
                            if matches:
                                index[mot_normalise].append(page_num)
                                break  # Évite les doublons si le mot apparaît plusieurs fois dans la page
 
                # Suppression des doublons et tri des numéros de page
                index[mot_normalise] = sorted(list(set(index[mot_normalise])))
 
    except FileNotFoundError:
        print(f"Erreur : Fichier PDF introuvable : {pdf_file}")
        return {}
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier PDF : {e}")
        return {}
 
    # Regroupement des numéros de pages en intervalles
    for mot in index:
        pages = index[mot]
        if pages:
            intervals = []
            start = pages[0]
            prev = start
            for page in pages[1:]:
                if page == prev + 1:
                    prev = page
                else:
                    if start == prev:
                        intervals.append(f"{start}")
                    else:
                        intervals.append(f"{start}-{prev}")
                    start = page
                    prev = page
            # Ajouter le dernier intervalle
            if start == prev:
                intervals.append(f"{start}")
            else:
                intervals.append(f"{start}-{prev}")
            index[mot] = intervals
 
    return index
	
if __name__ == '__main__':
    # Exemple d'utilisation
    pdf_file = input("Nom du fichier PDF à indexer : ")
    index_file = input("Nom de la liste des mots (2 colonnes, tabulé) : ")
 
    index_resultat = generer_index_pdf(pdf_file, index_file)
    
    index_report_name = pdf_file.replace(".pdf", "-index.pdf")

    if index_resultat:
        print("\nIndex généré :")
        with open(index_report_name, "w", encoding="utf-8") as report:
            for mot, intervals in index_resultat.items():
                report.write(f"{mot} : {', '.join(intervals)}")
                report.write("\n")
                print(f"{mot} : {', '.join(intervals)}")
    else:
        print("La génération de l'index a échoué.")