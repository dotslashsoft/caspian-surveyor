# Caspian Surveyor - An Elite Dangerous Exploration Companion

## What is Caspian Surveyor?
Caspian Surveyor is an exploration companion for Elite Dangerous built to turn raw journal data into a persistent, readable record of your journey. It monitors the Elite Dangerous journal in real time, maintains exploration history across sessions, and presents current system data through an in-game HUD-style overlay.

The project aims to improve the exploration experience for the Elite Dangerous community by providing quality-of-life tools and contributing to a more satisfying exploration gameplay loop.

## Current Version and Alpha Status

- Current Version: 0.9.9.0
- Alpha Status: Caspian Surveyor development is active and ongoing, receiving regular updates for features and bug fixes.

## What Caspian Surveyor Currently Does

- Live Elite Dangerous journal monitoring
- Current-system and body survey reconstruction
- Historical Odyssey journal ingestion and archive reconstruction
- Persistent exploration history
- SQLite-backed archive for systems, bodies, signals, and exobiology scans
- HUD-style exploration overlay
- Exobiology, biosignal, and planetary survey tracking
- Orbital and physical body data display
- Customizable HUD colors and theming
- REBOUND simulations for archived systems
    - Option to save the simulation and configure the number of simulation snapshots

## Reporting Bugs

Bug reports can be submitted through GitHub Issues.

When reporting a bug, please include:

- Caspian Surveyor version
- A description of what happened
- Steps to reproduce the issue, if known
- The relevant Caspian Surveyor log file

Logs are stored under:

```text
%LOCALAPPDATA%\CaspianSurveyor\logs\
```