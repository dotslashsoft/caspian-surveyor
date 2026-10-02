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

BODY_INSERT_SQL = """
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
"""

BODY_PARENTS_INSERT_SQL = """
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
"""

BODY_MATERIALS_INSERT_SQL = """
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
"""

BODY_PHYSORB_INSERT_SQL = """
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
"""

BODY_SIGNALS_INSERT_SQL = """
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
"""

BODY_DETECTED_GENUSES_INSERT_SQL = """
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
"""

BODY_EXOBIO_SCANS_INSERT_SQL = """
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
"""