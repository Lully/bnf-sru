"""Fichier d'installation du script ExtractionCatalogueBnF_code.py."""
#Commande Windows à utiliser : C:\ProgramData\Anaconda3\python.exe setup_ExtractionCatalogueBnF.py build

from cx_Freeze import setup, Executable
import os


path_anaconda = "C:\\ProgramData\\Anaconda3\\"
if (path_anaconda[-1] != "\\"):
    path_anaconda = path_anaconda + "\\"

os.environ['TCL_LIBRARY'] = path_anaconda + "tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = path_anaconda + "tcl\\tk8.6"
# On appelle la fonction setup

includes  = ["lxml._elementpath"]
include_files = [path_anaconda + "DLLs\\tcl86t.dll",
                 path_anaconda + "DLLs\\tk86t.dll"]
base = None

build_exe_options = {"packages": ["files", "tools"], "include_files": ["tcl86t.dll", "tk86t.dll"]}  
setup(

    name = "ExtractionCatalogueBnF",

    version = "0.1",

    description = "Extraction des données du catalogue de la BnF",
    options = {"build_exe": {"includes": includes,"include_files":include_files}},
    executables = [Executable("ExtractionCatalogueBnF.py", base=base)],

)

#Ajout d'un raccourci pointant vers le fichier *.exe
raccourci = open("build/ExtractionCatalogueBnF.bat","w")
raccourci.write("start exe/ExtractionCatalogueBnf.exe")
