#!/bin/bash

# Démarrer le cron en mode debug
cron -f &

# Garder le conteneur en cours d'exécution et vérifier les logs de cron
tail -f /var/log/cron.log
