# coding: utf-8
"""
Tesst sockets et recv
"""
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("www.bnf.fr", 80))
print(s)

print("Le nom du fichier que vous voulez récupérer:")
file_name = input(">> ") # utilisez raw_input() pour les anciennes versions python
s.send(file_name.encode())
print(s)
file_name = 'data/%s' % (file_name,)
r = s.recv(256)
print(r)
with open(file_name,'wb') as _file:
    _file.write(r)
print("Le fichier a été correctement copié dans : %s." % file_name)