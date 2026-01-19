# Data Import Scripts

Scripts for parsing, normalizing, and importing Coffee-Berry store data from KMZ/KML files.

## Workflow

1. **Parse KMZ/KML**: Extract stores and polygons from KMZ file
2. **Normalize Data**: Clean and match polygons to stores
3. **Import to Database**: Insert into PostgreSQL database
4. **Validate**: Check data quality and generate reports

## Usage

### 1. Parse KMZ File

```bash
python scripts/parse_kmz.py "Existing Data/Coffee Berry 2025.kmz" parsed_data.json
```

This extracts:
- Store locations (Point Placemarks)
- Polygons (Polygon Placemarks)
- Metadata (names, folders, styles)

### 2. Normalize Data

```bash
python scripts/normalize_data.py parsed_data.json normalized_data.json
```

This:
- Extracts store IDs from names (e.g., "(005)" → "005")
- Normalizes store names
- Matches polygons to stores
- Assigns polygon types (dedicated/delivery)

### 3. Import to Database

```bash
# Set database URL
export DATABASE_URL="postgresql://postgres:password@localhost:5432/coffee_berry"

# Dry run first
python scripts/import_data.py normalized_data.json --dry-run

# Actual import
python scripts/import_data.py normalized_data.json
```

This:
- Creates stores in database
- Creates polygon versions (sets first version as `is_current=true`)
- Handles duplicates (updates existing stores)
- Maps polygon types correctly

### 4. Validate Import

```bash
python scripts/validate_data.py --output validation_report.json
```

This checks for:
- Stores without polygons
- Duplicate current polygons
- Invalid geometries
- Overlapping polygons
- Delivery polygons not contained in dedicated polygons

## Output Files

- `parsed_data.json`: Raw parsed data from KMZ
- `normalized_data.json`: Cleaned and matched data
- `validation_report.json`: Data quality report

## Notes

- Store IDs are extracted from names using patterns: `(005)`, `[005]`, `#005`, etc.
- Polygon types are inferred from names or default to 'delivery'
- Polygons are matched to stores by store ID, name similarity, or fuzzy matching
- Import script handles duplicates and updates existing records
- All polygons are imported as version 1 with `is_current=true`
