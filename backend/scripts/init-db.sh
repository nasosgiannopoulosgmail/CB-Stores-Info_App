#!/bin/bash
# Initialize database - enable PostGIS extension
# This script runs when the PostgreSQL container is first created

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable PostGIS extension
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "PostGIS extension enabled successfully!"
