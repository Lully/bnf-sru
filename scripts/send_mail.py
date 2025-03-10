# coding: utf-8

explain = """
Envoi d'un mail sur une boîte Gmail
Utile à activer pour envoyer une notification par mail si un script plante !
(en cas de message d'erreur)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(to_address, subject, content, login, password):
    try:
        # Création de l'objet message
        msg = MIMEMultipart()
        msg['From'] = login
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))
        
        # Connexion au serveur SMTP de Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Sécurise la connexion
        
        # Connexion avec les identifiants
        server.login(login, password)
        
        # Envoi du mail
        server.sendmail(login, to_address, msg.as_string())
        server.quit()
        
        print("Email envoyé avec succès !")
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")


if __name__ == "__main__":
    print(explain)
    recipient = input("Destinataire : ")
    login = input("Identifiant GMail : ")
    pwd = input("Mot de passe GMail : ")
    subject = input("Sujet du mail : ")
    content = input("Contenu du mail : ")
    send_email(recipient, subject, content, login, pwd)