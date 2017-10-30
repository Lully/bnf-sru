"""Fichier d'installation du script setup_frbnf2ark.py."""
#Commande Windows à utiliser : python setup_frbnf2ark.py build

from cx_Freeze import setup, Executable
import os


path_anaconda = "D:\\BNF0017855\\Programmes\\Anaconda"
if (path_anaconda[-1] != "\\"):
    path_anaconda = path_anaconda + "\\"

os.environ['TCL_LIBRARY'] = path_anaconda + "tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = path_anaconda + "tcl\\tk8.6"
# On appelle la fonction setup

includes  = []
include_files = [path_anaconda + "DLLs\\tcl86t.dll",
                 path_anaconda + "DLLs\\tk86t.dll"]
base = None

build_exe_options = {"packages": ["files", "tools"], "include_files": ["tcl86t.dll", "tk86t.dll"]}  
setup(

    name = "ExtractionCatalogueBnF",

    version = "0.1",

    description = "Récupération des ARK à partir de numéros FRBNF",
    options = {"build_exe": {"includes": includes,"include_files":include_files}},
    executables = [Executable("frbnf2ark.py", base=base)],

)

#Ajout d'un raccourci pointant vers le fichier *.exe
raccourci = open("build/frbnf2ark.bat","w")
raccourci.write("start exe/frbnf2ark.exe")
