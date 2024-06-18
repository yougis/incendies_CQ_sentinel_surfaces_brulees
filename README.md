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

Ce dashboard utilise la technologie Panel pour générer les widgets et les appels de widget. Il n'est pas déployé car nécessite une application de fond telle que (Azure, )
Il permet de visualiser plusieurs choses :  

Premièrement :  

- Des chiffres clés tels que le nombre de détection, mono-détection, pluri-détections et les surfaces associées à chaque groupes.  
- Un tableau des mêmes groupes mais pour chaque tuile 
- Une carte pour localiser les densités de surface détectées selon la localisation en nécessite

Deuxièmement :  
- Selon la sélection de la tuile une graphique en barre s'affichera avec dessus, le nombre de détection Sentinel-2, Viirs SNPP et Viirs NOAA-20 sur la période choisie
- Un plot associé au graph précédent avec les valeurs de cloud cover pour chacun des passages Sentinel-2
- Une série d'image tumbnail Sentinel-2 sur la période et la tuile choisie, permet de vérifier la qualité d'une image 

L'objectif du dashboard est d'identifer de possible manquement de détection dû à un manque d'image source (Théia) ou un bug de l'algorithme de détection si aucune surface est détectées alors qu'il y a présence de points chauds Viirs et/ou des images de bonnes qualitées.
## [4] Identification des polygones avec des nuages : 04_Cloud_cover_SCL_detection.ipynb
---------------------------------------------------------------------------------