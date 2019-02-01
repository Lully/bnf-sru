# Projet de mapping data.bnf.fr - intermarc à partir des données elles-mêmes

Projet expérimental pour l'instant. L'idée est d'extraire une liste de notices Intermarc / RDF pour confronter les zones entre elles et identifier quelle zone Intermarc a généré quelle propriété RDF.

Etapes :
* Extraction d'une liste d'ARK à partir d'une requête SRU (sur un type de notice)
* Récupération des notices MARC correspondantes
* Récupération des propriétés RDF (ark et ark#about)
* Pour chaque ressource RDF
** pour chaque propriété RDF, on cherche la zone Intermarc contenant cette valeur

Au passage, le script splitte les valeurs trouvées dans le RDF quand certains séparateurs. 

Il concatène aussi certaines zones Intermarc identifiées comme source (100$am + 100$a correspond au foaf:name)

## A faire

* **AUT** : 
  * **date de début** : 008 pos.28-31 (année), pos.32-33 (mois), pos.34-35 (jour)
  * **date de fin** : 008 pos.38-41 (année), pos.42-43 (mois), pos.44-45 (jour)
  * **Nationalité** : 008 pos.12-13
  * **Langue** : 008 pos.14-15
  * **Sexe** : 008 pos.17
* **BIB** :
  * **date de début** : 008 pos.08-11 (année)
  * **date de fin** : 008 pos.13-16 (année)
  * **Pays** : 008 pos.29-30
  * **Langue** : 008 pos.31-33
