Scripts Catalogue BnF (web service SRU)
==

ExtractionCatalogueBnF
--
Programme facilitant l'extraction des données du catalogue BnF, via son SRU

Le script [ExtractionCatalogueBnF.py](ExtractionCatalogueBnF.py) a été converti en exécutable grâce à la librairie Python [cx_freeze](https://anthony-tuininga.github.io/cx_Freeze/), via le fichier [setup_ExtractionCatalogueBnF.py](setup_ExtractionCatalogueBnF.py)

**[L'exécutable Windows est récupérable sur Google Drive](https://drive.google.com/open?id=0B_SuYb5EUx7QRHJya25zOERLZWc)**

## Installation

*   Récupérer le fichier ZIP, le décompresser n'importe où.
*   Lancer le fichier ExtractionCatalogueBnF à la racine
*   Les fichiers rapports sont déposés dans un répertoire /reports, à la racine également

## Utilisation du programme

Quand on double-clique sur le fichier **ExtractionCatalogueBnF**, une fenêtre s’ouvre :


**Dans la moitié gauche : les donnés en entrée,** avec **au choix** :

*   **une URL de requête** SRU BnF  
    sous la forme : [http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.title%20all%20%22recherche%20temps%20perdu%20retrouve%22%20and%20bib.author%20all%20%22proust%22&recordSchema=unimarcxchange&maximumRecords=10&startRecord=1](http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.title%20all%20%22recherche%20temps%20perdu%20retrouve%22%20and%20bib.author%20all%20%22proust%22&recordSchema=unimarcxchange&maximumRecords=10&startRecord=1)  
    Logiquement, à partir du [formulaire de recherche SRU BnF](http://catalogue.bnf.fr/api) et de [la documentation fournie](http://www.bnf.fr/fr/professionnels/recuperation_donnees_bnf_boite_outils/a.service_SRU.html), vous ne devriez pas avoir trop de mal à lancer une requête et récupérer une première liste de résultats au format XML. C’est après, pour savoir quoi faire de ces résultats, que ça se gâte. D’où ce logiciel.
*   **OU un fichier** pouvant contenir plusieurs colonnes (séparées par des tabulations), mais dont la première doit être un numéro de notice ou un ARK BnF  
    Ce fichier a pu être obtenu comme étant le rapport d’une précédente requête, ou encore via une extraction du triple store de [data.bnf.fr](http://data.bnf.fr), ou par tout autre moyen.  
    Attention : pas de guillemets pour encadrer les valeurs de chaque colonne  
    Il faut préciser le chemin d’accès complet au fichier (arborescence des répertoires + nom du fichier **avec** **son** **extension**)
    *   **_Si on a donné en entrée un nom de fichier_**  
        il faut préciser quel format en sortie on veut utiliser pour indiquer les éléments d’information à récupérer : si je dis au programme récupérer la zone 100, celle-ci n’est pas la même en Unimarc (zone de données codées) et Intermarc (auteur principal)  
        Cette information en revanche n’est pas utile si on copie-colle l’URL d’une requête SRU : l’information est déjà dans l’URL

**Dans la moitié droite : les données en sortie**


*   **Le nom du fichier rapport** qui contiendra les informations extraites  
    Ce fichier sera déposé dans un répertoire <span style="text-decoration:underline;">_reports_</span> directement dans le répertoire <span style="text-decoration:underline;">ExtractionCatalogueBnF</span>
*   La liste des éléments d’information à récupérer :
    *   **Pour les formats Marc** : nom des zones et/ou sous-zones.  
        Si vous indiquez une zone, il précisera chaque sous-zone par son dollar. L’ensemble de la zone sera dans une colonne  
        Si vous indiquez une sous-zone, le $ ne sera rappelé que dans le nom de la colonne  
        Vous pouvez mélanger tout ça et mettre par exemple :  
        200;200$a;200$e$i  
        Ce qui vous permettra d’avoir une colonne avec l’ensemble de la zone 200 (zone de titre, en Unimarc), mais aussi dans une colonne à part la 200$a, et encore à côté les compléments éventuels du titre
    *   **Si vous avez choisi Dublin Core :** indiquez simplement le nom des balises à récupérer :  
        dc:identifier;dc:title;dc:creatorSi certaines informations sont répétées, elles seront dans la même colonne, séparées par un ~
*   Si vous voulez extraire des informations concernant des notices d’autorité, vous pouvez récupérer le nombre de notices bibliographiques liées à chacune des notices, en cochant la case idoine  
    C’est une information qui, dans l’interface web du catalogue, est indiquée en bas à droite des notices d’autorité. Dans ce programme, elle mélange les notices liées comme auteur et comme sujet  
    
### On sait que l’extraction est terminée quand…

Le bouton « OK » n’apparaît plus appuyé
