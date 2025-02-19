#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013 - Joachim Zettler                                  *
#*   Copyright (c) 2013 - Juergen Riegel <FreeCAD@juergen-riegel.net>      *
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


import FreeCAD
import os
from math import pow, sqrt

__title__ = "FreeCAD Calculix library"
__author__ = "Juergen Riegel "
__url__ = "http://www.freecadweb.org"

if open.__module__ == '__builtin__':
    pyopen = open  # because we'll redefine open below


# read a calculix result file and extract the nodes, displacement vectores and stress values.
def readResult(frd_input):
    frd_file = pyopen(frd_input, "r")
    nodes = {}
    elements = {}
    results = []
    mode_results = {}
    mode_disp = {}
    mode_stress = {}

    mode_disp_found = False
    nodes_found = False
    mode_stress_found = False
    elements_found = False
    eigenmode = 0
    elem = -1
    elemType = 0

    for line in frd_file:
        #Check if we found nodes section
        if line[4:6] == "2C":
            nodes_found = True
        #first lets extract the node and coordinate information from the results file
        if nodes_found and (line[1:3] == "-1"):
            elem = int(line[4:13])
            nodes_x = float(line[13:25])
            nodes_y = float(line[25:37])
            nodes_z = float(line[37:49])
            nodes[elem] = FreeCAD.Vector(nodes_x, nodes_y, nodes_z)
        #Check if we found nodes section
        if line[4:6] == "3C":
            elements_found = True
        #first lets extract element number
        if elements_found and (line[1:3] == "-1"):
            elem = int(line[4:13])
            elemType = int(line[14:18])
        #then the 10 id's for the Tet10 element
        if elements_found and (line[1:3] == "-2") and elemType == 6:
            node_id_2 = int(line[3:13])
            node_id_1 = int(line[13:23])
            node_id_3 = int(line[23:33])
            node_id_4 = int(line[33:43])
            node_id_5 = int(line[43:53])
            node_id_7 = int(line[53:63])
            node_id_6 = int(line[63:73])
            node_id_9 = int(line[73:83])
            node_id_8 = int(line[83:93])
            node_id_10 = int(line[93:103])
            elements[elem] = (node_id_1, node_id_2, node_id_3, node_id_4, node_id_5, node_id_6, node_id_7, node_id_8, node_id_9, node_id_10)
        #Check if we found new eigenmode
        if line[5:10] == "PMODE":
            eigenmode = int(line[30:36])
        #Check if we found displacement section
        if line[5:9] == "DISP":
            mode_disp_found = True
        #we found a displacement line in the frd file
        if mode_disp_found and (line[1:3] == "-1"):
            elem = int(line[4:13])
            mode_disp_x = float(line[13:25])
            mode_disp_y = float(line[25:37])
            mode_disp_z = float(line[37:49])
            mode_disp[elem] = FreeCAD.Vector(mode_disp_x, mode_disp_y, mode_disp_z)
        if line[5:11] == "STRESS":
            mode_stress_found = True
        #we found a displacement line in the frd file
        if mode_stress_found and (line[1:3] == "-1"):
            elem = int(line[4:13])
            stress_1 = float(line[13:25])
            stress_2 = float(line[25:37])
            stress_3 = float(line[37:49])
            stress_4 = float(line[49:61])
            stress_5 = float(line[61:73])
            stress_6 = float(line[73:85])
            mode_stress[elem] = (stress_1, stress_2, stress_3, stress_4, stress_5, stress_6)
        #Check for the end of a section
        if line[1:3] == "-3":
            if mode_disp_found:
                mode_disp_found = False

            if mode_stress_found:
                mode_stress_found = False

            if mode_disp and mode_stress:
                mode_results = {}
                mode_results['number'] = eigenmode
                mode_results['disp'] = mode_disp
                mode_results['stress'] = mode_stress
                results.append(mode_results)
                mode_disp = {}
                mode_stress = {}
                eigenmode = 0
            nodes_found = False
            elements_found = False

    frd_file.close()
    return {'Nodes': nodes, 'Tet10Elem': elements, 'Results': results}


def calculate_von_mises(i):
    # Von mises stress (http://en.wikipedia.org/wiki/Von_Mises_yield_criterion)
    s11 = i[0]
    s22 = i[1]
    s33 = i[2]
    s12 = i[3]
    s23 = i[4]
    s31 = i[5]
    s11s22 = pow(s11 - s22, 2)
    s22s33 = pow(s22 - s33, 2)
    s33s11 = pow(s33 - s11, 2)
    s12s23s31 = 6 * (pow(s12, 2) + pow(s23, 2) * pow(s31, 2))
    vm_stress = sqrt(0.5 * (s11s22 + s22s33 + s33s11 + s12s23s31))
    return vm_stress


def importFrd(filename, Analysis=None):
    m = readResult(filename)
    MeshObject = None
    if(len(m['Nodes']) > 0):
        import Fem
        if Analysis is None:
            AnalysisName = os.path.splitext(os.path.basename(filename))[0]
            AnalysisObject = FreeCAD.ActiveDocument.addObject('Fem::FemAnalysis', 'Analysis')
            AnalysisObject.Label = AnalysisName
        else:
            AnalysisObject = Analysis

        if 'Nodes' in m:
            positions = []
            for k, v in m['Nodes'].iteritems():
                positions.append(v)
            p_x_max, p_y_max, p_z_max = map(max, zip(*positions))
            p_x_min, p_y_min, p_z_min = map(min, zip(*positions))

            x_span = abs(p_x_max - p_x_min)
            y_span = abs(p_y_max - p_y_min)
            z_span = abs(p_z_max - p_z_min)
            span = max(x_span, y_span, z_span)

        if ('Tet10Elem' in m) and ('Nodes' in m) and (not Analysis):
            mesh = Fem.FemMesh()
            nds = m['Nodes']

            for i in nds:
                n = nds[i]
                mesh.addNode(n[0], n[1], n[2], i)
            elms = m['Tet10Elem']
            for i in elms:
                e = elms[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9]], i)
            if len(nds) > 0:
                MeshObject = FreeCAD.ActiveDocument.addObject('Fem::FemMeshObject', 'ResultMesh')
                MeshObject.FemMesh = mesh
                AnalysisObject.Member = AnalysisObject.Member + [MeshObject]

        for result_set in m['Results']:
            eigenmode_number = result_set['number']
            if eigenmode_number > 0:
                results_name = 'Mode_' + str(eigenmode_number) + '_results'
            else:
                results_name = 'Results'
            results = FreeCAD.ActiveDocument.addObject('Fem::FemResultObject', results_name)

            disp = result_set['disp']
            l = len(disp)
            displacement = []
            for k, v in disp.iteritems():
                displacement.append(v)

            x_max, y_max, z_max = map(max, zip(*displacement))
            if eigenmode_number > 0:
                max_disp = max(x_max, y_max, z_max)
                # Allow for max displacement to be 0.1% of the span
                # FIXME - add to Preferences
                max_allowed_disp = 0.001 * span
                scale = max_allowed_disp / max_disp
            else:
                scale = 1.0

            if len(disp) > 0:
                results.DisplacementVectors = map((lambda x: x * scale), disp.values())
                results.ElementNumbers = disp.keys()
                if(MeshObject):
                    results.Mesh = MeshObject

            stress = result_set['stress']
            if len(stress) > 0:
                mstress = []
                for i in stress.values():
                    mstress.append(calculate_von_mises(i))
                if eigenmode_number > 0:
                    results.StressValues = map((lambda x: x * scale), mstress)
                else:
                    results.StressValues = mstress

            if (results.ElementNumbers != 0 and results.ElementNumbers != stress.keys()):
                print ("Inconsistent FEM results: element number for Stress doesn't equal element number for Displacement {} != {}"
                       .format(results.ElementNumbers, len(results.StressValues)))
                results.ElementNumbers = stress.keys()

            x_min, y_min, z_min = map(min, zip(*displacement))
            sum_list = map(sum, zip(*displacement))
            x_avg, y_avg, z_avg = [i / l for i in sum_list]

            s_max = max(results.StressValues)
            s_min = min(results.StressValues)
            s_avg = sum(results.StressValues) / l

            disp_abs = []
            for d in displacement:
                disp_abs.append(sqrt(pow(d[0], 2) + pow(d[1], 2) + pow(d[2], 2)))
            results.DisplacementLengths = disp_abs

            a_max = max(disp_abs)
            a_min = min(disp_abs)
            a_avg = sum(disp_abs) / l

            results.Stats = [x_min, x_avg, x_max,
                             y_min, y_avg, y_max,
                             z_min, z_avg, z_max,
                             a_min, a_avg, a_max,
                             s_min, s_avg, s_max]
            AnalysisObject.Member = AnalysisObject.Member + [results]

        if(FreeCAD.GuiUp):
            import FemGui
            FemGui.setActiveAnalysis(AnalysisObject)


def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc

    importFrd(filename)


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)
