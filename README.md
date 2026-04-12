# FreeCAD Post Processors for MOG Pattern & Machine Corp

Custom post processors for FreeCAD CAM (Path workbench) tailored for Mach3/Mach4 CNC controllers.

## Post Processors

### mach4_MOG_AFR_STD_V3_post.py
**Recommended** - Full-featured post processor with advanced capabilities:

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

### mach3_mach4_std_post.py
Standard post processor with core functionality:

- Arc feed rate control
- Spindle ramp-up dwell
- G64 path blending
- Standard preamble/postamble

**Best for:** General-purpose milling operations

### ASTALA_M4Mill-G64-JUN2-spindle-ramp.cps
Autodesk Fusion 360 / HSM post processor for reference:

- Shows Mach4 best practices
- Spindle ramp-up implementation
- G64 path control mode

**Format:** JavaScript (.cps) - Not directly usable in FreeCAD

## Installation

1. Copy the desired `.py` post processor file to your FreeCAD installation
2. In FreeCAD, go to **Edit → Preferences → Path → Job Preferences**
3. Note your "Default Post Processor" directory location
4. Place the post processor in that directory (or reference it directly in Job settings)

**Recommended Location:**
```
C:\Users\[YourUsername]\AppData\Roaming\FreeCAD\Macro\
```

## Usage

### In FreeCAD:

1. Create your CAM Job and operations
2. Select the Job in the tree
3. In the Job properties, set **PostProcessor** to the desired file:
   - `mach4_MOG_AFR_STD_V3_post` (recommended)
   - `mach3_mach4_std_post`
4. Click **Post Process** to generate G-code

### Using Arc Feed Rate Control:

1. Create or select a Profile operation
2. In the **Data** tab, find **ArcFeedRatePercent** property
3. Set percentage (default 100%):
   - `100` = Normal speed (no change)
   - `60` = Arcs run at 60% of profile feed rate
   - `40` = Arcs run at 40% of profile feed rate
4. Generate toolpath and post-process

**Example:**
- Profile horizontal feed rate: 500 in/min
- ArcFeedRatePercent: 60%
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

**Lines 120-127** - POSTAMBLE:
```python
POSTAMBLE = """
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
