----------------------------------------------------------------------------------
# Articulation du projet de Contrôle/Qualité des données de surfaces brûlées
---------------------------------------------------------------------------------- 
---------------------------------------------------------------------------------

# Contrôle des données (rep Contrôle)

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

---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------

# Qualification des données (rep Qualif)

## [5] Génération des indicateurs spectraux + création des NetCDF : 01_indicateurs_spectraux.ipynb   
---------------------------------------------------------------------------------

Cette étape a fait l'objet d'une externalisation auprès d'APID pour faire une étude de faisabilité et un benchmarking des librairies disponibles, les livrables de cette étude sont disponibles dans ce répertoires : N:\Informatique\SIG\Etudes\2023\2309_QC_feux\LIVRABLE  

Ce script à pour but de récupérer les valeurs de bandes des images Sentinel-2 sur un intervale de date modifiable (aujourd'hui : jusqu'à 150 jours avant la date de détection et 40 jours après) pour chacune de nos formes, et calculer des indicateurs spectraux à l'échelle d'une bbox autour de notre formes et pour chacun des pixels avant de les stocker dans un fichier NetCDF.  

Un fichier NetCDF = 1 forme, ils contiennent actuellement les indicateurs suivants, la plage temporelle est fortement dépendante de la disponibilité des images et de la qualité des images (nuages) :  

- NDVI
- NDWI
- NBR
- NBR+
- BAIS2
- BADI
- Mask de la forme

Pour récupérer les bandes Sentinel, l'outil STAC et le catalogue Amazon sont utilisés (attention catalogue incomplet) https://earth-search.aws.element84.com/v1  
La nomenclature des noms de fichier NetCDF est la suivante : **"nom_de_tuile"+"date"+"surface_id_h3".nc** 

Pour augmenter la rapidité d'exécution du script, une parallélisation du script a été réalisé avec dask, les fchiers en sortie sont stockés sur le disque Archives : A:\INDICATEUR_FEUX\

## [6] Qualification des surfaces : 02_qualification_data.ipynb  
---------------------------------------------------------------------------------

Ce script utilise les valeurs des indicateurs spectraux issues des fichiers NetCDF ainsi que les points chauds VIIRS SNPP et NOAA-20.  
Les valeurs des indicateurs sont regroupées à l'échelle de la forme par un calcul de médiane.  

Actuellement, trois étapes sont réalisées dans ce script pour invalider ou valider les formes.  

- Les étapes d'invalidation des formes :  
    - Clasification kmeans utilisant les indicateurs NDVI et NBR, ils permettent de mettre en évidence les surfaces étant sur une végétation en bonne santé, les formes invalidées seront identifiéess dans l'attribut Qualification de la table "sentinel_surfaces_detectees" comme : ** invalid_niv1 **   
    - Les séries temporelles nous pemettent de mettre en évidence des tendances sur l'indicateur NBR, une tendance égale à 0 ou positive n'inquera pas de perte franche de végétation, les formes qui seront le plus souvent caractérisées par ces tendances positives seront les zones de cuirasse ou de repousse végétale. Ces formes seront identifiéess dans l'attribut Qualification de la table "sentinel_surfaces_detectees" comme : ** invalid_niv2 **     
- Les étape de validation des formes :  
    - Les formes intersectants des points chauds VIIRS dans un intervalle de temps de -10 jours jusqu'à la date de détection par rapport à la date de la ruptures estimée du NBR + ayany un dNBR >= 0.11 sont validées, dans la table "sentinel_surfaces_detectees" la valeur de qualification sera : ** validation_viirs_dnbr **   

Ces formes ne seront pas incluses dans les intersections avec les ZAE et n'auront pas de photo-interprétation dédiée.   

## [7] Génération des intersections (table de faits) : script bilbo    
---------------------------------------------------------------------------------

Pour faire les intersections des formes de surfaces brûlées avec les zones à enjeux et les HER, la configuration suivante est nécessaire :    
    
    - Fichiers yaml : Sentinel_Zones_Brulees_CQ.yaml et Zones_enjeux_incendies_CQ.yaml  

L'organisation des run.py doit etre comme suit :   

    list_data_to_calculate  = [ # ZOI / individu
        "Sentinel_Zones_Brulees_CQ"
    ]

    steplist= [1,2,3]  # 1 : generate indicators by spatial intersection (interpolation/raster/vector)/ 2: spliting byDims & calculate ratio... / 3: persist
    list_indicateur_to_calculate = [ # thematique
        "Zones_enjeux_incendies_CQ"
    ]
    listIdMulti=[listIdSpatialHER]
    

Faire attention de choisir les limites de date souhaitées de la table "sentinel_surfaces_detectees" qui est appelé dans le catalogue intake "Fire_Detection_Data_Quality.yaml", les données seront également filtrées sur l'attribut "qualification" toutes les données "null" dans cette colonne seront utilisées.      

La table de fait sera réutilisée pour faire la photo-inteprrétation dans l'application dédiée.  

----------------------------------------------------------------------------------
##FIN du CONTROLE QUALITE DES DONNEES SORTIE DE CHAINE
-----------------------------------------------------------------------------------