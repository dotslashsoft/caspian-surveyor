-- foreign key
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS systems (
    database_system_id   INTEGER PRIMARY KEY,
    system_name          TEXT NOT NULL,
    system_address       INTEGER NOT NULL UNIQUE,
    system_body_count    INTEGER,
    position_x           REAL,
    position_y           REAL,
    position_z           REAL
);

CREATE TABLE IF NOT EXISTS bodies (
    database_body_id     INTEGER PRIMARY KEY,
    database_system_id   INTEGER NOT NULL,
    elite_body_id        INTEGER NOT NULL,
    body_name            TEXT,
    planet_class         TEXT,
    star_type            TEXT,
    terraform_state      TEXT,
    was_discovered       INTEGER,
    was_mapped           INTEGER,
    was_footfalled       INTEGER,
    landable             INTEGER,
    dss_scan_complete    INTEGER,
    tidal_lock           INTEGER,
    atmosphere           TEXT,
    atmosphere_type      TEXT,
    distance_from_arrival REAL,
    FOREIGN KEY (database_system_id) REFERENCES systems (database_system_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_bodies_system_elite_id 
ON bodies (database_system_id, elite_body_id);


-- ============================================================================
-- bodies table children; my mind does not work well in SQL
-- ============================================================================

CREATE TABLE IF NOT EXISTS body_parents (
    database_body_id     INTEGER NOT NULL,
    parent_order         INTEGER NOT NULL,
    parent_elite_body_id INTEGER NOT NULL,
    parent_type          TEXT NOT NULL,
    PRIMARY KEY (database_body_id, parent_order),
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS body_materials (
    database_body_id     INTEGER NOT NULL,
    material_name        TEXT NOT NULL,
    material_percentage  REAL NOT NULL,
    PRIMARY KEY (database_body_id, material_name),
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS body_physical_orbital_properties (
    database_body_id     INTEGER PRIMARY KEY,
    radius               REAL,
    surface_gravity      REAL,
    surface_pressure     REAL,
    surface_temperature  REAL,
    semi_major_axis      REAL,
    eccentricity         REAL,
    orbital_inclination  REAL,
    orbital_period       REAL,
    ascending_node       REAL,
    mean_anomaly         REAL,
    rotational_period    REAL,
    axial_tilt           REAL,
    periapsis            REAL,
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS body_signals (
    database_body_id       INTEGER NOT NULL,
    signal_type            TEXT NOT NULL,
    signal_type_localised  TEXT,
    signal_count           INTEGER NOT NULL,
    PRIMARY KEY (database_body_id, signal_type),
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS body_detected_genuses (
    database_body_id   INTEGER NOT NULL,
    genus              TEXT NOT NULL,
    genus_localised    TEXT,
    PRIMARY KEY (database_body_id, genus),
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE IF NOT EXISTS body_exobio_scans (
    database_exobio_scan_id INTEGER PRIMARY KEY,
    database_body_id        INTEGER NOT NULL,
    scan_type               TEXT NOT NULL,
    scan_timestamp          INTEGER NOT NULL,
    genus                   TEXT,
    genus_localised         TEXT,
    species                 TEXT,
    species_localised       TEXT,
    variant                 TEXT,
    variant_localised       TEXT,
    was_logged              INTEGER,
    UNIQUE (database_body_id, scan_type, scan_timestamp),
    FOREIGN KEY (database_body_id) REFERENCES bodies (database_body_id) 
        ON DELETE NO ACTION ON UPDATE NO ACTION
);