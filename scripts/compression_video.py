import subprocess
import os

def compresser_video(fichier_entree, fichier_sortie, type_video, taux_compression):
    """
    Compresse une vidéo selon un taux donné.

    Paramètres :
        fichier_entree (str) : chemin du fichier vidéo d'entrée
        fichier_sortie (str) : nom du fichier de sortie (sans extension)
        type_video (str) : format souhaité (ex. 'mp4', 'mkv', 'avi')
        taux_compression (float) : valeur entre 0 et 1 (1 = qualité maximale, 0 = compression maximale)
    """
    if not (0 < taux_compression <= 1):
        raise ValueError("Le taux de compression doit être compris entre 0 (exclu) et 1 (inclus).")

    if not os.path.isfile(fichier_entree):
        raise FileNotFoundError(f"Le fichier '{fichier_entree}' n'existe pas.")

    # On inverse le taux pour correspondre à une échelle de qualité (CRF)
    # FFmpeg utilise le CRF : 0 = qualité parfaite, 51 = très basse qualité
    # On mappe donc le taux de compression à cette échelle :
    crf = int(51 - taux_compression * 51)

    # Génération du nom de fichier de sortie
    fichier_sortie_complet = f"{os.path.splitext(fichier_sortie)[0]}.{type_video}"

    # Commande FFmpeg
    commande = [
        "ffmpeg",
        "-i", fichier_entree,
        "-vcodec", "libx264",
        "-crf", str(crf),
        "-preset", "medium",
        "-acodec", "aac",
        "-b:a", "128k",
        fichier_sortie_complet,
        "-y"  # pour écraser le fichier si déjà existant
    ]

    print(f"Compression en cours... (CRF = {crf})")
    try:
        subprocess.run(commande, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Fichier compressé créé : {fichier_sortie_complet}")
    except subprocess.CalledProcessError as e:
        print("❌ Erreur lors de la compression :")
        print(e.stderr.decode())

    return fichier_sortie_complet

if __name__ == "__main__":
    fname = input("Nom du fichier en entrée : ")
    output_fname = input("Nom du fichier en sortie : ")
    type_video = input("Format de la vidéo : ")
    taux_compression = float(input("Ratio de compression (nombre entre 0 et 1) : "))
    compresser_video(fname, output_fname, type_video, taux_compression)