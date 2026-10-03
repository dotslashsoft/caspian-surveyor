SYSTEM_INSERT_SQL = """
INSERT INTO systems (
    system_name,
    system_address,
    system_body_count,
    position_x,
    position_y,
    position_z
)
VALUES (
    :system_name,
    :system_address,
    :system_body_count,
    :position_x,
    :position_y,
    :position_z
)
"""

SYSTEM_UPSERT_SQL = """
INSERT INTO systems (
    system_name,
    system_address,
    system_body_count,
    position_x,
    position_y,
    position_z
)
VALUES (
    :system_name,
    :system_address,
    :system_body_count,
    :position_x,
    :position_y,
    :position_z
)
ON CONFLICT (
    system_address
)
DO UPDATE SET
    system_body_count = excluded.system_body_count
WHERE
    excluded.system_body_count IS NOT NULL
    AND (
        system_body_count IS NULL
        OR excluded.system_body_count > system_body_count
    );
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
    body_name = excluded.body_name,
    planet_class = excluded.planet_class,
    star_type = excluded.star_type,
    terraform_state = excluded.terraform_state,
    was_discovered = excluded.was_discovered,
    was_mapped = excluded.was_mapped,
    was_footfalled = excluded.was_footfalled,
    landable = excluded.landable,
    dss_scan_complete = excluded.dss_scan_complete,
    tidal_lock = excluded.tidal_lock,
    atmosphere = excluded.atmosphere,
    atmosphere_type = excluded.atmosphere_type,
    distance_from_arrival = excluded.distance_from_arrival
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
    radius = excluded.radius,
    surface_gravity = excluded.surface_gravity,
    surface_pressure = excluded.surface_pressure,
    surface_temperature = excluded.surface_temperature,
    semi_major_axis = excluded.semi_major_axis,
    eccentricity = excluded.eccentricity,
    orbital_inclination = excluded.orbital_inclination,
    orbital_period = excluded.orbital_period,
    ascending_node = excluded.ascending_node,
    mean_anomaly = excluded.mean_anomaly,
    rotational_period = excluded.rotational_period,
    axial_tilt = excluded.axial_tilt,
    periapsis = excluded.periapsis
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