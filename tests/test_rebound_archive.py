from typing import Iterable, cast
import rebound
from caspian_surveyor.rebound.rebound_adapter import ReboundAdapter
from caspian_surveyor.rebound.rebound_archive import (
    ReboundArchiveManager,
)
from caspian_surveyor.bootstrap.cs_baseline_config import SIMULATION_ARCHIVES


def test_simulation_archive():
    system_address = 77284230795
    simulation_years = 25.0
    snapshot_count = 5000

    archive_manager = ReboundArchiveManager(
        SIMULATION_ARCHIVES / "test_simulation_archives"
    )

    adapter = ReboundAdapter()

    adapter.prepare_system_simulation(
        system_address=system_address,
        sim_years=0.0,
    )

    sim = adapter.sim

    archive_path = archive_manager.start_recording(
        sim=sim,
        filename=f"{system_address}_test.bin",
        interval_years=simulation_years / snapshot_count,
    )

    status = "completed"

    try:
        sim.integrate(simulation_years)

    except rebound.Collision:
        status = "collision"
        print(f"Collision detected at year {sim.t:.6f}")

    metadata_path = archive_manager.finalize_recording(
        sim=sim,
        archive_path=archive_path,
        system_address=system_address,
        system_data=adapter.handler.system_data,
        interval_years=simulation_years / snapshot_count,
        status=status,
    )

    summary = archive_manager.get_archive_summary(archive_path)

    print(f"Archive: {archive_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Status: {status}")
    print(f"Snapshots: {summary['snapshot_count']}")
    print(f"Start: {summary['start_years']:.6f} years")
    print(f"End: {summary['end_years']:.6f} years")

    middle_index = summary["snapshot_count"] // 2

    snapshot = archive_manager.get_snapshot(
        archive_path,
        index=middle_index,
    )

    print(f"\nSnapshot time: {snapshot.t:.6f}")
    print(f"Physical bodies: {snapshot.N}")

    particles = cast(
        Iterable[rebound.Particle],
        snapshot.particles,
    )

    for particle in particles:
        print(
            f"{particle.name}: "
            f"({particle.x:.6f}, "
            f"{particle.y:.6f}, "
            f"{particle.z:.6f}) AU"
        )


if __name__ == "__main__":
    test_simulation_archive()
