from dataclasses import dataclass


@dataclass
class ReboundSimulationResult:
    system_address: int
    simulation_years: float
    physical_body_count: int
    initial_energy: float
    final_energy: float
    relative_energy_drift: float | None