#!/bin/bash

backup_function() {
    year=2023
    rep_loc="/mnt/a/FEUX_INSIGHT/"$year
    # Connexion au serveur distant
    server_user="oeil"
    server_ip="192.168.13.43"
    server_path="../../mnt/geo-storage/FEUXV2/RESULTS/"$year
    
    # Utilisez rsync pour la sauvegard
    sshpass -p '03il2023!?' rsync -avz --no-perms -e ssh "$server_user@$server_ip:$server_path/*.gpkg" "$rep_loc"
}
# Appeler la fonction de sauvegarde
backup_function
