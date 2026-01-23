import pdfplumber
import pandas as pd
import re

def generer_index_pdf(pdf_file, index_file):
    """
    Génère un index de mots à partir d'un fichier PDF et d'un fichier d'index.

    Args:
        pdf_file (str): Le chemin vers le fichier PDF.
        index_file (str): Le chemin vers le fichier tabulé contenant les mots à rechercher
                         et leur normalisation.  Le fichier doit avoir deux colonnes :
                         mot_a_chercher, mot_normalise.

    Returns:
        dict: Un dictionnaire où les clés sont les mots normalisés et les valeurs
              sont des listes dédoublonnées de numéros de page où le mot apparaît.
              Retourne un dictionnaire vide en cas d'erreur de lecture des fichiers.
    """

    try:
        # Lecture du fichier d'index
        index_df = pd.read_csv(index_file, sep='\t', header=None, names=['mot_a_chercher', 'mot_normalise'])
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
            for mot_a_chercher, mot_normalise in zip(index_df['mot_a_chercher'], index_df['mot_normalise']):
                index[mot_normalise] = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        # Recherche insensible à la casse et sur plusieurs lignes
                        pattern = r'\b' + re.escape(mot_a_chercher) + r'\b'
                        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if matches:
                            index[mot_normalise].append(page_num)
                # Suppression des doublons et tri des numéros de page
                index[mot_normalise] = sorted(list(set(index[mot_normalise])))

            return index

    except FileNotFoundError:
        print(f"Erreur : Fichier PDF introuvable : {pdf_file}")
        return {}
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier PDF : {e}")
        return {}


if __name__ == '__main__':
    # Exemple d'utilisation
    # Créeons des fichiers tests pour l'exemple
    pdf_file = input("Nom du fichier PDF à indexer : ")
    index_file = input("Nom de la liste des mots (2 colonnes, tabulé) : ")

    index_resultat = generer_index_pdf(pdf_file, index_file)

    if index_resultat:
        print("\nIndex généré :")
        for mot, pages in index_resultat.items():
            print(f"{mot} : {', '.join([str(el) for el in pages])}")
    else:
        print("La génération de l'index a échoué.")