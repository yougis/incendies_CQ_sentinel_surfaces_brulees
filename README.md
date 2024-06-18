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

-----------------------------------------------------------------------------------------------  
-----------------------------------------------------------------------------------------------   
Une fois récupéré, les données sont pré-traitée pour les mettres en base, les étapes suivantes sont réalisées :
- Ouverture des fichiers gpkg
- Filtrage des données sur une période temporelle
- Convertir les surfaces en multi-polygones
- Définir un identifiant H3 à chauqe forme et leur générer un identifiant unique (surface_id_h3) avec cette typologie : **'nom_tuile'_'date'_'id_h3'**
- Ajout dans la table (*surfaces_brulees_brute_control*) des surfaces 

## [2] Contrôle des données de surfaces brûlées brutes : 02_Contrôle_Data_Brute.ipynb
---------------------------------------------------------------------------------

Le script de contrôle des données brutes permet de vérifier géométriquement et spatialement des formes pour cela plusieurs étapes de contrôle sont effectuées :  
- Une vérification des tuiles utilisées si différentes des 15 tuiles habituelles 
- Une vérification de surface, si surface inférieure à 1ha
- Une vérification sur les géométries, regarder si elles ont des erreurs
- Regarder si des formes sont des doublons, c'est à dire avec une même géométrie à une même date
- Regarder si des polygones se superposent à une même date, on les fusionnera 
- Regarder si des polygones sont en bords de tuile, les bords de tuile induise une coupure de la forme. Si celle-ci est également détectée sur la tuile voisine une fusion des géomtries sera faite
- Intégration des formes restantes dans la table *sentinel_surfaces_detectees*  

## [3] Dashboard de contrôle des données : 03_Dashboard_controle.ipynb
---------------------------------------------------------------------------------

Ce dashboard utilise la technologie Panel pour générer les widgets et les appels de widget. Il n'est pas déployé car nécessite une application de fond telle que (Azure, )
Il permet de visualiser plusieurs choses :  

Premièrement :  

- Des chiffres clés tels que le nombre de détection, mono-détection, pluri-détections et les surfaces associées à chaque groupes.  
- Un tableau des mêmes groupes mais pour chaque tuile 
- Une carte pour localiser les densités de surface détectées selon la localisation en nécessite

Deuxièmement :  
- Selon la sélection de la tuile un graphique en barre s'affichera avec dessus: le nombre de détection Sentinel-2, Viirs SNPP et Viirs NOAA-20 sur la période choisie
- Un plot associé au graph précédent avec les valeurs de cloud cover pour chacun des passages Sentinel-2
- Une série d'images tumbnail Sentinel-2 sur la période et la tuile choisie, permet de vérifier la qualité d'une image 

L'objectif du dashboard est d'identifer de possible manquement de détection dû à un manque d'image source (Théia) ou un bug de l'algorithme de détection si aucune surface est détectées alors qu'il y a présence de points chauds Viirs et/ou des images de bonnes qualitées.

## [4] Identification des polygones avec des nuages : 04_Cloud_cover_SCL_detection.ipynb
---------------------------------------------------------------------------------

Pour identifer la présence de nuage ou de voile nuageux à l'échelle de la forme, un calcul réalisé à partir de la bande SCL des images Sentinel-2 est réalisé.
Ce calcul utilise les classes [3, 8, 9, 10, 11] correspondant indépendamment à [Cloud Shadow, Cloud medium probability, Cloud high probability, Thin cirrus, Snow or ice]

Si à l'echelle de la forme le pourcentage de cloud cover calculé est supérieur à 0% alors la forme est supprimée de la base de données.  
Pour récupérer les valeurs de bandes SCL pour chaque forme à la date de détection, il est nécessaire d'utliser un catalogue STAC (ici Amazone) la requête de recherche et de récupération du array étant longue, le script a été parallélisé grâce à dask

