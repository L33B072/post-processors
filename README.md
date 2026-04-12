# Post Processors for MOG Pattern & Machine Corp

Custom post processors for various CAM software packages tailored for MOG's CNC machines and controllers.

## Overview

This repository contains post processors for multiple CAM applications:
- **FreeCAD** - Open-source parametric CAD/CAM
- **Fusion 360** - Autodesk cloud-based CAD/CAM
- Other CAM systems as needed

All post processors are optimized for **Mach3/Mach4 CNC controllers** and MOG's specific machine requirements.

---

## FreeCAD Post Processors

### mach4_MOG_AFR_STD_V3_post.py
**Application:** FreeCAD CAM (Path Workbench)  
**Controller:** Mach4  
**Status:** ✅ Recommended - Production Ready

- **Arc Feed Rate Control** - Independent feed rate control for arc moves (G2/G3) vs linear moves (G1)
- **Spindle Ramp-Up** - Automatic 10-second dwell after spindle start (M3/M4)
- **G64 Path Blending** - Smooth continuous motion through corners
- **Safe Motion Sequences** - Proper Z retraction before XY moves
- **Comprehensive G/M Code Reference** - Embedded documentation

**Features:**
- Reads `ArcFeedRatePercent` property from Profile operations (from CAM Extensions)
- Outputs G4 P10000 (10-second dwell) after spindle commands
- Custom preamble/postamble with safe homing sequences
- Imperial units (G20) by default
- 4 decimal precision

**Best for:** Foam cutting, finishing operations, projects requiring precise arc speed control

---

### mach3_mach4_std_post.py
**Application:** FreeCAD CAM (Path Workbench)  
**Controller:** Mach3/Mach4  
**Status:** ✅ Stable - General Purpose

- Arc feed rate control
- Spindle ramp-up dwell
- G64 path blending
---

## Fusion 360 Post Processors

### ASTALA_M4Mill-G64-JUN2-spindle-ramp.cps
**Application:** Autodesk Fusion 360 / HSM  
**Controller:** Mach4  
**Reference implementation of Mach4 best practices
- Spindle ramp-up timing examples
- G64 path control mode configuration
- JavaScript-based post processor format

**Note:** This is a reference file showing best practices that were adapted for FreeCAD posts.

---
**Installation:**
1. Copy the desired `.py` post processor file to your FreeCAD Macro directory
2. Default location: `C:\Users\[YourUsername]\AppData\Roaming\FreeCAD\Macro\`
3. Or reference directly in Job settings

**Usage:**go to **Edit → Preferences → Path → Job Preferences**
3. Note your "Default Post Processor" directory location
4. Place the post processor in that directory (or reference it directly in Job settings)

**Recommended Location:**
```
C:\Users\[YourUsername]\AppData\Roaming\FreeCAD\Macro\
```

## Usage in FreeCAD
2. Select the Job in the tree
3. In **Job properties**, set **PostProcessor**:
   - `mach4_MOG_AFR_STD_V3_post` (recommended)
   - `mach3_mach4_std_post`
4. Click **Post Process** to generate G-code

---

### Fusion 360 Post Processors

**Installation:**
1. In Fusion 360, go to **Manufacture → Manage → Post Library**
2. Click **Import** and select the `.cps` file
3. Post will appear in your library

**Usage:**
1. Select your CAM setup
2. Choose the post processor from the dropdown
3. Click **Post Process** to generate G-code

---

## FreeCAD Feature: Arc Feed Rate Control (recommended)
   - `mach3_mach4_std_post`
4. Click **Post Process** to generate G-code

### Using Arc Feed Rate Control:
---

## Configuration and Customization

### FreeCAD Post Processor
1. Create or select a Profile operation
2. In the **Data** tab, find **ArcFeedRatePercent** property
3. Set percentage (default 100%):
   - `100` = Normal speed (no change)
   - `60` = Arcs run at 60% of profile feed rate
   - `40` = Arcs run at 40% of profile feed rate
4. Generate toolpath and post-process

**Example:**
- Profile horizontal feed rate: 500 in/min
- A#rcFeedRatePercent: 60%
- Result: G1 moves at 500 in/min, G2/G3 moves at 300 in/min

## Configuration Options

### Spindle Ramp-Up Time
To adjust the dwell time after spindle start, edit the post processor:

**Line ~519** in `mach4_MOG_AFR_STD_V3_post.py`:
```python
out += linenumber() + "G4 P10000 \n"  # 10000 ms = 10 seconds
```

Change `P10000` to your desired milliseconds (Mach4 uses milliseconds):
- P5000 = 5 seconds
- P10000 = 10 seconds (default)
- P20000 = 20 seconds

### Preamble and Postamble
Customize machine initialization and shutdown sequences:

**Lines 107-112** - PREAMBLE:
```python
PREAMBLE = """
G90 G94 G91.1 G40 G49 G17 G64
G20
G28 G91 Z0.
G90
"""
```

---
FreeCAD post processors for comprehensive G-code and M-code reference covering:
- Motion commands (G0-G4)
- Coordinate systems and modes
- Canned cycles
- Spindle and coolant control
- Mach4-specific features

---

## Version History

### FreeCAD PostseCAD CAM Extensions](https://github.com/L33B072/FreeCAD_CAM_Extensions) for ArcFeedRatePercent property

### Fusion 360
- Fusion 360 with CAM workspace
- Cloud or local post processor library access

### CNC Controllers
---

## Adding New Post Processors

To add post processors for other CAM systems:

1. Create a new section in this README with:
   - Application name
   - Controller compatibility
   - Status and purpose
   - Installation instructions
   - Usage notes
2. Place the post processor file in this directory
3. Commit with descriptive message
4. Update version history if applicable

---

- Mach3 or Mach4 CNC controllerfor use with various CAM systems and Mach3/Mach4 controllers.

---

## Support and Contact

**Company:** MOG Pattern & Machine Corp  
**Internal Use:** Contact CAM administrator for customization requests  
**External Users:** This repository may contain company-specific configurations

---

## Related Resource
G17
M05
M9
G28 G91 Z0.
G90
G28 G91 X0. Y0.
G90
M30"""
```

## Requirements

- FreeCAD 1.0 or later with Path workbench
- Mach3 or Mach4 CNC controller
- **Optional:** [FreeCAD CAM Extensions](https://github.com/L33B072/FreeCAD_CAM_Extensions) for ArcFeedRatePercent property

## G-Code Reference

See embedded documentation in `mach4_MOG_AFR_STD_V3_post.py` for comprehensive G-code and M-code reference.

## Version History

### V3 (Current)
- Arc feed rate control from CAM Extensions
- 10-second spindle ramp-up (configurable)
- G64 path blending mode
- Enhanced preamble/postamble sequences
- Embedded G/M code reference documentation

### V2
- Arc feed rate support
- Updated motion sequences

### V1
- Basic Mach3/Mach4 support

## License

These post processors are provided as-is for use with FreeCAD and Mach3/Mach4 controllers.

## Support

**Company:** MOG Pattern & Machine Corp  
**For Issues:** Contact your CAM administrator

## Related Projects

- [FreeCAD CAM Extensions](https://github.com/L33B072/FreeCAD_CAM_Extensions) - Enhanced FreeCAD CAM features including arc feed rate control
- [FreeCAD](https://www.freecad.org/) - Open-source parametric 3D CAD modeler

---

*Last Updated: April 12, 2026*
