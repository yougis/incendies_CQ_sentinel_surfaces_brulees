#!/bin/bash
year=2023
rep_loc="/drives/a/FEUX_INSIGHT/"$year

# COnnexion au serveur distant
server_user="oeil"
server_ip="192.168.13.43"
server_path="../../mnt/geo-storage/FEUXV2/RESULTS/"$year

sshpass -p '03il2023!?' rsync -aP "$server_user@$server_ip:$server_path/*" "$rep_loc"
