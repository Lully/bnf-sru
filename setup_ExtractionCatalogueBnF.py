"""Fichier d'installation du script ExtractionCatalogueBnF_code.py."""
#Commande Windows à utiliser : C:\python\Anaconda\python.exe setup.py build

from cx_Freeze import setup, Executable
import os

os.environ['TCL_LIBRARY'] = "C:\\python\\Anaconda\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\python\\Anaconda\\tcl\\tk8.6"
# On appelle la fonction setup

includes  = []
include_files = ["C:\\python\\Anaconda\\DLLs\\tcl86t.dll",
                 "C:\\python\\Anaconda\\DLLs\\tk86t.dll"]
base = None

build_exe_options = {"packages": ["files", "tools"], "include_files": ["tcl86t.dll", "tk86t.dll"]}  
setup(

    name = "ExtractionCatalogueBnF",

    version = "0.1",

    description = "Extraction des données du catalogue de la BnF",
    options = {"build_exe": {"includes": includes,"include_files":include_files}},
    executables = [Executable("ExtractionCatalogueBnF.py", base=base)],

)