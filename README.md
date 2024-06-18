----------------------------------------------------------------------------------
# Articulation du projet de Contrôle/Qualité des données de surfaces brûlées
---------------------------------------------------------------------------------- 

## [1] Récupération des données de surfaces brûlées Sentinel-2 : 01_Recup_data_Sentinel2.ipynb
---------------------------------------------------------------------------------- 

Pour récupérer automatiquement les données de surfaces brûlées il est actuellement utilisé la méthode "crontab".  

Un script shell nommé **"recup_surfaces_brulees_STL2_INSIGHT.sh"** est utilisé et fait appel au serveur INSIGHT pour copier les fichiers du répertoire signifié (dépendnat de la variable $year)  

Un fichier **"crontab"** a été instancié à l'aide d'une WSL débian pour lancer automatiquement la récupération des données une fois par jour **(à 16h00 LT)**

Aide Crontab:

* crontab -e : accès au fichier avec la ligne de commande souhaitée
* sudo service cron restart : permet de prendre en compte les modifications effectuées dans le fichier 
* crontab -l : permet de vérifier la demande 

Les données téléchargées sont au format .gpkg et stockées dans le lecteur réseaux "Archives/FEUX_INSIGHT/$year" et mis à jour quotidiennement.

**Remarque : nécessite d'être connecté au VPN insight, possibilité de paramétrer un docker pour faire le travail.  

## [2] Contrôle des données de surfaces brûlées brutes : 02_Contrôle_Data_Brute.ipynb
---------------------------------------------------------------------------------

## [3] Dashboard de contrôle des données : 03_Dashboard_controle.ipynb
---------------------------------------------------------------------------------

## [4] Dashboard de contrôle des données : 03_Dashboard_controle.ipynb
---------------------------------------------------------------------------------