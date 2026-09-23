import logging
import caspian_surveyor.cs_journal_toolbox as Journal
from caspian_surveyor.cs_data_structures import (
    BodyMaterialInfo,
    BodyParentInfo,
    BodySignalInfo,
    BodyGenusInfo,
    ExoBioScanInfo,
    CelestialBody,
    FullStarSystemPayload,
    SystemInfo,
    SystemSummaryInfo
)
from typing import Any
### ### ### ### ### ### ### ### ### ### ### ### 
logger = logging.getLogger(__name__)

class SurveyDataAggregator:
    """
    Central location for maintaining the current system survey state.

    Contains methods that initialize a new system survey and apply supported
    Elite Dangerous journal events to the current survey state, including
    discovery scans, body scans, body signals, DSS scans, and FSS completion.

    Journal events are routed through process_journal_event() and applied to
    the appropriate survey-state method.
    """

    def __init__(self):
        self.current_system = None
        notable_stellar_phenomena = []
    
    def _get_current_system(self, event):
        """
        It's in the name, my dude.

        Returns the current system survey state when the supplied Elite Dangerous
        journal event belongs to the active system. Uses "SystemAddress" to prevent
        events from another system from modifying the current survey state.

        If the event does not contain "SystemAddress", the current system is
        returned without address validation.

        Args:
            event: Parsed Elite Dangerous journal event.

        Returns:
            The current system survey-state dictionary if the event belongs to the
            active system; otherwise None.
        """

        current_system = self.current_system

        if current_system is None:
            return None

        event_address = event.get("SystemAddress")

        if event_address is None:
            return current_system

        if event_address != current_system["system_address"]:
            return None

        return current_system

    def begin_system(self, event) -> None:
        """
        Initializes a new system survey from an Elite Dangerous journal event.

        Creates the initial system-state dictionary and assigns it to
        self.current_system.

        Args:
            event: Parsed Elite Dangerous journal event containing the initial
                system data.

        Returns:
            None.
        """
        self.current_system = {
            "system_name": event.get("StarSystem"),
            "system_address": event.get("SystemAddress"),
            "system_position": event.get("StarPos"),
            "system_body_count": None,
            "fss_complete": False,
            "bodies": {},
        }

        logger.info("Survey state initialized for system: %s", self.current_system["system_name"])

    def record_discovery_scan(self, event) -> bool:
        """
        Records FSS discovery scan data for the current system ("honk"),
        including body count and discovery progress.

        Processes the Elite Dangerous "FSSDiscoveryScan" journal event.

        Args:
            event: Parsed Elite Dangerous journal event containing FSS
                discovery scan data.

        Returns:
            True if the current survey state was updated; otherwise False.
        """
        current_system = self._get_current_system(event)
        if current_system is None:
            return False

        current_system["system_body_count"] = event.get("BodyCount")

        return True

    def record_body_signals(self, event) -> bool:
        current_system = self._get_current_system(event)
        if current_system is None:
            return False

        body_id = event.get("BodyID")
        if body_id is None:
            logger.warning("FSSBodySignals event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})

        body["body_id"] = body_id
        body["body_name"] = event.get("BodyName")

        body["body_signals"] = [
            self.translate_body_signal_fields(signal)
            for signal in event.get("Signals", [])
        ]

        return True

    def translate_body_signal_fields(self, signal: dict[str, Any]) -> dict[str, Any]:

        return {
            "body_signal_type": signal.get("Type", "--"),
            "body_signal_type_localised": signal.get("Type_Localised", "--"),
            "body_signal_count": signal.get("Count", 0),
        }

    def record_body_scan(self, event) -> bool:
        """
        Records body data from an FSS body scan in the current system.

        Creates or updates the body entry in the current system's body dictionary
        using the event's BodyID.

        Args:
            event: Parsed Elite Dangerous journal event containing FSS body scan data.

        Returns:
            True if the body scan was applied to the current survey state;
            otherwise False.
        """
        current_system = self._get_current_system(event)
        if current_system is None:
            return False

        body_id = event.get("BodyID")
        if body_id is None:
            logger.warning("Scan event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})
        scan_type = event.get("ScanType")
        scan_types = body.setdefault("_scan_types", [])
        if scan_type and scan_type not in scan_types:
            scan_types.append(scan_type)

        body["body_parents"] = event.get("Parents", [])

        body.update(self.translate_body_scalar_fields(event))
        return True

    def mark_all_bodies_found(self, event) -> bool:
        current_system = self._get_current_system(event)
        if current_system is None:
            return False

        already_complete = current_system["fss_complete"]
        current_system["fss_complete"] = True
        if current_system["system_body_count"] is None:
            current_system["system_body_count"] = event.get("Count")

        return not already_complete

    def record_dss_complete(self, event) -> bool:
        """
        It's in the name, my dude.

        Processes an "SAAScanComplete" journal event for the specified body
        within the current system.

        Args:
            event: Parsed Elite Dangerous journal event containing DSS
                completion data.

        Returns:
            True if the DSS scan was applied to the current survey state;
            otherwise False.
        """

        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("BodyID")

        if body_id is None:
            return False

        body = current_system["bodies"].setdefault(body_id, {})

        body["body_id"] = body_id

        if "BodyName" in event:
            body["body_name"] = event.get("BodyName")

        body["body_dss_scan_complete"] = True

        return True

    def translate_body_genus_fields(self, genus: dict[str, Any]) -> dict[str, Any]:

        return {
            "body_genus": genus.get("Genus", "--"),
            "body_genus_localised": genus.get("Genus_Localised", "--"),
        }

    def record_saa_signals(self, event) -> bool:
        """
        Processes an "SAASignalsFound" journal event for the specified body
        within the current system.

        Args:
            event: Parsed Elite Dangerous journal event containing exobio
                data.

        Returns:
            True if the SAASignalsFound was applied to the current survey state;
            otherwise False.
        """
        current_system = self._get_current_system(event)
        if current_system is None:
            return False

        body_id = event.get("BodyID")
        if body_id is None:
            logger.warning("SAASignalsFound event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})
        body["body_id"] = body_id
        body["body_name"] = event.get("BodyName")

        body["body_signals"] = [
            self.translate_body_signal_fields(signal)
            for signal in event.get("Signals", [])
        ]

        body["body_genuses"] = [
            self.translate_body_genus_fields(genus)
            for genus in event.get("Genuses", [])
        ]

        return True
    
    def record_organic_scans(self, event) -> bool:
        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("Body")

        if body_id is None:
            logger.warning("ScanOrganic event received without Body.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})
        body["body_id"] = body_id

        exobio_scans = body.setdefault("exobio_scans", [])

        exobio_scans.append({
            "exo_scan_type": event.get("ScanType", "--"),
            "exo_genus": event.get("Genus", "--"),
            "exo_genus_localised": event.get("Genus_Localised", "--"),
            "exo_species": event.get("Species", "--"),
            "exo_species_localised": event.get("Species_Localised", "--"),
            "exo_variant": event.get("Variant", "--"),
            "exo_variant_localised": event.get("Variant_Localised", "--"),
            "exo_was_logged": event.get("WasLogged", False),
        })

        return True

    def process_journal_event(self, event) -> bool:
        """
        One journal processor to rule them all.

        Processes supported Elite Dangerous journal events and applies
        their data to the current survey state. FSDJump is currently
        handled separately.

        Args:
            event (dict[str, Any]): Parsed Elite Dangerous journal event.

        Returns:
            bool: True if the event updated survey state; otherwise False.
        """
        event_type = event.get("event")

        if event_type == "FSSDiscoveryScan":
            return self.record_discovery_scan(event)

        elif event_type == "Scan":
            return self.record_body_scan(event)

        elif event_type == "FSSBodySignals":
            return self.record_body_signals(event)

        elif event_type == "SAAScanComplete":
            return self.record_dss_complete(event)

        elif event_type == "SAASignalsFound":
            return self.record_saa_signals(event)

        elif event_type == "ScanOrganic":
            return self.record_organic_scans(event)

        elif event_type == "FSSAllBodiesFound":
            return self.mark_all_bodies_found(event)

        return False

    def translate_body_scalar_fields(self, event: dict[str, Any], ) -> dict[str, Any]:

        return {
            "body_id": event.get("BodyID"),
            "body_name": event.get("BodyName"),
            "body_star_type": event.get("StarType"),
            "body_planet_class": event.get("PlanetClass"),
            "body_terraform_state": event.get("TerraformState"),
            "body_periapsis": event.get("Periapsis"),
            "body_surface_temperature": event.get("SurfaceTemperature"),
            "body_was_discovered": event.get("WasDiscovered", False),
            "body_was_mapped": event.get("WasMapped", False),
            "body_was_footfalled": event.get("WasFootfalled", False),
            "body_tidal_lock": event.get("TidalLock", False),
            "body_atmosphere": event.get("Atmosphere"),
            "body_atmosphere_type": event.get("AtmosphereType"),
            "body_radius": event.get("Radius"),
            "body_surface_gravity": event.get("SurfaceGravity"),
            "body_surface_pressure": event.get("SurfacePressure"),
            "body_semi_major_axis": event.get("SemiMajorAxis"),
            "body_eccentricity": event.get("Eccentricity"),
            "body_orbital_inclination": event.get("OrbitalInclination"),
            "body_orbital_period": event.get("OrbitalPeriod"),
            "body_ascending_node": event.get("AscendingNode"),
            "body_mean_anomaly": event.get("MeanAnomaly"),
            "body_rotational_period": event.get("RotationPeriod"),
            "body_axial_tilt": event.get("AxialTilt"),
            "body_distance_from_arrival": event.get("DistanceFromArrivalLS"),
            "body_landable": event.get("Landable", False),
        }

class SurveyDataBuilder:
    """
    Builds consumable survey-data records from the current SurveyDataAggregator.

    Reads the current system survey state and constructs the structured
    system record used by Caspian Surveyor, including system-level data,
    derived summary statistics, and nested body records.

    SurveyDataBuilder does not process Elite Dangerous journal events
    directly. Journal events are first applied to SurveyDataAggregator, which this
    class then uses as the source for building output records.
    """


    def __init__(self, survey_state):
        self.survey_state = survey_state


    def build_system_record(self) -> FullStarSystemPayload | None:
        """
        Builds the output record for the current system survey state.

        Constructs the system-level record, generates the system summary with
        build_system_summary(), and converts each stored body into an output
        record using build_body_record().

        Returns:
            The completed current-system record, or None if no current system
            survey state exists.

        """ 
        current_system = self.survey_state.current_system

        if current_system is None:
            return None
        
        system_info = self.build_system_info(current_system)
        system_summary = self.build_system_summary(current_system)
        bodies = {}

        for body_id, body in current_system["bodies"].items():
            bodies[body_id] = self.build_body_record(body)

        return FullStarSystemPayload(
            schema_version=1,
            system=system_info,
            summary=system_summary,
            bodies = bodies,
        )

    def build_system_info(self, current_system: dict[str, Any]) -> SystemInfo:
        
        return SystemInfo(
            system_name=current_system["system_name"],
            system_address=current_system["system_address"],
            system_position=current_system["system_position"],
            system_body_count=current_system["system_body_count"],
        )


    def build_system_summary(self, current_system: dict[str, Any]) -> SystemSummaryInfo:
        """
        Builds derived summary statistics for the current system survey state.

        Examines the bodies stored in the current SurveyDataAggregator and calculates
        counts used by build_system_record(), such as planet classifications,
        terraformable bodies, and landable bodies.

        Returns:
            The completed system-summary dictionary, or None if no current
            system survey state exists.
        """    
        bodies = current_system["bodies"]

        system_summary = SystemSummaryInfo(
            system_scan_record_count=len(bodies),
            system_star_count=0,
            system_planet_count=0,
            system_belt_cluster_count=0,
            system_unknown_scan_object_count=0,
            system_landable_body_count=0,
            system_hmc_count=0,
            system_tf_hmc_count=0,
            system_water_world_count=0,
            system_tf_water_world_count=0,
            system_earthlike_world_count=0,
            system_ammonia_world_count=0,
        )

        for body in bodies.values():
            if body.get("body_star_type"):
                system_summary.system_star_count += 1
                continue

            planet_class = body.get("body_planet_class")
            if planet_class is None:
                body_name = body.get("body_name", "")
                if "Belt Cluster" in body_name:
                    system_summary.system_belt_cluster_count += 1
                else:
                    system_summary.system_unknown_scan_object_count += 1
                    print("UNCLASSIFIED SCAN:", body.get("body_id"), body.get("body_name"))
                continue

            system_summary.system_planet_count += 1
            if body.get("body_landable"):
                system_summary.system_landable_body_count += 1

            terraformable = (body.get("body_terraform_state") == "Terraformable")
            if planet_class == "High metal content body":
                system_summary.system_hmc_count += 1

                if terraformable:
                    system_summary.system_tf_hmc_count += 1

            elif planet_class == "Water world":
                system_summary.system_water_world_count += 1

                if terraformable:
                    system_summary.system_tf_water_world_count += 1

            elif planet_class == "Earthlike body":
                system_summary.system_earthlike_world_count += 1

            elif planet_class == "Ammonia world":
                system_summary.system_ammonia_world_count += 1

        return system_summary

    def build_body_parent_record(self, parent: dict[str, int]) -> BodyParentInfo:

        parent_type, parent_body_id = next(iter(parent.items()))

        return BodyParentInfo(
            parent_type=parent_type,
            parent_body_id=parent_body_id
        )

    def build_body_material_record(self, material: dict[str, Any]) -> BodyMaterialInfo:

        return BodyMaterialInfo(
            material_name=material.get("Name", "--"),
            material_percent=material.get("Percent", 0.0)
        )

    def build_body_signal_record(self, body: dict[str, Any]) -> BodySignalInfo:

        return BodySignalInfo(
            body_signal_type = body.get("Type", "--"),
            body_signal_type_localised = body.get("Type_Localised", "--"),
            body_signal_count = body.get("Count", "--")
        )

    def build_body_genus_record(self, body: dict[str, Any]) -> BodyGenusInfo:

        return BodyGenusInfo(
            body_genus = body.get("Genus", "--"),
            body_genus_localised = body.get("Genus_Localised", "--")
        )

    def build_exobio_scan_record(self, exoscan: dict[str, Any]) -> ExoBioScanInfo:

        return ExoBioScanInfo(
            exo_scan_type=exoscan.get("ScanType", "--"),
            exo_genus=exoscan.get("Genus", "--"),
            exo_genus_localised=exoscan.get("Genus_Localised", "--"),
            exo_species=exoscan.get("Species", "--"),
            exo_species_localised=exoscan.get("Species_Localised", "--"),
            exo_variant=exoscan.get("Variant", "--"),
            exo_variant_localised=exoscan.get("Variant_Localised", "--"),
            exo_was_logged=exoscan.get("WasLogged", False)
        )

    def build_body_record(self, body: dict[str, Any]) -> CelestialBody:
        """
        Builds an output record for a single body in the current survey state.

        Transforms body data stored by SurveyDataAggregator into the body-record structure
        used by build_system_record().

        Args:
            body: Survey-state dictionary containing data for a single body.

        Returns:
            The completed body-record dictionary.
        """
        
        raw_body_materials = body.get("Materials")
        body_signals = body.get("body_signals")
        body_genuses = body.get("body_genuses")
        exobio_scans = body.get("exobio_scans")
        
        return CelestialBody(
            body_id = body["body_id"],
            body_name = body["body_name"],
            body_star_type = body.get("body_star_type"),
            body_parents=[
                self.build_body_parent_record(parent)
                for parent in body.get("body_parents", [])
            ],
            body_planet_class = body["body_planet_class"],
            body_terraform_state = body["body_terraform_state"],
            body_materials=([self.build_body_material_record(material)
                                for material in raw_body_materials]
                                if isinstance(raw_body_materials, list)
                                else None),
            body_periapsis = body["body_periapsis"],
            body_surface_temperature = body["body_surface_temperature"],
            body_was_discovered = body["body_was_discovered"],
            body_was_mapped = body["body_was_mapped"],
            body_was_footfalled = body["body_was_footfalled"],
            body_tidal_lock = body["body_tidal_lock"],
            body_atmosphere = body["body_atmosphere"],
            body_atmosphere_type = body["body_atmosphere_type"],
            body_radius = body["body_radius"],
            body_surface_gravity = body["body_surface_gravity"],
            body_surface_pressure = body["body_surface_pressure"],
            body_semi_major_axis = body["body_semi_major_axis"],
            body_eccentricity = body["body_eccentricity"],
            body_orbital_inclination = body["body_orbital_inclination"],
            body_orbital_period = body["body_orbital_period"],
            body_ascending_node = body["body_ascending_node"],
            body_mean_anomaly = body["body_mean_anomaly"],
            body_rotational_period = body["body_rotational_period"],
            body_axial_tilt = body["body_axial_tilt"],
            body_distance_from_arrival = body["body_distance_from_arrival"],
            body_signals=([BodySignalInfo(**signal)
                                for signal in body_signals]
                                if isinstance(body_signals, list)
                                else None),
            body_dss_scan_complete = body.get("body_dss_scan_complete", False),
            body_landable = body["body_landable"],
            body_genuses=([BodyGenusInfo(**genus) for genus in body_genuses]
                                if isinstance(body_genuses, list)
                                else None
                        ),
            exobio_scans=([ExoBioScanInfo(**exoscan) for exoscan in exobio_scans]
                                if isinstance(exobio_scans, list)
                                else None)
        )

class StateRecovery:
    """
    Reconstructs the current system survey state from Elite Dangerous
    journal history.

    Identifies the oldest relevant journal containing the current system,
    initializes survey state from that journal, and replays supported
    journal events forward chronologically through subsequent matching
    journals.
    """
    def __init__(self):
        self.survey_data_aggregator = SurveyDataAggregator()

    def find_oldest_matching_journal_index(self, latest_journal_events: list[dict]) -> int:
        current_system_address = latest_journal_events[0].get("SystemAddress")

        oldest_matching_index = 0
        journal_index = 1

        while True:
            journal_file = Journal.get_journal_file_by_index(journal_index)
            if journal_file is None:
                break

            journal_events = Journal.get_reconstruction_start_events(journal_file)
            if not journal_events:
                journal_index += 1
                continue

            journal_system_address = journal_events[0].get("SystemAddress")
            if journal_system_address != current_system_address:
                break

            oldest_matching_index = journal_index
            journal_index += 1

        return oldest_matching_index

    def reconstruct_system_data(self, latest_journal_events)-> dict[str, Any] | None:
        """
        Loops from the returned value of find_oldest_matching_journal_index(), 
        if the value is not None, and reconstructs system data from events within
        journal[index] -> latest journal.

        Args:
            latest_journal_events: Parsed journal events for the current system,
            returned by get_latest_system_events()

        Returns:
            reconstructed current system state as dict
        """
        if not latest_journal_events:
            return None

        oldest_matching_index = self.find_oldest_matching_journal_index(latest_journal_events)
        if oldest_matching_index is None:
            return None
        
        for journal_index in range(oldest_matching_index, -1, -1):
            journal_file = Journal.get_journal_file_by_index(journal_index)
            if journal_file is None:
                return None
            
            journal_events = Journal.get_reconstruction_start_events(journal_file)
            if not journal_events:
                continue

            if journal_index == oldest_matching_index:
                self.survey_data_aggregator.begin_system(journal_events[0])

            self.replay_system_events(self.survey_data_aggregator, journal_events[1:])
        return self.survey_data_aggregator.current_system


    def replay_system_events(self, survey_data_aggregator, events) -> None:
        """
        Replays Elite Dangerous journal events into the current survey state.

        Called by reconstruct_system_data() to process journal events in
        chronological order. Each event is passed to process_journal_event(),
        which applies supported event data to the supplied SurveyDataAggregator instance.

        Args:
            survey_state: SurveyDataAggregator instance being reconstructed.
            events: Parsed Elite Dangerous journal events to replay.

        Returns:
            None.
        """
        for event in events:
            survey_data_aggregator.process_journal_event(event)