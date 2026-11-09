#!/usr/bin/env bash
# Configure Nexus pour servir de registry Docker privé :
#  - change le mot de passe admin initial
#  - active le realm "Docker Bearer Token"
#  - crée le dépôt "docker-hosted" exposé en HTTP sur le port 8082
# Usage : bash ci/nexus-setup.sh <nouveau_mot_de_passe_admin>
set -euo pipefail
# Git Bash (Windows) : empêche la réécriture des chemins /nexus-data/... passés à docker exec
export MSYS_NO_PATHCONV=1

NEXUS_URL="${NEXUS_URL:-http://localhost:8081}"
NEW_PASS="${1:?Usage: $0 <nouveau_mot_de_passe_admin>}"

echo "Attente du démarrage de Nexus..."
until curl -fsS "$NEXUS_URL/service/rest/v1/status/writable" >/dev/null 2>&1; do sleep 5; done

if docker exec nexus test -f /nexus-data/admin.password; then
  INIT_PASS="$(docker exec nexus cat /nexus-data/admin.password)"
  curl -fsS -u "admin:$INIT_PASS" -X PUT -H "Content-Type: text/plain" \
       --data "$NEW_PASS" "$NEXUS_URL/service/rest/v1/security/users/admin/change-password"
  echo "Mot de passe admin modifié."
fi
AUTH="admin:$NEW_PASS"

curl -fsS -u "$AUTH" -X PUT -H "Content-Type: application/json" \
     --data '["NexusAuthenticatingRealm","DockerToken"]' \
     "$NEXUS_URL/service/rest/v1/security/realms/active"
echo "Realm Docker Bearer Token activé."

if curl -fsS -u "$AUTH" "$NEXUS_URL/service/rest/v1/repositories/docker-hosted" >/dev/null 2>&1; then
  echo "Dépôt docker-hosted déjà présent."
else
  curl -fsS -u "$AUTH" -X POST -H "Content-Type: application/json" \
       "$NEXUS_URL/service/rest/v1/repositories/docker/hosted" --data '{
    "name": "docker-hosted",
    "online": true,
    "storage": {"blobStoreName": "default", "strictContentTypeValidation": true, "writePolicy": "allow"},
    "docker": {"v1Enabled": false, "forceBasicAuth": true, "httpPort": 8082}
  }'
  echo "Dépôt docker-hosted créé (registry : localhost:8082)."
fi
