# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *   Copyright (c) 2014 sliptonic <shopinthewoods@gmail.com>               *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************/

import FreeCAD
from FreeCAD import Units
import Path
import argparse
import datetime
import shlex
import Path.Base.Util as PathUtil
import Path.Post.Utils as PostUtils
import PathScripts.PathUtils as PathUtils
from builtins import open as pyopen

TOOLTIP = """
This is a postprocessor file for the Path workbench. It is used to
take a pseudo-G-code fragment outputted by a Path object, and output
real G-code suitable for a mach3_4 3 axis mill. This postprocessor, once placed
in the appropriate PathScripts folder, can be used directly from inside
FreeCAD, via the GUI importer or via python scripts with:

import mach3_4_post
mach3_4_post.export(object,"/path/to/file.ncc","")
"""

now = datetime.datetime.now()

parser = argparse.ArgumentParser(prog="mach3_4", add_help=False)
parser.add_argument("--no-header", action="store_true", help="suppress header output")
parser.add_argument("--no-comments", action="store_true", help="suppress comment output")
parser.add_argument("--line-numbers", action="store_true", help="prefix with line numbers")
parser.add_argument(
    "--no-show-editor",
    action="store_true",
    help="don't pop up editor before writing output",
)
parser.add_argument("--precision", default="3", help="number of digits of precision, default=3")
parser.add_argument(
    "--preamble",
    help='set commands to be issued before the first command, default="G17 G54 G40 G49 G80 G90\\n"',
)
parser.add_argument(
    "--postamble",
    help='set commands to be issued after the last command, default="M05\\nG17 G54 G90 G80 G40\\nM2\\n"',
)
parser.add_argument(
    "--inches", action="store_true", help="Convert output for US imperial mode (G20)"
)
parser.add_argument(
    "--modal",
    action="store_true",
    help="Output the Same G-command Name USE NonModal Mode",
)
parser.add_argument("--axis-modal", action="store_true", help="Output the Same Axis Value Mode")
parser.add_argument(
    "--no-tlo",
    action="store_true",
    help="suppress tool length offset (G43) following tool changes",
)

TOOLTIP_ARGS = parser.format_help()

# These globals set common customization preferences
OUTPUT_COMMENTS = True
OUTPUT_HEADER = True
OUTPUT_LINE_NUMBERS = False
SHOW_EDITOR = True
MODAL = False  # if true commands are suppressed if the same as previous line.
USE_TLO = True  # if true G43 will be output following tool changes
OUTPUT_DOUBLES = True  # if false duplicate axis values are suppressed if the same as previous line.
COMMAND_SPACE = " "
LINENR = 100  # line number starting value

# These globals will be reflected in the Machine configuration of the project
UNITS = "G20"  # G21 for metric, G20 for us standard
UNIT_SPEED_FORMAT = "in/min"
UNIT_FORMAT = "in"

MACHINE_NAME = "mach3_4"
CORNER_MIN = {"x": 0, "y": 0, "z": 0}
CORNER_MAX = {"x": 500, "y": 300, "z": 300}
PRECISION = 4

# Preamble text will appear at the beginning of the GCODE output file.
# PREAMBLE = """G17 G54 G40 G49 G80 G90 G64"""
PREAMBLE = """
G90 G94 G91.1 G40 G49 G17 G64
G20
G28 G91 Z0.
G90
"""

# Postamble text will appear following the last operation.
# POSTAMBLE = """M05
# G17 G54 G90 G80 G40
# M2
# """

POSTAMBLE = """
G17
M05
M9
G28 G91 Z0.
G90
G28 G91 X0. Y0.
G90
M30"""

# Pre operation text will be inserted before every operation
PRE_OPERATION = """"""

# Post operation text will be inserted after every operation
POST_OPERATION = """"""

# Tool Change commands will be inserted before a tool change
TOOL_CHANGE = """"""


def processArguments(argstring):
    global OUTPUT_HEADER
    global OUTPUT_COMMENTS
    global OUTPUT_LINE_NUMBERS
    global SHOW_EDITOR
    global PRECISION
    global PREAMBLE
    global POSTAMBLE
    global UNITS
    global UNIT_SPEED_FORMAT
    global UNIT_FORMAT
    global MODAL
    global USE_TLO
    global OUTPUT_DOUBLES

    try:
        args = parser.parse_args(shlex.split(argstring))
        if args.no_header:
            OUTPUT_HEADER = False
        if args.no_comments:
            OUTPUT_COMMENTS = False
        if args.line_numbers:
            OUTPUT_LINE_NUMBERS = True
        if args.no_show_editor:
            SHOW_EDITOR = False
        print("Show editor = %d" % SHOW_EDITOR)
        PRECISION = args.precision
        if args.preamble is not None:
            PREAMBLE = args.preamble.replace("\\n", "\n")
        if args.postamble is not None:
            POSTAMBLE = args.postamble.replace("\\n", "\n")
        if args.inches:
            UNITS = "G20"
            UNIT_SPEED_FORMAT = "in/min"
            UNIT_FORMAT = "in"
            PRECISION = 4
        if args.modal:
            MODAL = True
        if args.no_tlo:
            USE_TLO = False
        if args.axis_modal:
            print("here")
            OUTPUT_DOUBLES = False

    except Exception:
        return False

    return True


def export(objectslist, filename, argstring):
    if not processArguments(argstring):
        return None
    global UNITS
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT

    for obj in objectslist:
        if not hasattr(obj, "Path"):
            print(
                "the object " + obj.Name + " is not a path. Please select only path and Compounds."
            )
            return None

    print("postprocessing...")
    gcode = ""

    # write header
    if OUTPUT_HEADER:
        gcode += linenumber() + "(Exported by FreeCAD)\n"
        gcode += linenumber() + "(Post Processor: " + __name__ + ")\n"
        gcode += linenumber() + "(Output Time:" + str(now) + ")\n"

    # Write the preamble
    if OUTPUT_COMMENTS:
        gcode += linenumber() + "(begin preamble)\n"
    for line in PREAMBLE.splitlines():
        gcode += linenumber() + line + "\n"
    gcode += linenumber() + UNITS + "\n"

    for obj in objectslist:

        # Skip inactive operations
        if not PathUtil.activeForOp(obj):
            continue

        # do the pre_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(begin operation: %s)\n" % obj.Label
            gcode += linenumber() + "(machine: %s, %s)\n" % (
                MACHINE_NAME,
                UNIT_SPEED_FORMAT,
            )
        for line in PRE_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # get coolant mode
        coolantMode = PathUtil.coolantModeForOp(obj)

        # turn coolant on if required
        if OUTPUT_COMMENTS:
            if not coolantMode == "None":
                gcode += linenumber() + "(Coolant On:" + coolantMode + ")\n"
        if coolantMode == "Flood":
            gcode += linenumber() + "M8" + "\n"
        if coolantMode == "Mist":
            gcode += linenumber() + "M7" + "\n"

        # process the operation gcode
        gcode += parse(obj)

        # do the post_op
        if OUTPUT_COMMENTS:
            gcode += linenumber() + "(finish operation: %s)\n" % obj.Label
        for line in POST_OPERATION.splitlines(True):
            gcode += linenumber() + line

        # turn coolant off if required
        if not coolantMode == "None":
            if OUTPUT_COMMENTS:
                gcode += linenumber() + "(Coolant Off:" + coolantMode + ")\n"
            gcode += linenumber() + "M9" + "\n"

    # do the post_amble
    if OUTPUT_COMMENTS:
        gcode += "(begin postamble)\n"
    for line in POSTAMBLE.splitlines():
        gcode += linenumber() + line + "\n"

    if FreeCAD.GuiUp and SHOW_EDITOR:
        dia = PostUtils.GCodeEditorDialog()
        dia.editor.setText(gcode)
        result = dia.exec_()
        if result:
            final = dia.editor.toPlainText()
        else:
            final = gcode
    else:
        final = gcode

    print("done postprocessing.")

    if not filename == "-":
        gfile = pyopen(filename, "w")
        gfile.write(final)
        gfile.close()

    return final


def linenumber():
    global LINENR
    if OUTPUT_LINE_NUMBERS is True:
        LINENR += 10
        return "N" + str(LINENR) + " "
    return ""


def parse(pathobj):
    global PRECISION
    global MODAL
    global OUTPUT_DOUBLES
    global UNIT_FORMAT
    global UNIT_SPEED_FORMAT

    out = ""
    lastcommand = None
    precision_string = "." + str(PRECISION) + "f"
    currLocation = {}  # keep track for no doubles
    lastFeedRate = None  # Track last feed rate to ensure F on every line
    spindleActive = False  # Track if spindle has been started in this operation
    lastG0Move = None  # Track last G0 move to suppress duplicates

    # the order of parameters
    # mach3_4 doesn't want K properties on XY plane  Arcs need work.
    params = [
        "X",
        "Y",
        "Z",
        "A",
        "B",
        "C",
        "I",
        "J",
        "F",
        "S",
        "T",
        "Q",
        "R",
        "L",
        "H",
        "D",
        "P",
    ]
    firstmove = Path.Command("G0", {"X": -1, "Y": -1, "Z": -1, "F": 0.0})
    currLocation.update(firstmove.Parameters)  # set First location Parameters

    if hasattr(pathobj, "Group"):  # We have a compound or project.
        # if OUTPUT_COMMENTS:
        #     out += linenumber() + "(compound: " + pathobj.Label + ")\n"
        for p in pathobj.Group:
            out += parse(p)
        return out
    else:  # parsing simple path

        # groups might contain non-path things like stock.
        if not hasattr(pathobj, "Path"):
            return out

        # if OUTPUT_COMMENTS:
        #     out += linenumber() + "(" + pathobj.Label + ")\n"

        adaptiveOp = False
        opHorizRapid = 0
        opVertRapid = 0
        
        # Check for ArcFeedRatePercent property (from CAM Extensions)
        arcFeedRatePercent = 100  # Default to 100% (no change)
        if hasattr(pathobj, "ArcFeedRatePercent"):
            arcFeedRatePercent = pathobj.ArcFeedRatePercent
            if OUTPUT_COMMENTS and arcFeedRatePercent != 100:
                out += linenumber() + "(Arc feed rate: {}%)\n".format(arcFeedRatePercent)

        if "Adaptive" in pathobj.Name:
            adaptiveOp = True
            if hasattr(pathobj, "ToolController"):
                if (
                    hasattr(pathobj.ToolController, "HorizRapid")
                    and pathobj.ToolController.HorizRapid > 0
                ):
                    opHorizRapid = Units.Quantity(
                        pathobj.ToolController.HorizRapid, FreeCAD.Units.Velocity
                    )
                else:
                    FreeCAD.Console.PrintWarning(
                        "Tool Controller Horizontal Rapid Values are unset" + "\n"
                    )

                if (
                    hasattr(pathobj.ToolController, "VertRapid")
                    and pathobj.ToolController.VertRapid > 0
                ):
                    opVertRapid = Units.Quantity(
                        pathobj.ToolController.VertRapid, FreeCAD.Units.Velocity
                    )
                else:
                    FreeCAD.Console.PrintWarning(
                        "Tool Controller Vertical Rapid Values are unset" + "\n"
                    )

        for c in PathUtils.getPathWithPlacement(pathobj).Commands:

            outstring = []
            command = c.Name

            if adaptiveOp and c.Name in ["G0", "G00"]:
                if opHorizRapid and opVertRapid:
                    command = "G1"
                else:
                    outstring.append("(Tool Controller Rapid Values are unset)" + "\n")

            outstring.append(command)

            # if modal: suppress the command if it is the same as the last one
            if MODAL is True:
                if command == lastcommand:
                    outstring.pop(0)

            if c.Name.startswith("(") and not OUTPUT_COMMENTS:  # command is a comment
                continue

            # Now add the remaining parameters in order
            for param in params:
                if param in c.Parameters:
                    if param == "F":
                        # Store the feed rate for later use
                        if c.Name not in ["G0", "G00"]:  # mach3_4 doesn't use rapid speeds
                            speed = Units.Quantity(c.Parameters["F"], FreeCAD.Units.Velocity)
                            if speed.getValueAs(UNIT_SPEED_FORMAT) > 0.0:
                                # Apply arc feed rate reduction for G2/G3 commands
                                if c.Name in ["G2", "G02", "G3", "G03"]:
                                    # Reduce feed rate by arcFeedRatePercent
                                    speedValue = speed.getValueAs(UNIT_SPEED_FORMAT) * (arcFeedRatePercent / 100.0)
                                    lastFeedRate = speed  # Store original for G1 moves
                                else:
                                    speedValue = speed.getValueAs(UNIT_SPEED_FORMAT)
                                    lastFeedRate = speed
                                    
                                outstring.append(
                                    param
                                    + format(
                                        float(speedValue),
                                        precision_string,
                                    )
                                )
                    elif param == "T":
                        outstring.append(param + str(int(c.Parameters["T"])))
                    elif param == "H":
                        outstring.append(param + str(int(c.Parameters["H"])))
                    elif param == "D":
                        outstring.append(param + str(int(c.Parameters["D"])))
                    elif param == "S":
                        outstring.append(param + str(int(c.Parameters["S"])))
                    else:
                        if (
                            (not OUTPUT_DOUBLES)
                            and (param in currLocation)
                            and (currLocation[param] == c.Parameters[param])
                        ):
                            continue
                        else:
                            pos = Units.Quantity(c.Parameters[param], FreeCAD.Units.Length)
                            outstring.append(
                                param + format(float(pos.getValueAs(UNIT_FORMAT)), precision_string)
                            )
            
            # Force feed rate on every feed move (G1, G2, G3) even if F wasn't in parameters
            if c.Name in ["G1", "G01", "G2", "G02", "G3", "G03"]:
                if "F" not in c.Parameters and lastFeedRate is not None:
                    # Apply arc feed rate reduction for G2/G3 commands
                    if c.Name in ["G2", "G02", "G3", "G03"]:
                        feedValue = lastFeedRate.getValueAs(UNIT_SPEED_FORMAT) * (arcFeedRatePercent / 100.0)
                    else:
                        feedValue = lastFeedRate.getValueAs(UNIT_SPEED_FORMAT)
                        
                    outstring.append(
                        "F"
                        + format(
                            float(feedValue),
                            precision_string,
                        )
                    )

            if adaptiveOp and c.Name in ["G0", "G00"]:
                if opHorizRapid and opVertRapid:
                    if "Z" not in c.Parameters:
                        outstring.append(
                            "F"
                            + format(
                                float(opHorizRapid.getValueAs(UNIT_SPEED_FORMAT)),
                                precision_string,
                            )
                        )
                    else:
                        outstring.append(
                            "F"
                            + format(
                                float(opVertRapid.getValueAs(UNIT_SPEED_FORMAT)),
                                precision_string,
                            )
                        )

            # store the latest command
            lastcommand = command
            currLocation.update(c.Parameters)

            # Check for Tool Change:
            if command == "M6":
                # stop the spindle
                out += linenumber() + "M5\n"
                spindleActive = False  # Reset spindle tracking on tool change
                for line in TOOL_CHANGE.splitlines(True):
                    out += linenumber() + line

                # add height offset
                if USE_TLO:
                    tool_height = "\nG43 H" + str(int(c.Parameters["T"]))
                    outstring.append(tool_height)
            
            # Check for Spindle Start (M3 or M4):
            if command in ["M3", "M03", "M4", "M04"] and not spindleActive:
                spindleActive = True
                # Output the spindle command first
                if len(outstring) >= 1:
                    if OUTPUT_LINE_NUMBERS:
                        outstring.insert(0, (linenumber()))
                    for w in outstring:
                        out += w + COMMAND_SPACE
                    out = out.strip() + "\n"
                # Add dwell for spindle ramp-up (10 seconds = 10000 milliseconds)
                out += linenumber() + "G4 P10000 \n"
                if OUTPUT_COMMENTS:
                    out += linenumber() + "(Spindle ramp-up dwell)\n"
                outstring = []  # Clear outstring since we already output it
                continue

            if command == "message":
                if OUTPUT_COMMENTS is False:
                    out = []
                else:
                    outstring.pop(0)  # remove the command

            # Suppress duplicate consecutive G0 moves (common at operation boundaries)
            if command in ["G0", "G00"]:
                currentG0Move = " ".join(outstring)
                if currentG0Move == lastG0Move:
                    continue  # Skip this duplicate G0 move
                lastG0Move = currentG0Move
            else:
                lastG0Move = None  # Reset if not a G0 move

            # prepend a line number and append a newline
            if len(outstring) >= 1:
                if OUTPUT_LINE_NUMBERS:
                    outstring.insert(0, (linenumber()))

                # append the line to the final output
                for w in outstring:
                    out += w + COMMAND_SPACE
                out = out.strip() + "\n"

        return out


# print(__name__ + " gcode postprocessor loaded.")

# ================================================================================
# MACH4 G-CODE AND M-CODE REFERENCE
# ================================================================================
#
# This reference covers the G-codes and M-codes used by this post processor
# for Mach4 CNC controllers.
#
# G-CODES (Preparatory Functions)
# --------------------------------------------------------------------------------
#
# MOTION COMMANDS:
#   G0 (G00)    Rapid positioning - Move at maximum speed (non-cutting)
#   G1 (G01)    Linear interpolation - Straight line feed move at specified F rate
#   G2 (G02)    Circular interpolation clockwise (CW) - Arc feed move
#   G3 (G03)    Circular interpolation counter-clockwise (CCW) - Arc feed move
#   G4          Dwell - Pause for specified time (P parameter in milliseconds for Mach4)
#
# PLANE SELECTION:
#   G17         XY plane selection (most common for 3-axis milling)
#   G18         XZ plane selection
#   G19         YZ plane selection
#
# UNITS:
#   G20         Inch units
#   G21         Metric (millimeter) units
#
# DISTANCE MODE:
#   G90         Absolute positioning - Coordinates relative to work zero
#   G91         Incremental positioning - Coordinates relative to current position
#   G91.1       Arc centers in absolute mode (IJK relative to work zero)
#
# FEED RATE MODE:
#   G93         Inverse time feed rate
#   G94         Feed per minute (in/min or mm/min) - Standard mode
#   G95         Feed per revolution
#
# CUTTER COMPENSATION:
#   G40         Cancel cutter radius compensation
#   G41         Cutter compensation left
#   G42         Cutter compensation right
#
# TOOL LENGTH OFFSET:
#   G43         Tool length offset (H parameter specifies offset number)
#   G49         Cancel tool length offset
#
# WORK COORDINATE SYSTEMS:
#   G54         Work coordinate system 1 (default)
#   G55         Work coordinate system 2
#   G56         Work coordinate system 3
#   G57         Work coordinate system 4
#   G58         Work coordinate system 5
#   G59         Work coordinate system 6
#
# RETURN TO HOME:
#   G28         Return to home position through reference point
#   G30         Return to secondary home position
#
# PATH CONTROL:
#   G61         Exact path mode (stop at each point)
#   G64         Continuous path mode / Path blending (smooth through corners)
#
# CANNED CYCLES:
#   G80         Cancel canned cycle
#   G81         Drilling cycle (simple)
#   G82         Spot drilling cycle (with dwell)
#   G83         Peck drilling cycle
#   G84         Tapping cycle
#   G85         Boring cycle
#   G98         Canned cycle initial level return
#   G99         Canned cycle R-point level return
#
# M-CODES (Miscellaneous Functions)
# --------------------------------------------------------------------------------
#
# PROGRAM CONTROL:
#   M0          Program stop (operator must restart)
#   M1          Optional stop (only stops if optional stop is enabled)
#   M2          Program end
#   M30         Program end and reset (rewind to start)
#
# SPINDLE CONTROL:
#   M3          Spindle on clockwise (CW) - Normal cutting direction
#   M4          Spindle on counter-clockwise (CCW)
#   M5          Spindle stop
#
# TOOL CHANGE:
#   M6          Tool change - Change to tool specified by T word
#
# COOLANT CONTROL:
#   M7          Mist coolant on
#   M8          Flood coolant on
#   M9          All coolant off
#
# SPECIAL PARAMETERS USED IN THIS POST
# --------------------------------------------------------------------------------
#
# COORDINATE PARAMETERS:
#   X, Y, Z     Linear axis positions
#   A, B, C     Rotary axis positions
#   I, J, K     Arc center offsets for G2/G3 commands
#   R           Arc radius (alternative to IJK)
#
# OTHER PARAMETERS:
#   F           Feed rate (in/min or mm/min in G94 mode)
#   S           Spindle speed (RPM)
#   T           Tool number
#   H           Tool length offset number (used with G43)
#   D           Tool diameter offset number (used with G41/G42)
#   P           Dwell time in milliseconds (G4) for Mach4, or other parameter
#   L           Loop count for canned cycles or subroutines
#   Q           Peck increment for G83
#
# NOTES FOR THIS POST PROCESSOR:
# --------------------------------------------------------------------------------
#
# 1. Arc Feed Rate Control:
#    - This post processor supports the ArcFeedRatePercent property
#    - Set on Profile operations to independently control arc (G2/G3) feed rates
#    - Linear moves (G1) use the operation's normal feed rate
#    - Arc moves use: feed_rate * (ArcFeedRatePercent / 100)
#
# 2. Spindle Ramp-Up:
#    - Automatic 10-second dwell (G4 P10000) after spindle start (M3/M4)
#    - P parameter is in milliseconds for Mach4 (10000 ms = 10 seconds)
#    - Ensures spindle reaches full speed before cutting begins
#    - Important for foam cutting and finishing operations
#
# 3. Path Blending (G64):
#    - Enabled in preamble for smooth continuous motion
#    - Reduces jerky motion at corners
#    - Maintains better surface finish
#
# 4. Safe Sequences:
#    - Preamble initializes machine to known state
#    - Postamble retracts Z before moving XY (safe)
#    - Returns machine to home position at end
#
# 5. Tool Changes:
#    - Spindle stopped (M5) before tool change
#    - Tool length offset (G43) applied after change if USE_TLO is enabled
#
# FOR MORE INFORMATION:
#   - Mach4 CNC Controller Documentation
#   - NIST RS274NGC G-code standard
#   - Machine tool manufacturer specifications
#
# ================================================================================
