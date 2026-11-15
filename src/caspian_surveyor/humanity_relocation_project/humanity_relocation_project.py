import math
from math import sqrt
from dataclasses import dataclass, field
from caspian_surveyor.cs_data_structures import FullStarSystemPayload
from caspian_surveyor.db.connection_manager import ConnectionManager
from caspian_surveyor.db.system_archive_reconstruction import ArchivedSystemQueries
from caspian_surveyor.runtime.cs_runtime import load_current_system_record


def kelvin_to_celsius(temp_k: float) -> float:
    return round(temp_k - 273.15, 2)

def ms2_to_earth_g(gravity: float) -> float:
    return round(gravity / 9.80665, 4)

def bell_curve_score(value: float, ideal: float, tolerance: float) -> float:
    """Returns 0.0 to 1.0 based on proximity to an ideal value."""
    return math.exp(-0.5 * ((value - ideal) / tolerance) ** 2)


PLANET_CLASS_SCORES = {
    "Earthlike body": 1.0,
    "Water world": 0.75,
    "Ammonia world": 0.40,
    "High metal content body": 0.25,
    "Rocky body": 0.15,
    "Rocky ice body": 0.07,
    "Icy body": 0.02
}


PLANET_CLASSES = frozenset({
    "Metal rich body",
    "High metal content body",
    "Rocky body",
    "Rocky ice body",
    "Icy body",
    "Earthlike body",
    "Water world",
    "Ammonia world",
    "Water giant",
    "Water giant with life",
    "Gas giant with water based life",
    "Gas giant with ammonia based life",
    "Sudarsky class I gas giant",
    "Sudarsky class II gas giant",
    "Sudarsky class III gas giant",
    "Sudarsky class IV gas giant",
    "Sudarsky class V gas giant",
    "Helium rich gas giant",
    "Helium gas giant",
})


@dataclass
class BodyScoreBreakdown:
    body_id: int
    planet_class: str
    is_terraformable: bool
    class_score: float
    gravity_score: float
    temp_score: float
    total_body_score: float = field(init=False)

    def __post_init__(self):
        # Weighted body score (0.0 to 1.0)
        base = (
            (self.class_score * 0.50) +
            (self.gravity_score * 0.30) +
            (self.temp_score * 0.20)
        )
        # Terraformable bonus without exceeding 1.0
        bonus = 0.20 if self.is_terraformable else 0.0
        self.total_body_score = round(min(1.0, base + bonus), 4)


class BodyScorer:
    def score_body(self, body) -> BodyScoreBreakdown | None:
        if not body.body_planet_class or body.body_surface_temperature is None or body.body_surface_gravity is None:
            return None

        gravity_earth_g = ms2_to_earth_g(body.body_surface_gravity)
        temperature_celsius = kelvin_to_celsius(body.body_surface_temperature)
        is_terraformable = body.body_terraform_state == "Terraformable"

        return BodyScoreBreakdown(
            body_id=body.body_id,
            planet_class=body.body_planet_class,
            is_terraformable=is_terraformable,
            class_score=PLANET_CLASS_SCORES.get(body.body_planet_class, 0.05),
            gravity_score=bell_curve_score(gravity_earth_g, ideal=1.0, tolerance=0.5),
            temp_score=bell_curve_score(temperature_celsius, ideal=15.0, tolerance=35.0),
        )


@dataclass
class SystemReport:
    system_address: int
    distance_from_sol: float
    habitability_subscore: float
    terraformable_subscore: float
    diversity_subscore: float
    final_system_score: float
    body_breakdowns: list[BodyScoreBreakdown]


class SystemScorer:
    def __init__(self, weights: dict[str, float]):
        self.weights = weights
        self.body_scorer = BodyScorer()

    def evaluate_system(self, payload, distance_from_sol: float) -> SystemReport:
        scored_bodies = [
            score for body in payload.planetary_bodies
            if (score := self.body_scorer.score_body(body)) is not None
        ]

        if not scored_bodies:
            return SystemReport(payload.system.system_address, distance_from_sol, 0.0, 0.0, 0.0, 0.0, [])

        # best body score weighted heavily plus average of others
        best_body = max(body.total_body_score for body in scored_bodies)
        average_body = sum(body.total_body_score for body in scored_bodies) / len(scored_bodies)
        habitability_subscore = (best_body * 0.7) + (average_body * 0.3)

        # diminishing returns - caps around three+ terraformable bodies
        terraformable_count = sum(1 for b in scored_bodies if b.is_terraformable)
        terraformable_subscore = min(1.0, terraformable_count / 3.0)

        # unique planet classes in system - greater than five distinct types = 1.0
        unique_classes = len({b.planet_class for b in scored_bodies})
        diversity_subscore = min(1.0, unique_classes / 5.0)

        # Final Weighted Sum (0 to 100 scale)
        raw_total = (
            habitability_subscore * self.weights["current_habitability"] +
            terraformable_subscore * self.weights["terraformable_bodies"] +
            diversity_subscore * self.weights["body_diversity"]
        )

        return SystemReport(
            system_address=payload.system.system_address,
            distance_from_sol=distance_from_sol,
            habitability_subscore=round(habitability_subscore * 100, 2),
            terraformable_subscore=round(terraformable_subscore * 100, 2),
            diversity_subscore=round(diversity_subscore * 100, 2),
            final_system_score=round(raw_total * 100, 2),
            body_breakdowns=scored_bodies
        )


class HumanityRelocationProject:
    def __init__(self) -> None:
        self.weighted_mappings = {
            "current_habitability": 0.50,
            "terraformable_bodies": 0.30,
            "body_diversity": 0.20,
        }
        self.scorer = SystemScorer(weights=self.weighted_mappings)

    def evaluate_archived_system(self, system_address: int) -> SystemReport:
        """Fetches a system by address from SQLite DB and returns its habitability report."""
        payload = self._get_fullstarsystempayload(system_address)
        distance = self._get_distance_from_sol(payload)
        return self.scorer.evaluate_system(payload, distance)

    def evaluate_current_system(self) -> SystemReport:
        """Loads the current system record and returns its habitability report."""
        payload = self._verify_current_system()
        distance = self._get_distance_from_sol(payload)
        return self.scorer.evaluate_system(payload, distance)

    def _get_fullstarsystempayload(self, system_address: int) -> FullStarSystemPayload:
        system_query = ArchivedSystemQueries()
        connection = ConnectionManager()
        conn = connection.establish_db_connection()

        try:
            connection.initialize_schema(conn)
            payload = system_query.get_archived_system_info(conn, system_address)
            return self._validate_payload(payload)
        finally:
            connection.close_db_connection(conn)

    def _verify_current_system(self) -> FullStarSystemPayload:
        current_system = load_current_system_record()
        return self._validate_payload(current_system)

    def _validate_payload(self, payload) -> FullStarSystemPayload:
        if not isinstance(payload, FullStarSystemPayload):
            raise TypeError(f"Expected FullStarSystemPayload, got {type(payload).__name__}")
        return payload

    def _get_distance_from_sol(self, system: FullStarSystemPayload) -> float:
        position_x, position_y, position_z = system.system.system_position
        return round(sqrt(position_x**2 + position_y**2 + position_z**2), 4)


if __name__ == "__main__":
    hrp = HumanityRelocationProject()

    current_system = hrp.evaluate_current_system()
    print(f"-======= CASPIAN FIELD REPORT - CURRENT SYSTEM =======-")
    print(f"System Address: {current_system.system_address}")
    for body in current_system.body_breakdowns:
        print(f"  - Body {body.body_id} ({body.planet_class}): {body.total_body_score}")

    print(f"\nCurrent System Score: {current_system.final_system_score}/100 ({current_system.distance_from_sol} LY from Sol)\n\n")

    archived_report = hrp.evaluate_archived_system(system_address=3615411171)
    print(f"-======= CASPIAN FIELD REPORT - ARCHIVED SYSTEM =======-")
    print(f"System Address: {archived_report.system_address}")
    for body in archived_report.body_breakdowns:
        print(f"  - Body {body.body_id} ({body.planet_class}): {body.total_body_score}")

    print(f"\nArchived System Score: {archived_report.final_system_score}/100 ({archived_report.distance_from_sol} LY from Sol)")