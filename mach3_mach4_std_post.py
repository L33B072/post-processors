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
OUTPUT_DOUBLES = False  # if false duplicate axis values are suppressed if the same as previous line.
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
PREAMBLE = """G17 G54 G40 G49 G80 G90 G64
"""

# Postamble text will appear following the last operation.
POSTAMBLE = """M05
G17 G54 G90 G80 G40
M2
"""

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
    lastStoredFeedRate = None  # Track last feed rate from parameters
    lastOutputFeedRate = None  # Track last feedrate actually output (for modal output)
    spindleActive = False  # Track if spindle has been started in this operation
    lastG0Move = None  # Track last G0 move to suppress duplicates
    
    # Track initial G0 moves to reorder them (XY before Z)
    initialG0Buffer = []
    commandCount = 0
    MAX_INITIAL_G0_COMMANDS = 5  # Only reorder the first few G0 commands

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
            commandCount += 1

            outstring = []
            command = c.Name
            
            # Buffer initial G0 moves to reorder them (XY before Z)
            if command in ["G0", "G00"] and commandCount <= MAX_INITIAL_G0_COMMANDS and not adaptiveOp:
                # Store this G0 command for potential reordering
                initialG0Buffer.append(c)
                continue  # Don't process yet, wait to collect all initial G0s
            
            # If we've moved past the initial G0 sequence, flush the buffer with reordering
            if initialG0Buffer and (command not in ["G0", "G00"] or commandCount > MAX_INITIAL_G0_COMMANDS):
                # Separate G0 moves into XY moves and Z-only moves
                xyMoves = []
                zMoves = []
                
                for g0cmd in initialG0Buffer:
                    hasXY = "X" in g0cmd.Parameters or "Y" in g0cmd.Parameters
                    hasZ = "Z" in g0cmd.Parameters
                    hasOnlyZ = hasZ and not hasXY
                    
                    if hasOnlyZ:
                        zMoves.append(g0cmd)
                    else:
                        xyMoves.append(g0cmd)
                
                # Output in order: XY moves first, then Z moves
                for g0cmd in xyMoves + zMoves:
                    bufferedOut = []
                    bufferedOut.append(g0cmd.Name)
                    
                    # Add parameters in order
                    for param in params:
                        if param in g0cmd.Parameters:
                            if param == "F" and g0cmd.Name in ["G0", "G00"]:
                                continue  # mach3_4 doesn't use rapid speeds
                            if param in ["X", "Y", "Z", "A", "B", "C", "I", "J"]:
                                if (
                                    (not OUTPUT_DOUBLES)
                                    and (param in currLocation)
                                    and (currLocation[param] == g0cmd.Parameters[param])
                                ):
                                    continue
                                pos = Units.Quantity(g0cmd.Parameters[param], FreeCAD.Units.Length)
                                bufferedOut.append(
                                    param + format(float(pos.getValueAs(UNIT_FORMAT)), precision_string)
                                )
                    
                    # Update current location
                    currLocation.update(g0cmd.Parameters)
                    
                    # Output the buffered G0 move
                    if len(bufferedOut) >= 1:
                        if OUTPUT_LINE_NUMBERS:
                            bufferedOut.insert(0, (linenumber()))
                        for w in bufferedOut:
                            out += w + COMMAND_SPACE
                        out = out.strip() + "\n"
                
                # Clear the buffer
                initialG0Buffer = []

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
                                    lastStoredFeedRate = speed  # Store original for G1 moves
                                else:
                                    speedValue = speed.getValueAs(UNIT_SPEED_FORMAT)
                                    lastStoredFeedRate = speed
                                
                                # Only output F if it's different from the last output feedrate (modal)
                                if lastOutputFeedRate is None or abs(speedValue - lastOutputFeedRate) > 0.001:
                                    outstring.append(
                                        param
                                        + format(
                                            float(speedValue),
                                            precision_string,
                                        )
                                    )
                                    lastOutputFeedRate = speedValue
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
            
            # Add feed rate on feed moves if not in parameters (inherit from last move)
            if c.Name in ["G1", "G01", "G2", "G02", "G3", "G03"]:
                if "F" not in c.Parameters and lastStoredFeedRate is not None:
                    # Apply arc feed rate reduction for G2/G3 commands
                    if c.Name in ["G2", "G02", "G3", "G03"]:
                        feedValue = lastStoredFeedRate.getValueAs(UNIT_SPEED_FORMAT) * (arcFeedRatePercent / 100.0)
                    else:
                        feedValue = lastStoredFeedRate.getValueAs(UNIT_SPEED_FORMAT)
                    
                    # Only output F if it's different from the last output feedrate (modal)
                    if lastOutputFeedRate is None or abs(feedValue - lastOutputFeedRate) > 0.001:
                        outstring.append(
                            "F"
                            + format(
                                float(feedValue),
                                precision_string,
                            )
                        )
                        lastOutputFeedRate = feedValue

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
                # Add dwell for spindle ramp-up (20 seconds)
                out += linenumber() + "G4 P20.0\n"
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
            
            # Skip G0/G00 commands with no coordinates (can happen with modal output)
            if command in ["G0", "G00"] and len(outstring) == 1:
                # Only has the command itself, no coordinates - skip it
                continue

            # prepend a line number and append a newline
            if len(outstring) >= 1:
                if OUTPUT_LINE_NUMBERS:
                    outstring.insert(0, (linenumber()))

                # append the line to the final output
                for w in outstring:
                    out += w + COMMAND_SPACE
                out = out.strip() + "\n"
        
        # Flush any remaining buffered G0 commands at end of operation
        if initialG0Buffer:
            # Separate G0 moves into XY moves and Z-only moves
            xyMoves = []
            zMoves = []
            
            for g0cmd in initialG0Buffer:
                hasXY = "X" in g0cmd.Parameters or "Y" in g0cmd.Parameters
                hasZ = "Z" in g0cmd.Parameters
                hasOnlyZ = hasZ and not hasXY
                
                if hasOnlyZ:
                    zMoves.append(g0cmd)
                else:
                    xyMoves.append(g0cmd)
            
            # Output in order: XY moves first, then Z moves
            for g0cmd in xyMoves + zMoves:
                bufferedOut = []
                bufferedOut.append(g0cmd.Name)
                
                # Add parameters in order
                for param in params:
                    if param in g0cmd.Parameters:
                        if param == "F" and g0cmd.Name in ["G0", "G00"]:
                            continue  # mach3_4 doesn't use rapid speeds
                        if param in ["X", "Y", "Z", "A", "B", "C", "I", "J"]:
                            if (
                                (not OUTPUT_DOUBLES)
                                and (param in currLocation)
                                and (currLocation[param] == g0cmd.Parameters[param])
                            ):
                                continue
                            pos = Units.Quantity(g0cmd.Parameters[param], FreeCAD.Units.Length)
                            bufferedOut.append(
                                param + format(float(pos.getValueAs(UNIT_FORMAT)), precision_string)
                            )
                
                # Update current location
                currLocation.update(g0cmd.Parameters)
                
                # Output the buffered G0 move
                if len(bufferedOut) >= 1:
                    if OUTPUT_LINE_NUMBERS:
                        bufferedOut.insert(0, (linenumber()))
                    for w in bufferedOut:
                        out += w + COMMAND_SPACE
                    out = out.strip() + "\n"

        return out


# print(__name__ + " gcode postprocessor loaded.")
