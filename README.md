# Récupération des données données surfaces brûlées Sentinel-2

Pour récupérer automatiquement les données de surfaces brûlées il est actuellement utilisé la méthode de "crontab".
Un script shell nommé "recup_surfaces_brulees_STL2_INSIGHT.sh" est utilisé et fait appel au serveur INSIGHT pour copier les fichiers du répertoire signifié (dépendnat de la variable $year)

Un fichier "crontab" a été instancié à l'aide d'une WSL débian pour lancer automatiquement la Récupération des données une fois par jour (à 16h00 LT)