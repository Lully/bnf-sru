# coding: utf-8

import os
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_pdf_from_images(image_folder, output_pdf):
    # Dimensions de la page A4 en points (1 point = 1/72 pouces)
    a4_width, a4_height = A4
    margin = 2 * 72  # 2 cm en points (1 pouce = 2.54 cm donc 2 cm = 2/2.54 pouces)

    # Obtenir la liste des fichiers d'image dans le dossier
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith('.jpg')]
    image_files.sort()  # Trier les fichiers pour les avoir dans l'ordre alphabétique

    # Créer un objet canvas pour le PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)

    for i, image_file in enumerate(image_files):
        image_path = os.path.join(image_folder, image_file)
        image = Image.open(image_path)

        # Redimensionner l'image si nécessaire pour qu'elle tienne dans la page avec les marges
        image_width, image_height = image.size
        max_width = a4_width - 2 * margin
        max_height = a4_height - 2 * margin

        if image_width > max_width or image_height > max_height:
            ratio = min(max_width / image_width, max_height / image_height)
            ratio = ratio * 1.2
            image_width = int(image_width * ratio)
            image_height = int(image_height * ratio)
            image = image.resize((image_width, image_height), Image.ANTIALIAS)

        # Calculer les positions pour centrer l'image
        x = (a4_width - image_width) / 2
        y = (a4_height - image_height) / 2

        # Ajouter l'image à la page
        c.drawImage(image_path, x, y, width=image_width, height=image_height)

        # Ajouter le numéro de page en haut à droite
        page_number = f"Page {i + 1}"
        c.setFont("Helvetica", 10)
        c.drawString(a4_width - margin, a4_height - 10, page_number)

        c.showPage()  # Terminer la page et passer à la suivante

    c.save()  # Sauvegarder le PDF

# Utilisation de la fonction
image_folder = r'D:\Documents\perso\Etienne\DUEC\compressed'
output_pdf = r'D:\Documents\perso\Etienne\DUEC\DUEC_selection.pdf'
create_pdf_from_images(image_folder, output_pdf)
