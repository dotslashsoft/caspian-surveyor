# ------------------------------------
#
#       SQL INSERTS/UPSERTS
#
# ------------------------------------

SYSTEM_INSERT_SQL = """
INSERT INTO systems (
    system_name,
    system_address,
    system_body_count,
    position_x,
    position_y,
    position_z,
    system_fss_complete
)
VALUES (
    :system_name,
    :system_address,
    :system_body_count,
    :position_x,
    :position_y,
    :position_z,
    :system_fss_complete
)
"""

SYSTEM_UPSERT_SQL = """
INSERT INTO systems (
    system_name,
    system_address,
    system_body_count,
    position_x,
    position_y,
    position_z,
    system_fss_complete
)
VALUES (
    :system_name,
    :system_address,
    :system_body_count,
    :position_x,
    :position_y,
    :position_z,
    :system_fss_complete
)
ON CONFLICT (
    system_address
)
DO UPDATE SET
    system_body_count = CASE
        WHEN excluded.system_body_count IS NOT NULL
            AND (
                systems.system_body_count IS NULL
                OR excluded.system_body_count > systems.system_body_count
            )
        THEN excluded.system_body_count
        ELSE systems.system_body_count
    END,
    system_fss_complete = MAX(
        systems.system_fss_complete,
        excluded.system_fss_complete
    )
WHERE
    (
        excluded.system_body_count IS NOT NULL
        AND (
            systems.system_body_count IS NULL
            OR excluded.system_body_count > systems.system_body_count
        )
    )
    OR excluded.system_fss_complete > systems.system_fss_complete;
"""

BODY_UPSERT_SQL = """
INSERT INTO bodies (
    database_system_id,
    elite_body_id,
    body_name,
    planet_class,
    star_type,
    terraform_state,
    was_discovered,
    was_mapped,
    was_footfalled,
    landable,
    dss_scan_complete,
    tidal_lock,
    atmosphere,
    atmosphere_type,
    distance_from_arrival
)
VALUES (
    :system_id,
    :body_id,
    :body_name,
    :body_planet_class,
    :body_star_type,
    :body_terraform_state,
    :body_was_discovered,
    :body_was_mapped,
    :body_was_footfalled,
    :body_landable,
    :body_dss_scan_complete,
    :body_tidal_lock,
    :body_atmosphere,
    :body_atmosphere_type,
    :body_distance_from_arrival
)
ON CONFLICT (
    database_system_id,
    elite_body_id
)
DO UPDATE SET
    body_name = COALESCE(
        excluded.body_name,
        bodies.body_name
    ),
    planet_class = COALESCE(
        excluded.planet_class,
        bodies.planet_class
    ),
    star_type = COALESCE(
        excluded.star_type,
        bodies.star_type
    ),
    terraform_state = COALESCE(
        excluded.terraform_state,
        bodies.terraform_state
    ),
    was_discovered = MAX(
        COALESCE(bodies.was_discovered, 0),
        COALESCE(excluded.was_discovered, 0)
    ),
    was_mapped = MAX(
        COALESCE(bodies.was_mapped, 0),
        COALESCE(excluded.was_mapped, 0)
    ),
    was_footfalled = MAX(
        COALESCE(bodies.was_footfalled, 0),
        COALESCE(excluded.was_footfalled, 0)
    ),
    landable = MAX(
        COALESCE(bodies.landable, 0),
        COALESCE(excluded.landable, 0)
    ),
    dss_scan_complete = MAX(
        COALESCE(bodies.dss_scan_complete, 0),
        COALESCE(excluded.dss_scan_complete, 0)
    ),
    tidal_lock = MAX(
        COALESCE(bodies.tidal_lock, 0),
        COALESCE(excluded.tidal_lock, 0)
    ),
    atmosphere = COALESCE(
        excluded.atmosphere,
        bodies.atmosphere
    ),
    atmosphere_type = COALESCE(
        excluded.atmosphere_type,
        bodies.atmosphere_type
    ),
    distance_from_arrival = COALESCE(
        excluded.distance_from_arrival,
        bodies.distance_from_arrival
    )
RETURNING database_body_id;
"""

BODY_PARENTS_UPSERT_SQL = """
INSERT INTO body_parents (
    database_body_id,
    parent_order,
    parent_elite_body_id,
    parent_type
)
VALUES (
    :database_body_id,
    :parent_order,
    :parent_body_id,
    :parent_type
)
ON CONFLICT (
    database_body_id, 
    parent_order
)
DO UPDATE SET
    parent_elite_body_id = excluded.parent_elite_body_id,
    parent_type = excluded.parent_type
"""

BODY_MATERIALS_UPSERT_SQL = """
INSERT INTO body_materials (
    database_body_id,
    material_name,
    material_percentage
)
VALUES (
    :database_body_id,
    :material_name,
    :material_percent
)
ON CONFLICT (
    database_body_id,
    material_name
)
DO UPDATE SET
    material_percentage = excluded.material_percentage
"""

BODY_PHYSORB_UPSERT_SQL = """
INSERT INTO body_physical_orbital_properties (
    database_body_id,
    radius,
    mass,
    surface_gravity,
    surface_pressure,
    surface_temperature,
    semi_major_axis,
    eccentricity,
    orbital_inclination,
    orbital_period,
    ascending_node,
    mean_anomaly,
    rotational_period,
    axial_tilt,
    periapsis
)
VALUES (
    :database_body_id,
    :body_radius,
    :body_mass,
    :body_surface_gravity,
    :body_surface_pressure,
    :body_surface_temperature,
    :body_semi_major_axis,
    :body_eccentricity,
    :body_orbital_inclination,
    :body_orbital_period,
    :body_ascending_node,
    :body_mean_anomaly,
    :body_rotational_period,
    :body_axial_tilt,
    :body_periapsis
)
ON CONFLICT (
    database_body_id
)
DO UPDATE SET
    radius = COALESCE(
        excluded.radius,
        body_physical_orbital_properties.radius
    ),
    mass = COALESCE(
        excluded.mass,
        body_physical_orbital_properties.mass
    ),
    surface_gravity = COALESCE(
        excluded.surface_gravity,
        body_physical_orbital_properties.surface_gravity
    ),
    surface_pressure = COALESCE(
        excluded.surface_pressure,
        body_physical_orbital_properties.surface_pressure
    ),
    surface_temperature = COALESCE(
        excluded.surface_temperature,
        body_physical_orbital_properties.surface_temperature
    ),
    semi_major_axis = COALESCE(
        excluded.semi_major_axis,
        body_physical_orbital_properties.semi_major_axis
    ),
    eccentricity = COALESCE(
        excluded.eccentricity,
        body_physical_orbital_properties.eccentricity
    ),
    orbital_inclination = COALESCE(
        excluded.orbital_inclination,
        body_physical_orbital_properties.orbital_inclination
    ),
    orbital_period = COALESCE(
        excluded.orbital_period,
        body_physical_orbital_properties.orbital_period
    ),
    ascending_node = COALESCE(
        excluded.ascending_node,
        body_physical_orbital_properties.ascending_node
    ),
    mean_anomaly = COALESCE(
        excluded.mean_anomaly,
        body_physical_orbital_properties.mean_anomaly
    ),
    rotational_period = COALESCE(
        excluded.rotational_period,
        body_physical_orbital_properties.rotational_period
    ),
    axial_tilt = COALESCE(
        excluded.axial_tilt,
        body_physical_orbital_properties.axial_tilt
    ),
    periapsis = COALESCE(
        excluded.periapsis,
        body_physical_orbital_properties.periapsis
    )
"""

BODY_SIGNALS_UPSERT_SQL = """
INSERT INTO body_signals (
    database_body_id,
    signal_type,
    signal_type_localised,
    signal_count
)
VALUES (
    :database_body_id,
    :body_signal_type,
    :body_signal_type_localised,
    :body_signal_count
)
ON CONFLICT (
    database_body_id,
    signal_type
)
DO UPDATE SET
    signal_type_localised = excluded.signal_type_localised,
    signal_count = excluded.signal_count
"""

BODY_DETECTED_GENUSES_UPSERT_SQL = """
INSERT INTO body_detected_genuses (
    database_body_id,
    genus,
    genus_localised
)
VALUES (
    :database_body_id,
    :body_genus,
    :body_genus_localised
)
ON CONFLICT (
    database_body_id,
    genus
)
DO UPDATE SET
    genus_localised = excluded.genus_localised
"""

BODY_EXOBIO_SCANS_UPSERT_SQL = """
INSERT INTO body_exobio_scans (
    database_body_id,
    scan_type,
    scan_timestamp,
    genus,
    genus_localised,
    species,
    species_localised,
    variant,
    variant_localised,
    was_logged
)
VALUES (
    :database_body_id,
    :exo_scan_type,
    :exo_scan_timestamp,
    :exo_genus,
    :exo_genus_localised,
    :exo_species,
    :exo_species_localised,
    :exo_variant,
    :exo_variant_localised,
    :exo_was_logged
)
ON CONFLICT (
    database_body_id,
    scan_type,
    scan_timestamp
)
DO NOTHING
"""



# ------------------------------------
#
#       SQL Query Templates
#
# ------------------------------------

GET_MOST_RECENT_BODY = """
SELECT max(database_body_id)
FROM bodies
"""

GET_NEXT_BODY_ID = """
SELECT max(database_body_id) + 1 
FROM bodies
"""

QUERY_BODY_EXOBIO_SCANS = """
SELECT
    bodies.body_name,
    body_exobio_scans.*
FROM bodies
JOIN body_exobio_scans
    ON bodies.database_body_id = body_exobio_scans.database_body_id
"""

QUERY_BODY_DETECTED_GENUSES = """
SELECT
    CONCAT('System Body: ',bodies.body_name) as system_body_name,
    body_detected_genuses.genus_localised
FROM systems
JOIN bodies
    ON systems.database_system_id = bodies.database_system_id
JOIN body_detected_genuses
    ON bodies.database_body_id = body_detected_genuses.database_body_id
"""

QUERY_BODY_SIGNALS = """
SELECT
    CONCAT('Body ID | ', bodies.database_body_id,': ', bodies.body_name) as full_body_id,
    CONCAT('Signal | ', body_signals.signal_type_localised,': ', body_signals.signal_count) as signal_type_count,
    CONCAT('-------------------------------------------------------------')
FROM bodies
INNER JOIN body_signals
    ON bodies.database_body_id = body_signals.database_body_id
ORDER BY bodies.database_body_id
"""

QUERY_ALL_BODIES = """
SELECT DISTINCT
    bodies.database_body_id,
    bodies.body_name,
    body_materials.material_name,
    body_materials.material_percentage
FROM bodies
JOIN body_materials
    ON bodies.database_body_id = body_materials.database_body_id;
"""

QUERY_ALL_SYSTEMS = """
SELECT *
FROM systems
"""


# ------------------------------------
#
#    System Reconstruction Queries
#
# ------------------------------------

GET_SYSTEM_INFO = """
SELECT *
FROM systems
WHERE database_system_id = ?
"""

GET_SYSTEM_BODIES = """
SELECT *
FROM bodies
WHERE database_system_id = ?
"""

GET_SYSTEM_PARENTS = """
SELECT body_parents.*
FROM body_parents
JOIN bodies 
    ON body_parents.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""

GET_SYSTEM_MATERIALS = """
SELECT body_materials.*
FROM body_materials
JOIN bodies 
    ON body_materials.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""

GET_SYSTEM_PHYSORB = """
SELECT body_physical_orbital_properties.*
FROM body_physical_orbital_properties
JOIN bodies 
    ON body_physical_orbital_properties.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""

GET_SYSTEM_SIGNALS = """
SELECT body_signals.*
FROM body_signals
JOIN bodies 
    ON body_signals.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""

GET_SYSTEM_GENUSES = """SELECT body_detected_genuses.*
FROM body_detected_genuses
JOIN bodies 
    ON body_detected_genuses.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""

GET_SYSTEM_EXOBIO = """
SELECT body_exobio_scans.*
FROM body_exobio_scans
JOIN bodies 
    ON body_exobio_scans.database_body_id = bodies.database_body_id
WHERE bodies.database_system_id = ?
"""