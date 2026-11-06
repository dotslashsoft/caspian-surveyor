# Caspian Surveyor - First-Launch

Upon launching Caspian Surveyor for the first time, the application reads the journal files within `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\` and reads the file header. If that file header contains the string `Odyssey`, it processes the events within the journal file and archives the data within SQLite.

This process is called *Historical Event Ingestion*. This process takes ~10 seconds per two-thousand systems processed; commanders with a large volume of exploration data within their journals since the release of Odyssey will experience a longer first-time initialization, taking anywhere from four to five minutes, depending on how current the computer's hardware is.

During *Historical Event Ingestion*, a progress bar will display, giving you a visual of the progress being made.

Once that has completed, Caspian Surveyor will be displayed at the top center of your screen.

---
---

***NOTE: headings will be suffixed of the logical coordinate ([x, y]) location of the panels.***

Annotated Positions:
- [0, 0] - default panel
- [1, 0] - from default panel, cycle right once
- [1, 1] - from default panel, cycle right once, cycle down once
- [1, 2] - from default panel, cycle right once, cycle down twice

---
---

![Caspian Surveyor HUD - Default Panel](_cs_default_hud_panel.png)

## Default (Home) Panel - [0, 0]

HOTKEY: `Ctrl + Alt + HOME`

The default system panel contains:
- System name
- Celestial body count
- Earthlike world body count
- Terraformable water-world body count
- Terraformable high-metal content body count
- Water-world body count
- High-metal content body count
- Landable body count

---
---

![Celestial body panel](_celestial_body_panel.png)

## Celestial Body Panel - [1, 0]

HOTKEYS:
    - `Ctrl + Alt + RIGHT` - cycle right
    - `Ctrl + Alt + LEFT` - cycle left

The celestial body panel contains:
- Body name
- Body class
- Landable (True or False)
- Signals (geological, biological, mining)
- Biological signals
  - Displays two at a time. If there are greater than two signatures, the panel cycles to the next group every five seconds
- Surface Temperature in kelvin
- DSS scan completed

You can cycle right or left as much as you'd like; if you cycle right ten times on a nine body system, the tenth cycle will place you back at the first celestial body

---
---

![Exobio panel](_exobio_panel.png)

## Exobiology Panel - [1, 1]

HOTKEYS: From the celestial body panel
- `Ctrl + Alt + DOWN`: cycle down
- `Ctrl + Alt + UP`: cycle up

Note: the cycle up/down hotkeys will act similarly to the cycle left/right hotkeys. There are three vertical panels. Cycling up three times will place you in the same panel.

The exobiology panel contains:
- Celestial body name
- Variant localised
- Scan status
  - First exobio scan: 1 Sample
  - Second exobio scan: 2 Samples
  - Third exobio scan: Analysed

---
---

![Physical/orbital panel](_physorb_panel.png)

## Physical/Orbital Panel - [1, 2]

HOTKEYS: From the celestial body panel
- `Ctrl + Alt + DOWN`: cycle down
- `Ctrl + Alt + UP`: cycle up

The physical/orbital panel contains:
- Radius: **R⊕**
- Axial tilt: **ε**
- Orbital eccentricity: **e**
- Orbital inclination: **i**
- Orbital period: **P**
- Rotational period: **T**
- Argument of periapsis: **ω**
- Semi-major axis: **a**

---
---

![Physical/orbital legend panel](_physorb_legend.png)

## Physical/Orbital Legend Panel Toggle

HOTKEY: `Ctrl + Alt + ]` (toggle from anywhere)

The physical/orbital legend contains:
- **R⊕** - Radius in Earth radii
- **ε** - Axial tilt/obliquity
- **e** - Orbital eccentricity
- **i** - Orbital inclination
- **P** - Orbital period
- **T** - Rotational period
- **ω** - Argument of periapsis
- **a** - emi-major axis

---
---

![REBOUND panel](_REBOUND_panel.png)

## REBOUND Panel Toggle

HOTKEY: `Ctrl + Shift + R`

The REBOUND panel contains:
- System address
- System name
- System body count

To utilize the REBOUND simulation, you first must get the system address from Elite Dangerous.

*NOTE* - `caspian_surveyor.db` can be explored with third-party tools such as DB Browser.

1. Obtain a system address from a system that has been archived.
2. Enter the system address in the text box to the left of `Fetch System Data`
3. Click `Fetch System Data`.
4. The Metric/Value information will fill out with basic details of the system.
5. In the `Specify years to simulate:` text box, enter the number of years to simulate.
  - NOTE: Please begin at a low number such as `1` or `5`. REBOUND simulations can be resource-intensive.
6. Click `Run Simulation`.
  - If you wish to save the simulation, check the `Save simulation archive (.bin)` check box.
  - You can adjust the number of snapshots the simulation takes, allowing more *states* to be access when replaying the simulation.
7. When the REBOUND simulation completes, the panel will expand, displaying the following:
  - Duration
  - Physical bodies
  - Initial energy
  - Final energy
  - Relative energy drift
8. To exit the REBOUND panel, simple use the toggle hotkey (`Ctrl + Shift + R`) once more

NOTE: If you wish to move the REBOUND window, double-clicking *within* the panel will bring up the title bar, allowing you to drag and move, resize, minimize or simply exiting the REBOUND panel.