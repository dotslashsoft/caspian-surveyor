import logging
import cs_journal_toolbox as Journal
from typing import Any
### ### ### ### ### ### ### ### ### ### ### ### 
logger = logging.getLogger(__name__)

class SurveyState:
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

        if event_address != current_system["address"]:
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
            "name": event.get("StarSystem"),
            "address": event.get("SystemAddress"),
            "position": event.get("StarPos"),
            "jump_distance": event.get("JumpDist"),
            "fuel_used": event.get("FuelUsed"),
            "fuel_level": event.get("FuelLevel"),
            "body_count": None,
            "discovery_progress": None,
            "fss_complete": False,
            "bodies": {},
        }

        logger.info("Survey state initialized for system: %s", self.current_system["name"])

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

        current_system["body_count"] = event.get("BodyCount")
        current_system["discovery_progress"] = event.get("Progress")

        return True

    def record_body_signals(self, event) -> bool:
        """
        Records signals discovered from an FSS body scan for a body in the
        current system.

        Args:
            event: Parsed Elite Dangerous journal event containing FSS body
            signal data.

        Returns:
            True if the body signal data was applied to the current survey
            state; otherwise False.
        """

        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        body_id = event.get("BodyID")

        if body_id is None:
            logger.warning("FSSBodySignals event received without BodyID.")
            return False

        body = current_system["bodies"].setdefault(body_id, {})

        body["BodyID"] = body_id
        body["BodyName"] = event.get("BodyName")
        body["Signals"] = event.get("Signals", [])

        return True

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

        body.update(event)

        return True

    def mark_all_bodies_found(self, event) -> bool:
        """
        Processes an "FSSAllBodiesFound" journal event for the current system.

        Sets discovery progress to 1.0 and marks the system's FSS survey as complete.
        If body count has not already been recorded, it is populated from the event.

        Args:
            event: Parsed Elite Dangerous "FSSAllBodiesFound" journal event.

        Returns:
            True if the event newly marked the current system as FSS complete;
            otherwise False.

        For Brandon:
        
        Bridge Keeper: WHAT DOES TRUE MEAN?

        mark_all_bodies_found(): THE SYSTEM WAS NOT COMPLETE BEFORE, BUT IT IS NOW.

        Bridge Keeper: Right. Off you go.
        """     

        current_system = self._get_current_system(event)

        if current_system is None:
            return False

        already_complete = current_system["fss_complete"]

        current_system["fss_complete"] = True
        current_system["discovery_progress"] = 1.0

        if current_system["body_count"] is None:
            current_system["body_count"] = event.get("Count")

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
        body["DSSScanComplete"] = True

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

        elif event_type == "FSSAllBodiesFound":
            return self.mark_all_bodies_found(event)

        return False



class SurveyDataBuilder:

    def __init__(self, survey_state):
        self.survey_state = survey_state


    def build_system_record(self):
        current_system = self.survey_state.current_system

        if current_system is None:
            return None

        bodies = {}

        for body_id, body in current_system["bodies"].items():
            bodies[body_id] = self.build_body_record(body)

        return {
            "schema_version": 1,

            "system": {
                "name": current_system["name"],
                "address": current_system["address"],
                "position": current_system["position"],
                "body_count": current_system["body_count"],
            },

            "summary": self.build_system_summary(),

            "bodies": bodies,
        }

    def build_system_summary(self):
        current_system = self.survey_state.current_system
    
        if current_system is None:
            return None
    
        bodies = current_system["bodies"]
    
        summary = {
            "scan_records": len(bodies),
            "stars": 0,
            "planets": 0,
            "belt_clusters": 0,
            "unknown_scan_objects": 0,
            "landable": 0,
            "hmc": 0,
            "tf_hmc": 0,
            "water_worlds": 0,
            "tf_water_worlds": 0,
            "earthlike_worlds": 0,
            "ammonia_worlds": 0,
        }
    
        for body in bodies.values():
            if body.get("StarType"):
                summary["stars"] += 1
                continue
            
            planet_class = body.get("PlanetClass")
            if planet_class is None:
                body_name = body.get("BodyName", "")
                if "Belt Cluster" in body_name:
                    summary["belt_clusters"] += 1
                else:
                    summary["unknown_scan_objects"] += 1
                    print("UNCLASSIFIED SCAN:", body.get("BodyID"), body.get("BodyName"))
                continue
            
            summary["planets"] += 1
            if body.get("Landable"):
                summary["landable"] += 1
        
            terraformable = (body.get("TerraformState") == "Terraformable")
            if planet_class == "High metal content body":
                summary["hmc"] += 1
    
                if terraformable:
                    summary["tf_hmc"] += 1
        
            elif planet_class == "Water world":
                summary["water_worlds"] += 1
    
                if terraformable:
                    summary["tf_water_worlds"] += 1
    
            elif planet_class == "Earthlike body":
                summary["earthlike_worlds"] += 1
    
            elif planet_class == "Ammonia world":
                summary["ammonia_worlds"] += 1
    
        return summary


    def build_body_record(self, body):
        return {
            "body_id": body.get("BodyID"),
            "body_name": body.get("BodyName"),
            "parents": body.get("Parents", []),
            "planet_class": body.get("PlanetClass"),
            "terraform_state": body.get("TerraformState"),
            "materials": body.get("Materials"),
            "periapsis": body.get("Periapsis"),
            "surface_temperature": body.get("SurfaceTemperature"),
            "was_discovered": body.get("WasDiscovered", False),
            "was_mapped": body.get("WasMapped", False),
            "was_footfalled": body.get("WasFootfalled", False),
            "tidal_lock": body.get("TidalLock", False),
            "atmosphere": body.get("Atmosphere"),
            "atmosphere_type": body.get("AtmosphereType"),
            "radius": body.get("Radius"),
            "surface_gravity": body.get("SurfaceGravity"),
            "surface_pressure": body.get("SurfacePressure"),
            "semi_major_axis": body.get("SemiMajorAxis"),
            "eccentricity": body.get("Eccentricity"),
            "orbital_inclination": body.get("OrbitalInclination"),
            "orbital_period": body.get("OrbitalPeriod"),
            "ascending_node": body.get("AscendingNode"),
            "mean_anomaly": body.get("MeanAnomaly"),
            "rotational_period": body.get("RotationPeriod"),
            "axial_tilt": body.get("AxialTilt"),
            "distance_from_arrival": body.get("DistanceFromArrivalLS"),
            "signals": body.get("Signals"),
            "dss_scan_complete": body.get("DSSScanComplete", False),
            "landable": body.get("Landable", False)
        }

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
        self.survey_state = SurveyState()

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
            journal_events = Journal.get_latest_system_events(journal_file)

            if journal_index == oldest_matching_index:
                self.survey_state.begin_system(journal_events[0])

            self.replay_system_events(self.survey_state, journal_events[1:])

        return self.survey_state.current_system


    def replay_system_events(self, survey_state, events) -> None:
        """
        Replays Elite Dangerous journal events into the current survey state.

        Called by reconstruct_system_data() to process journal events in
        chronological order. Each event is passed to process_journal_event(),
        which applies supported event data to the supplied SurveyState instance.

        Args:
            survey_state: SurveyState instance being reconstructed.
            events: Parsed Elite Dangerous journal events to replay.

        Returns:
            None.
        """
        for event in events:
            survey_state.process_journal_event(event)

    def find_oldest_matching_journal_index(self, latest_journal_events) -> int | None:
        """
        Finds the oldest contiguous journal containing events for the current system.

        Walks backward through Elite Dangerous journals from newest to oldest,
        comparing their SystemAddress against the SystemAddress from the latest
        journal events. Stops when a journal belonging to a different system is
        encountered.

        Called by reconstruct_system_data() to determine where journal replay
        should begin.

        Args:
            latest_journal_events: Parsed journal events for the current system,
                returned by get_latest_system_events().

        Returns:
            The index of the oldest journal containing the matching SystemAddress,
            or None if a matching journal index cannot be determined.
        """

        if not latest_journal_events:
            return None

        current_system_address = (latest_journal_events[0].get("SystemAddress"))

        journal_index = 1

        while True:
            journal_file = Journal.get_journal_file_by_index(journal_index)

            if journal_file is None:
                return journal_index - 1

            journal_events = Journal.get_latest_system_events(journal_file)

            previous_system_address = (journal_events[0].get("SystemAddress")
                if journal_events
                else None)

            if previous_system_address != current_system_address:
                return journal_index - 1

            journal_index += 1