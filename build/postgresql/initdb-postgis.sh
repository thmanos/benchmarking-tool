#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

PGUSER="$POSTGRES_USER" psql --dbname="$POSTGRES_DB" <<-'EOSQL'
    CREATE DATABASE template_postgis;
    UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template_postgis';
EOSQL

for db in template_postgis "$POSTGRES_DB"; do
PGUSER="$POSTGRES_USER" psql --dbname="$db" <<-'EOSQL'
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS hstore;
    CREATE EXTENSION IF NOT EXISTS unaccent;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
    CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder
EOSQL
done

echo "Creating benchmarking tool"
PGPASSWORD=mysecretpassword PGUSER=postgres psql --dbname=postgres <<-'EOSQL'
   CREATE SCHEMA ws_performance_indicator;

   CREATE TABLE ws_performance_indicator."meteo_measurement" (
    id serial4 NOT NULL,
    "parcelId" varchar NOT NULL,
    "timestamp" timestamp NOT NULL,
    temperature numeric NULL,
    humidity numeric NULL,
    windstrength numeric NULL,
    leafwetness numeric NULL,
    rain numeric NULL
   );
   CREATE UNIQUE INDEX meteo_measurement_id_idx ON ws_performance_indicator.meteo_measurement USING btree (id);
   CREATE UNIQUE INDEX meteo_measurement_parcelid_idx ON ws_performance_indicator.meteo_measurement USING btree ("parcelId", "timestamp");

   CREATE TABLE ws_performance_indicator."event" (
    id serial4 NOT NULL,
    dat varchar NULL,
    "parcelId" varchar NOT NULL,
    "eventStart" timestamp NOT NULL,
    "eventEnd" timestamp NULL,
    duration numeric NULL,
    "type" varchar NOT NULL,
    crop varchar NULL,
    variety varchar NULL,
    "comments" varchar NULL,
    amount numeric NULL,
    unit varchar NULL,
    "unitRef" varchar NULL,
    metric varchar NULL,
    target varchar NULL,
    "productName" varchar NULL,
    stage varchar NULL,
    "fuelConsumption" numeric NULL,
    "fuelType" varchar NULL,
    "fuelUnit" varchar NULL,
    "fuelUnitRef" varchar NULL
   );
   CREATE UNIQUE INDEX event_id_idx ON ws_performance_indicator.event USING btree (id);
   CREATE UNIQUE INDEX event_parcelid_idx ON ws_performance_indicator.event USING btree ("parcelId", "eventStart", "eventEnd", type, metric);

   CREATE TABLE ws_performance_indicator.parametric (
    id serial4 NOT NULL,
    "type" varchar NULL,
    value varchar NULL
   );
   CREATE UNIQUE INDEX parametric_id_idx ON ws_performance_indicator.parametric USING btree (id);

   INSERT INTO ws_performance_indicator.parametric ("type",VALUE) VALUES
     ('Unit','ton'),
     ('Unit','kg'),
     ('Unit','gr'),
     ('Unit','kl'),
     ('Unit','lt'),
     ('Unit','ml'),
     ('Unit','m3'),
     ('EventType','spray'),
     ('EventType','irrigation'),
     ('EventType','harvest'),
     ('EventType','fertilization'),
     ('UnitReference','Stremma'),
     ('UnitReference','Hectar'),
     ('FuelType','Diesel'),
     ('FuelType','Gas'),
     ('FuelType','Electricity'),
     ('FuelType','WindTurbine'),
     ('FuelType','Hydro');

   CREATE TABLE ws_performance_indicator.parcel (
    id serial4 NOT NULL,
    "name" varchar NOT NULL,
    polygon public.geometry NULL,
    country varchar NOT NULL,
    county varchar NOT NULL,
    ektaria numeric NULL,
    "user" varchar NULL,
    uid varchar NOT NULL
   );
   CREATE UNIQUE INDEX parcel_id_idx ON ws_performance_indicator.parcel USING btree (id);
   CREATE UNIQUE INDEX uid_idx ON ws_performance_indicator.parcel USING btree (uid);
   CREATE UNIQUE INDEX parcel_name_idx ON ws_performance_indicator.parcel USING btree (name, "user");
   
   ALTER TABLE ws_performance_indicator.event ADD CONSTRAINT parcel_id_fk FOREIGN KEY ("parcelId") REFERENCES ws_performance_indicator.parcel(uid) ON DELETE CASCADE;
   ALTER TABLE ws_performance_indicator."meteo_measurement" ADD CONSTRAINT parcel_id_fk FOREIGN KEY ("parcelId") REFERENCES ws_performance_indicator.parcel(uid) ON DELETE CASCADE;

EOSQL