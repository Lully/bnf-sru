:: 1.Lance la compilation du code source
:: 2. Nettoie le répertoire build, renomme dist en "ExtractionCatalogueBnF" et y place le raccourci pour le lancement du fichier
:: 3. Compresse le répertoire obtenu
:: 4. Supprime le répertoire initial "ExtractionCatalogueBnF" 
@echo off
set /p version="version: "
pyinstaller ExtractionCatalogueBnF.py --exclude-module pandas, scipy, notebook, matplotlib, botocore, numpy
rd /s /q build
copy ExtractionCatalogueBnF.bat dist
rename dist ExtractionCatalogueBnF
rename ExtractionCatalogueBnF\ExtractionCatalogueBnF exe
"C:\Program Files\7-Zip\7z" a -tzip bin\ExtractionCatalogueBnF_%version%_win64_py3.6.zip ExtractionCatalogueBnF/
rd /s /q ExtractionCatalogueBnF