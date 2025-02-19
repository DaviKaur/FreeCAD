#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__ = "Command Mechanical Job Control"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

import FreeCAD
from FemCommands import FemCommands

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore


class _CommandMechanicalJobControl(FemCommands):
    "the Fem JobControl command definition"
    def __init__(self):
        super(_CommandMechanicalJobControl, self).__init__()
        self.resources = {'Pixmap': 'fem-new-analysis',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Fem_JobControl", "Start calculation"),
                          'Accel': "S, C",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Fem_JobControl", "Dialog to start the calculation of the mechanical anlysis")}
        self.is_active = 'with_analysis'

    def Activated(self):
        import _JobControlTaskPanel
        taskd = _JobControlTaskPanel._JobControlTaskPanel(FemGui.getActiveAnalysis())
        #taskd.obj = vobj.Object
        taskd.update()
        FreeCADGui.Control.showDialog(taskd)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Fem_MechanicalJobControl', _CommandMechanicalJobControl())
