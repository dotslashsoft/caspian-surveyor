import json
import math
from pathlib import Path
from caspian_surveyor.bootstrap.cs_baseline_config import SIMULATION_ARCHIVES

import rebound


class ReboundArchiveManager:
    """Manage native REBOUND Simulationarchive files."""

    def __init__(self, archive_directory=SIMULATION_ARCHIVES):
        self.archive_directory = Path(archive_directory)

    def start_recording(self, sim, filename, interval_years):
        """Enable automatic archiving before integration."""

        if interval_years <= 0:
            raise ValueError("Snapshot interval must be positive.")

        self.archive_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        archive_path = self.archive_directory / filename
        archive_path = archive_path.with_suffix(".bin")

        sim.save_to_file(
            str(archive_path),
            interval=interval_years,
            delete_file=True,
        )

        return archive_path

    def finalize_recording(
        self,
        sim,
        archive_path,
        system_address,
        system_data,
        interval_years,
        status="completed",
    ):
        """Preserve the final state and write Caspian metadata."""

        archive_path = Path(archive_path)
        archive = rebound.Simulationarchive(str(archive_path))

        # Append the final state only if it wasn't already saved.
        if not math.isclose(
            archive.tmax,
            sim.t,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            sim.save_to_file(str(archive_path))
            archive = rebound.Simulationarchive(str(archive_path))

        body_metadata = {}

        for body_id, body in system_data.items():
            body_metadata[str(body_id)] = {
                "name": body.get("name"),
                "type": body.get("type"),
                "immediate_parent": body.get("immediate_parent"),
                "immediate_children": body.get(
                    "immediate_children", []
                ),
            }

        metadata = {
            "schema_version": 1,
            "system_address": system_address,
            "rebound_version": rebound.__version__,
            "integrator": str(sim.integrator),
            "status": status,
            "final_time_years": sim.t,
            "particle_count": sim.N,
            "particle_names": [
                particle.name for particle in sim.particles
            ],
            "snapshot_count": len(archive),
            "archive_start_years": archive.tmin,
            "archive_end_years": archive.tmax,
            "snapshot_interval_years": interval_years,
            "bodies": body_metadata,
        }

        metadata_path = archive_path.with_suffix(".json")

        metadata_path.write_text(
            json.dumps(metadata, indent=4),
            encoding="utf-8",
        )

        return metadata_path

    @staticmethod
    def get_archive_summary(archive_path):
        """Retrieve basic information from an existing archive."""

        archive = rebound.Simulationarchive(str(archive_path))

        return {
            "snapshot_count": len(archive),
            "start_years": archive.tmin,
            "end_years": archive.tmax,
        }

    @staticmethod
    def get_snapshot(
        archive_path: str | Path,
        index: int = -1,
    ) -> rebound.Simulation:
        """Return a saved REBOUND Simulation at an archive index."""

        archive = rebound.Simulationarchive(str(archive_path))
        return archive[index]