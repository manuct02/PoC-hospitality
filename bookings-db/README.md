# Hotel Bookings Database

This project provides a PostgreSQL database for hotel bookings, along with a data loader that populates the database with synthetic data.

## Prerequisites

- Docker
- Docker Compose
- Python 3.9 or higher
- Required Python packages (pandas, openpyxl, psycopg2-binary)

## Project Structure

```
.
├── src/
│   ├── db/
│   │   ├── init-db.sh
│   │   ├── init.sql
│   │   └── load_data.py
│   ├── generator/
│   │   ├── booking_generator.py
│   │   ├── hotel_generator.py
│   │   ├── hotel_name_location_generator.py
│   │   └── hotel_query_generator.py
│   ├── output/
│   │   ├── booking_output_writer.py
│   │   └── hotel_output_writer.py
│   └── gen_synthetic_hotels.py
├── config/
│   ├── generate_hotels_param.yaml
│   └── hotel_queries.yaml
├── output/
│   ├── hotels/
│   │   ├── hotels.json
│   │   ├── hotels.xlsx
│   │   ├── hotels.csv
│   │   ├── all_hotels.csv
│   │   ├── hotel_details.md
│   │   ├── hotel_rooms.md
│   │   ├── hotel_room_queries.csv
│   │   └── hotel_bookings.md
│   └── bookings/
│       └── all_bookings.xlsx
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Configuration

The project uses the following configuration files:

1. `config/generate_hotels_param.yaml`: Parameters for generating synthetic hotel data
2. `config/hotel_queries.yaml`: Configuration for hotel queries

## Environment Variables

The following environment variables can be configured:

- `POSTGRES_USER`: PostgreSQL username (default: postgres)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: postgres)
- `POSTGRES_DB`: PostgreSQL database name (default: bookings_db)
- `DATABASE_CONFIG_LOGGING`: Enable/disable database logging (default: NO)

## Usage

1. Generate synthetic data:
```bash
python -m src.gen_synthetic_hotels
```

2. Start/stop the database and load data:
```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_DB=bookings_db  docker-compose up --build
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_DB=bookings_db  docker-compose up
```

## Database Schema

The database contains the following tables:

### bookings
- hotel_name (VARCHAR)
- room_id (VARCHAR)
- room_type (VARCHAR)
- room_category (VARCHAR)
- check_in_date (DATE)
- check_out_date (DATE)
- guest_first_name (VARCHAR)
- guest_last_name (VARCHAR)
- guest_email (VARCHAR)
- guest_phone (VARCHAR)
- guest_country (VARCHAR)
- guest_city (VARCHAR)
- guest_address (VARCHAR)
- guest_zip_code (VARCHAR)
- meal_plan (VARCHAR)
- total_price (DECIMAL)

## Services

### bookings-db
PostgreSQL database service.

### bookings-db-data-loader
Service that initializes the database and loads the data from the Excel file.

## Network

The services communicate through the `prj_hospitality-network` network.

## Volumes

- `bookings_postgresql-db`: Persistent storage for PostgreSQL data
