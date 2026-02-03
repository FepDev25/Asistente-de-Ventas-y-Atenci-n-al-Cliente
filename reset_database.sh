#!/bin/bash
# Script para reiniciar la base de datos desde cero
# Uso: ./reset_database.sh

set -e  # Detenerse en cualquier error

# Exportar SECRET_KEY si no está definida (para evitar error en init.db.py)
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY="super-secret-sales-agent-key-2026-cuenca"
    export JWT_SECRET="super-secret-sales-agent-key-2026-cuenca"
    echo "🔑 Usando SECRET_KEY por defecto"
fi

echo "🛑 Deteniendo contenedores..."
docker-compose down

echo "🗑️  Eliminando volumen de datos de PostgreSQL..."
docker volume rm practica-4_postgres_data 2>/dev/null || echo "Volumen ya eliminado o no existe"

echo "🧹 Limpiando contenedores huérfanos..."
docker-compose rm -f 2>/dev/null || true

echo "🚀 Iniciando contenedores limpios..."
docker-compose up -d

echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 5

# Verificar que PostgreSQL responde
until docker exec sales_agent_db pg_isready -U postgres > /dev/null 2>&1; do
    echo "   PostgreSQL aún no está listo... esperando"
    sleep 2
done

echo "✅ PostgreSQL está listo"

echo "📦 Instalando dependencias con uv..."
uv pip install email-validator slowapi asyncpg --quiet

echo "🗃️  Ejecutando script de inicialización de base de datos principal..."
uv run python init.db.py

echo ""
echo "🧪 Creando base de datos de tests..."
uv run python init_test_db.py

echo ""
echo "=============================================="
echo "✅ Base de datos reiniciada exitosamente"
echo "=============================================="
echo ""
echo "Bases de datos creadas:"
echo "  • app_db (principal)"
echo "  • sales_ai_test (para tests)"
echo ""
echo "Tablas creadas en ambas bases:"
echo "  • users"
echo "  • product_stocks"
echo "  • orders (NUEVA)"
echo "  • order_details (NUEVA)"
echo ""
echo "Para iniciar el servidor:"
echo "  uv run -m backend.main"
echo ""
echo "Para ejecutar tests:"
echo "  uv run pytest backend/tests -v"
echo ""
