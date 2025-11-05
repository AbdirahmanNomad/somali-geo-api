# 🇸🇴 Somalia Geography & Governance API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: ODbL](https://img.shields.io/badge/License-ODbL-brightgreen.svg)](https://opendatacommons.org/licenses/odbl/)
![Made in Somalia](https://img.shields.io/badge/Made%20in-Somalia-blue?style=for-the-badge&logo=somalia)

**By [Abdirahman Ahmed (Maano)](https://github.com/abdirahmannomad)**  
*"Faafinta aqoonta, iyo xogta Soomaliyeed ee furan."*  
(Open Somali Data Initiative)

> The first open geographic API for Somalia — mapping regions, districts, roads, ports, and postal codes.  
> Free and open for developers, researchers, and Somali communities everywhere.

An open-source, production-ready API providing Somali geographic and infrastructure data. The first comprehensive open geographic API for Somalia, combining administrative boundaries, roads, transport infrastructure, and postal codes.

## 🎉 Current Status

**✅ PRODUCTION-READY** with **26,343 real Somalia-only geographic items** loaded:

- ✅ **36 Regions** (GADM - Administrative Boundaries)
- ✅ **148 Districts** (GADM - Administrative Boundaries)
- ✅ **26,046 Roads** (OpenStreetMap - Major cities road network)
- ✅ **23 Airports** (OpenStreetMap - **Somalia only**, verified and cleaned)
- ✅ **8 Ports** (Major Somali ports: Mogadishu, Berbera, Bosaso, Kismayo, Merca, Hobyo, Garacad, Las Khorey)
- ✅ **17 Checkpoints** (OpenStreetMap - **Somalia only**, filtered)

**✅ All data filtered to Somalia bounding box** - No non-Somalia locations included.

## 🏗️ Project Overview

This API serves Somali geographic and governance data in clean, structured, and open formats. It works like OpenStreetMap API, GADM boundaries API, and Google PlusCodes resolver - but focused 100% on Somali data.

### Key Features

- 🗺️ **Administrative Boundaries**: 36 regions, 148 districts with full GeoJSON geometries
- 🧭 **Postal Codes**: Google Open Location Code (PlusCodes) with Somali region prefixes
- 🛣️ **Road Infrastructure**: 26,046+ roads from OpenStreetMap (major cities)
- ✈️ **Transport**: 23 verified airports, 8 major Somali ports, 17 checkpoints (all Somalia only)
- 🔍 **Search**: Fuzzy place name search with aliases
- 📊 **Open Data**: All data served as GeoJSON with ODbL licensing

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- SQLite (default) or PostgreSQL/PostGIS (future)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AbdirahmanNomad/somali-geo-api.git
cd somali-geo-api
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
# or with uv
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Download and load real data:
```bash
# Download real data from GADM and OpenStreetMap
python scripts/download_and_load_real_data.py

# Or download OSM data separately
python scripts/download_osm_complete.py

# Load all data into database
python scripts/load_geodata.py
```

5. Run the API:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Optional: Simple Viewer (static)

- A minimal static viewer is included to test and visualize endpoints quickly.
- Location: `frontend/simple`

Run locally:
```bash
cd frontend/simple
python3 -m http.server 8080
# open http://127.0.0.1:8080
```

Notes:
- CORS is already configured to allow http://localhost:8080 during local development.
- Use the endpoint dropdown, filters, and the Location Codes panel to test the API.
- Viewer features: region/type filters, pagination (skip/limit), marker clustering for transport layers.

### Local Auto-Cleanup (transport data)

- In local environment, the backend auto-runs a light data cleanup on startup:
  - Assigns `region` for checkpoints, airports, and ports via point-in-polygon against region polygons
  - Removes transport points outside Somalia polygons
- This keeps results Somalia-only and labeled, without PostGIS. For production-scale spatial queries, migrate to PostGIS.

### Quick Data Verification

After loading data, verify what's loaded:
```bash
cd backend
python -c "
from app.core.db import engine
from app import models
from sqlmodel import Session, select
with Session(engine) as db:
    print(f'Regions: {len(db.exec(select(models.Region)).all())}')
    print(f'Districts: {len(db.exec(select(models.District)).all())}')
    print(f'Roads: {len(db.exec(select(models.Road)).all())}')
    print(f'Airports: {len(db.exec(select(models.Airport)).all())}')
    print(f'Ports: {len(db.exec(select(models.Port)).all())}')
    print(f'Checkpoints: {len(db.exec(select(models.Checkpoint)).all())}')
"
```

## 📚 API Documentation

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

### Core Endpoints

#### Bulk Export (GeoJSON)
```bash
# Regions
curl "http://localhost:8000/api/v1/regions/export" -o regions.geojson
# Districts
curl "http://localhost:8000/api/v1/districts/export" -o districts.geojson
# Roads
curl "http://localhost:8000/api/v1/roads/export" -o roads.geojson
```

## 🗺️ Spatial (PostGIS) Migration Plan

This project runs on SQLite by default. To enable spatial queries (nearby, within polygon), migrate to PostGIS:

1. Provision PostgreSQL with PostGIS extension.
2. Set environment variables in `.env`:
   - `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME`
3. Run Alembic migrations (or re-run loaders to populate PostGIS).
4. Replace Haversine approximations with ST_DWithin/ST_Contains queries in `/roads/nearby` and future polygon endpoints.

## ⚙️ Performance & Caching

- In-memory caching is enabled for hot endpoints scaffold (can be swapped to Redis).
- Redis plan:
  - Add `REDIS_URL=redis://localhost:6379/0` to `.env`
  - Replace in-memory cache with Redis client in `app/core/cache.py`.

## 🔒 Security & CI

- Secrets: never use defaults in production.
  - Set `SECRET_KEY`, `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD` in `.env`.
- CI matrix:
  - Align Node to v25 and pin Python (e.g., 3.11.x) in workflows.
  - Build backend and frontend; run endpoint tests.
- Rate limiting: optional middleware scaffold added; enable via dependency if needed.

## 🧪 Tests

- Endpoint tests: add coverage for regions/districts/roads/transport/locationcode.
- Loader tests: verify counts and Somalia-only filters (bbox/polygon).
- Manual checks:
  - `/api/v1/regions/export` → 36 features
  - `/api/v1/districts/export` → 148 features
  - `/api/v1/roads/export` → 26,046 features
  - `/api/v1/roads/nearby?lat=2.0469&lon=45.3182&radius_km=5` → should return results


#### Paged GeoJSON
```bash
curl "http://localhost:8000/api/v1/roads?format=geojson&limit=10"
```

#### Nearby Queries
```bash
# Roads within 5km of Mogadishu Port
curl "http://localhost:8000/api/v1/roads/nearby?lat=2.0469&lon=45.3182&radius_km=5"
# Districts (places) within 10km of Mogadishu Port
curl "http://localhost:8000/api/v1/places/nearby?lat=2.0469&lon=45.3182&radius_km=10"
```

#### Administrative Boundaries

```http
GET /api/v1/regions
GET /api/v1/regions/{id}
GET /api/v1/districts?region={name}
GET /api/v1/districts/{id}
```

**Example: Get all regions**
```bash
curl http://localhost:8000/api/v1/regions
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Banaadir",
      "code": "SOM-BAN",
      "population": null,
      "area_km2": null,
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [...]
      }
    }
  ],
  "count": 36
}
```

**Example: Get districts in a region**
```bash
curl "http://localhost:8000/api/v1/districts?region=Banadir"
```

**Example District Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Mogadishu",
      "code": "SOM-BNR-MGD",
      "region_name": "Banadir",
      "population": null,
      "aliases": ["Xamar", "Hamari"],
      "centroid": {"lat": 2.0, "lon": 45.3},
      "geometry": {...}
    }
  ],
  "count": 5
}
```

#### Location Codes (Open Location Code)

```http
GET /api/v1/locationcode/generate?lat={lat}&lon={lon}
GET /api/v1/locationcode/resolve?code={code}
```

**Generate Example:**
```bash
curl "http://localhost:8000/api/v1/locationcode/generate?lat=2.0343&lon=45.3201"
```

**Response:**
```json
{
  "code": "8FJ53+PM",
  "latitude_center": 2.0343,
  "longitude_center": 45.3201,
  "region_code": "SOM-BNR"
}
```

**Resolve Example:**
```bash
curl "http://localhost:8000/api/v1/locationcode/resolve?code=8FJ53+PM"
```

#### Roads & Transport

```http
GET /api/v1/roads
GET /api/v1/roads/{id}
GET /api/v1/transport/airports
GET /api/v1/transport/airports/{id}
GET /api/v1/transport/ports
GET /api/v1/transport/ports/{id}
GET /api/v1/transport/checkpoints
GET /api/v1/transport/checkpoints/{id}
```

**Example: Get roads**
```bash
curl "http://localhost:8000/api/v1/roads?limit=10"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "KM4",
      "type": "primary",
      "length_km": null,
      "condition": null,
      "surface": null,
      "geometry": [[45.3108, 2.0314], [45.3109, 2.0315], ...]
    }
  ],
  "count": 26046
}
```

**Example: Get airports**
```bash
# Get all airports
curl "http://localhost:8000/api/v1/transport/airports?limit=5"

# Filter by type (international or domestic)
curl "http://localhost:8000/api/v1/transport/airports?type=international"
curl "http://localhost:8000/api/v1/transport/airports?type=domestic"
```

**Example: Get roads with filtering**
```bash
# Get all roads
curl "http://localhost:8000/api/v1/roads?limit=10"

# Filter by type (primary or secondary)
curl "http://localhost:8000/api/v1/roads?type=primary"
curl "http://localhost:8000/api/v1/roads?type=secondary"
```

#### Place Search

```http
GET /api/v1/places/search?name={name}&limit={limit}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/places/search?name=mogadishu&limit=5"
```

**Response:**
```json
{
  "data": [
    {
      "id": "SOM-BNR-MGD",
      "name": "Mogadishu",
      "region": "Banadir",
      "type": "district",
      "aliases": ["Xamar", "Hamari"],
      "centroid": {"lat": 2.0, "lon": 45.3},
      "population": null
    }
  ],
  "count": 1
}
```

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   │   ├── regions.py
│   │   ├── districts.py
│   │   ├── roads.py
│   │   ├── location_codes.py
│   │   ├── places.py
│   │   └── transport.py
│   ├── core/                 # Configuration
│   ├── models/               # Database models
│   ├── utils/                # Utilities (OLC helper)
│   └── data/                 # GeoJSON data files
├── scripts/
│   └── load_geodata.py       # Data loading script
└── tests/                    # API tests
```

## 🗃️ Data Sources

| Data Type | Count | Source | Format | License |
|-----------|-------|--------|--------|---------|
| **Administrative Boundaries** | 36 regions, 148 districts | [GADM](https://gadm.org) | GeoJSON | Free |
| **Roads** | 26,046 roads | [OpenStreetMap](https://openstreetmap.org) | GeoJSON | ODbL |
| **Airports** | 59 airports (Somalia only, verified) | [OpenStreetMap](https://openstreetmap.org) | GeoJSON | ODbL |
| **Ports** | 8 major Somali ports (Mogadishu, Berbera, Bosaso, Kismayo, Merca, Hobyo, Garacad, Las Khorey) | Manual data entry | GeoJSON | ODbL |
| **Checkpoints** | 46 checkpoints (Somalia only) | [OpenStreetMap](https://openstreetmap.org) | GeoJSON | ODbL |
| **Location Codes** | Algorithm-based | [Google Open Location Code](https://github.com/google/open-location-code) | API | Apache 2.0 |

**Note**: All transport data (airports, ports, checkpoints) is **geographically filtered** to only include locations within Somalia's bounding box.

### Data Download Scripts

- `scripts/download_and_load_real_data.py` - Download GADM and geoBoundaries data
- `scripts/download_osm_complete.py` - Download all OpenStreetMap data
- `scripts/download_roads_alternative.py` - Alternative roads download (city-based)
- `scripts/load_geodata.py` - Load all GeoJSON files into database

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (current), PostGIS (future upgrade)
- **ORM**: SQLModel + SQLAlchemy
- **Data Format**: GeoJSON (standard)
- **Location Codes**: Google Open Location Code library
- **Deployment**: Docker, Render/Railway/Fly.io
- **Data Processing**: Python with requests, geopandas (optional)

## 📊 Current Data Statistics

```
✅ Regions:       36   (GADM - Administrative Boundaries)
✅ Districts:    148   (GADM - Administrative Boundaries)  
✅ Roads:     26,046   (OpenStreetMap - Major Cities Road Network)
✅ Airports:      59   (OpenStreetMap - Somalia Only, Verified ✓)
✅ Ports:          8   (Major Somali Ports: Mogadishu, Berbera, Bosaso, Kismayo, Merca, Hobyo, Garacad, Las Khorey)
✅ Checkpoints:    46  (OpenStreetMap - Somalia Only, Filtered ✓)
─────────────────────────────────────────────────────────────
📊 TOTAL:    26,278   Real Somalia Geographic Items
```

**✅ All data is filtered to Somalia bounding box:**
- Latitude: 1.5° to 11.5° (South to North) - excludes border areas
- Longitude: 41.0° to 51.5° (West to East)

All data is **real, verified, Somalia-only, and sourced from authoritative providers** (GADM, OpenStreetMap).

## 🚀 Deployment

### Docker

```bash
# Build and run
docker-compose up --build
```

### Manual Deployment

1. Set environment variables
2. Run data loader: `python scripts/load_geodata.py`
3. Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Data Contributions

- Submit GeoJSON files for new regions/districts
- Report data inaccuracies
- Add missing place name aliases
- Contribute transport infrastructure data
- Improve road condition data
- Add population statistics

### Improvement Areas

**Recent Improvements Completed:**
- ✅ Geographic filtering - All transport data filtered to Somalia only
- ✅ Airport/road type filtering - Filter airports by `?type=international` or `?type=domestic`
- ✅ Enhanced error messages - 404 errors now show available IDs
- ✅ Database indexes - All key fields indexed for performance

**Planned Enhancements:**
- [ ] Spatial queries (nearby roads, places within bounding box)
- [ ] Population data integration
- [ ] PostGIS migration for advanced spatial queries
- [ ] Redis caching layer
- [ ] API rate limiting
- [ ] Automated data refresh pipeline

## 🚧 Known Limitations

1. **✅ Data Quality**: All transport data now filtered to Somalia bounding box - **FIXED**
2. **Road Coverage**: Roads downloaded from major cities (Mogadishu, Hargeisa, Bosaso, Kismayo); full country coverage may be incomplete
3. **Population Data**: Not all regions/districts have population statistics
4. **Spatial Queries**: Currently using SQLite; PostGIS upgrade planned for advanced spatial queries
5. **Transport Data**: OSM may have limited coverage for Somalia; some airports/ports/checkpoints may be missing from OSM

## 🔮 Future Enhancements

- [ ] PostGIS migration for spatial queries
- [ ] Redis caching layer
- [ ] Nearby/within-bbox spatial endpoints
- [ ] Population data integration
- [ ] Road condition updates
- [ ] Automated data refresh pipeline
- [ ] API rate limiting
- [ ] Enhanced search with fuzzy matching

## 📄 License

**Code**: MIT License
**Data**: ODbL (Open Data Commons Open Database License)

Data sources include:
- © OpenStreetMap contributors
- © GADM
- © OCHA Somalia
- © FAO Somalia

## 🙏 Acknowledgments

- FastAPI community for the excellent framework
- Google for Open Location Code library
- OpenStreetMap contributors
- Humanitarian data providers (OCHA, HDX)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AbdirahmanNomad/somali-geo-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AbdirahmanNomad/somali-geo-api/discussions)
- **Documentation**: [API Docs](http://localhost:8000/docs)

---

**Built with ❤️ for Somalia's open data community**
