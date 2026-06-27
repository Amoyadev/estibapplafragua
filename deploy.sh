#!/bin/bash
# Script de deployment a DigitalOcean

DROPLET_IP="209.97.149.174"
DROPLET_USER="root"
DROPLET_PATH="/opt/estiba-app"

echo "=========================================="
echo "🚀 INICIANDO DEPLOY A DIGITALOCEAN"
echo "=========================================="

# Paso 1: Copiar entrypoint.sh actualizado
echo ""
echo "📋 [1/4] Copiando entrypoint.sh al droplet..."
scp -o StrictHostKeyChecking=no \
    c:/estibapp/APP/entrypoint.sh \
    ${DROPLET_USER}@${DROPLET_IP}:${DROPLET_PATH}/

echo "✅ Archivo copiado"

# Paso 2: Hacer ejecutable el script
echo ""
echo "🔐 [2/4] Haciendo ejecutable el script..."
ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} \
    "chmod +x ${DROPLET_PATH}/entrypoint.sh"

echo "✅ Script actualizado"

# Paso 3: Reconstruir containers
echo ""
echo "🐳 [3/4] Reconstruyendo containers (esto toma ~30 segundos)..."
ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} \
    "cd ${DROPLET_PATH} && docker-compose down && docker-compose up -d --build"

echo "✅ Containers reconstruidos"

# Paso 4: Esperar y verificar
echo ""
echo "⏳ [4/4] Esperando 10 segundos para que inicie el container..."
sleep 10

echo ""
echo "=========================================="
echo "📊 ESTADO DE CONTAINERS"
echo "=========================================="
ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} \
    "cd ${DROPLET_PATH} && docker-compose ps"

echo ""
echo "=========================================="
echo "📝 LOGS DEL CONTAINER WEB"
echo "=========================================="
ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} \
    "docker logs estiba_web 2>&1 | tail -60"

echo ""
echo "=========================================="
echo "🌐 PROBANDO CONEXIÓN HTTP"
echo "=========================================="
ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} \
    "curl -s -I http://localhost/ | head -15"

echo ""
echo "=========================================="
echo "✅ DEPLOY COMPLETADO"
echo "=========================================="
echo ""
echo "📌 Para ver logs en tiempo real:"
echo "   ssh root@${DROPLET_IP} 'cd ${DROPLET_PATH} && docker logs -f estiba_web'"
echo ""
echo "📌 Para acceder a la app:"
echo "   http://${DROPLET_IP}/"
echo ""
