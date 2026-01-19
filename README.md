# Coffee-Berry Stores Management System

A comprehensive store management system with geospatial polygon handling, versioning, and API access for Coffee-Berry Stores.

## Features

- **Store Management**: Complete CRUD operations for stores with location data
- **Polygon Management**: Versioned polygons for dedicated and delivery areas
- **Geospatial Queries**: Optimized point-in-polygon queries for data warehouse (15K+ queries/day)
- **Authentication**: OAuth2 and API Key authentication
- **Frontend**: React-based web interface with Google Maps integration
- **Self-Hosted**: Deploy on Hetzner VMs with Cloudflare Tunnel

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Tunnel                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                   │
└────────┬───────────────────────────────────────┬────────────┘
         │                                       │
┌────────┴────────┐                    ┌────────┴─────────┐
│  React Frontend │                    │  FastAPI Backend │
└─────────────────┘                    └────────┬─────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                            ┌───────┴──────┐      ┌────────┴──────┐
                            │ PostgreSQL   │      │     Redis     │
                            │  + PostGIS   │      │   (Optional)  │
                            └──────────────┘      └───────────────┘
```

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Google Maps API
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, GeoAlchemy2
- **Database**: PostgreSQL 15+, PostGIS 3.3+
- **Cache**: Redis (optional)
- **Deployment**: Docker, Docker Compose, Nginx, Cloudflare Tunnel

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL with PostGIS (or use Docker)
- Google Maps API key (for frontend)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coffee-berry-stores
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Import existing data** (optional)
   ```bash
   # Parse KMZ file
   python scripts/parse_kmz.py "Existing Data/Coffee Berry 2025.kmz" parsed_data.json
   
   # Normalize data
   python scripts/normalize_data.py parsed_data.json normalized_data.json
   
   # Import to database
   python scripts/import_data.py normalized_data.json
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
coffee-berry-stores/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── db/             # Database configuration
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── package.json
├── scripts/                 # Data import scripts
├── deploy/                  # Deployment scripts
├── nginx/                   # Nginx configuration
└── docker-compose.yml       # Docker orchestration
```

## API Documentation

### Authentication

The API supports two authentication methods:

1. **OAuth2** (Client Credentials Flow)
   ```bash
   POST /api/v1/auth/oauth/token
   Authorization: Basic <base64(client_id:client_secret)>
   ```

2. **API Key**
   ```bash
   X-API-Key: <api_key>
   ```

### Key Endpoints

- **Stores**: `/api/v1/stores`
- **Polygons**: `/api/v1/polygons`
- **Geospatial Queries**: `/api/v1/geospatial`
- **Franchisees**: `/api/v1/franchisees`
- **Schedules**: `/api/v1/schedules`
- **Media**: `/api/v1/media`

Full API documentation available at `/docs` when running in development mode.

## Deployment

See [deploy/README.md](deploy/README.md) for detailed deployment instructions on Hetzner VMs with Cloudflare Tunnel.

## Data Import

See [scripts/README.md](scripts/README.md) for instructions on importing existing KML/KMZ data.

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

## Database Schema

Key tables:
- `stores`: Store locations and metadata
- `polygon_versions`: Versioned polygons (dedicated/delivery areas)
- `franchisees`: Franchisee information
- `store_schedules`: Operating hours per day
- `store_media`: Store pictures
- `api_keys`: API key authentication
- `oauth_clients` & `oauth_tokens`: OAuth2 support

See [backend/app/db/schema.sql](backend/app/db/schema.sql) for complete schema.

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions, please refer to the documentation or contact the development team.
