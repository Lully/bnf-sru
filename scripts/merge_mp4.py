# coding: utf-8

import subprocess
import os

def merge_mp4_files(input_files, output_file, compression_rate=None):
    """
    Fusionne plusieurs fichiers MP4 en un seul avec une option de compression.

    Args:
        input_files (list of str): Liste des chemins vers les fichiers MP4 à fusionner.
        output_file (str): Chemin du fichier de sortie fusionné.
        compression_rate (str, optional): Taux de compression (par exemple, '23' pour une compression standard). Plus la valeur est basse, meilleure est la qualité.

    Returns:
        bool: True si la fusion est réussie, False sinon.
    """
    # Vérification des fichiers d'entrée
    if not input_files or len(input_files) < 2:
        raise ValueError("Vous devez fournir au moins deux fichiers MP4 à fusionner.")

    # Vérification de l'existence des fichiers
    for file in input_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"Le fichier {file} est introuvable.")

    try:
        # Créer un fichier texte temporaire contenant la liste des fichiers à fusionner
        with open("file_list.txt", "w") as f:
            for file in input_files:
                f.write(f"file '{os.path.abspath(file)}'\n")

        # Commande FFmpeg pour fusionner les fichiers sans réencodage
        merge_command = [
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_file
        ]

        # Si un taux de compression est spécifié, ajouter les options de réencodage
        if compression_rate is not None:
            merge_command = [
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c:v", "libx264", "-crf", str(compression_rate), output_file
            ]

        # Exécution de la commande FFmpeg
        subprocess.run(merge_command, check=True)

        # Nettoyage du fichier temporaire
        os.remove("file_list.txt")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de FFmpeg : {e}")
        return False

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return False

if __name__ == "__main__":
    folder = input("Dossier où se trouvent les fichiers MP4 : ")
    files = os.listdir(folder)
    files = [os.path.join(folder, f) for f in files if f.endswith(".mp4")]
    output_file = input("Nom du fichier en sortie : ")
    output_file = os.path.join(folder, output_file)
    compression_rate = input("Taux de compression (23 = normal, en augmentant la compression on diminue la qualité) : ")
    if compression_rate == "":
        compression_rate = None
    merge_mp4_files(files, output_file, compression_rate)