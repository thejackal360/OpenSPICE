#!/usr/bin/env python3

from arpeggio import ZeroOrMore, EOF, ParserPython
from arpeggio import RegExMatch
import numpy
import sys

# https://pypi.org/project/Arpeggio/1.0/

### Parsing Functions ###

def root():
    return ZeroOrMore(element), EOF

# TODO: check
def element():
    return el, node, node, val, RegExMatch(r';')

def el():
    return RegExMatch(r'(R\d+)|(V\d+)')

# Only # names
def node():
    return RegExMatch(r'\d+')

# TODO: check
def val():
    return RegExMatch(r'\d*\.\d*|\d+')

### Matrix Construction Functions ###

def get_nodes(ptree):
    nodes = []
    for l in ptree:
        if str(l) != "":
            l = str(l).replace("|", "").split()
            if int(l[1]) not in nodes and int(l[1]) != 0:
                nodes.append(int(l[1]))
            if int(l[2]) not in nodes and int(l[2]) != 0:
                nodes.append(int(l[2]))
    nodes.sort()
    # Don't allow user to skip node numbers
    for i in range(len(nodes)-1):
        assert nodes[i+1] - nodes[i] == 1
    # Don't allow user to start past node 1
    assert nodes[0] == 1
    return nodes

def get_ind_v_srcs(ptree):
    ind_v_srcs = []
    for l in ptree:
        if str(l) != "":
            l = str(l).replace("|", "").split()
            if l[0][0] == "V":
                ind_v_srcs.append(int(l[0][1:]))
    ind_v_srcs.sort()
    for i in range(len(ind_v_srcs)-1):
        assert ind_v_srcs[i+1] - ind_v_srcs[i] == 1
    assert ind_v_srcs[0] == 1
    return ind_v_srcs

if __name__ == "__main__":
    parser = ParserPython(root)
    with open(sys.argv[1], "r") as f:
        parse_tree = parser.parse(f.read())
        nodes = get_nodes(parse_tree)
        ind_v_srcs = get_ind_v_srcs(parse_tree)
        A_matrix = numpy.zeros([len(nodes) + len(ind_v_srcs), len(nodes) + len(ind_v_srcs)])
        z_vector = numpy.zeros([len(nodes) + len(ind_v_srcs), 1])
        for r in parse_tree:
            _r = str(r).replace("|", "").split()
            if _r != [] and _r[0][0] == "R":
                if int(_r[1]) != 0 and int(_r[2]) != 0:
                    A_matrix[int(_r[1]) - 1][int(_r[2]) - 1] = -1.00 / float(_r[3])
                    A_matrix[int(_r[2]) - 1][int(_r[1]) - 1] = -1.00 / float(_r[3])
                if int(_r[1]) != 0:
                    A_matrix[int(_r[1]) - 1][int(_r[1]) - 1] += 1.00 / float(_r[3])
                if int(_r[2]) != 0:
                    A_matrix[int(_r[2]) - 1][int(_r[2]) - 1] += 1.00 / float(_r[3])
            elif _r != [] and _r[0][0] == "V":
                if int(_r[1]) != 0:
                    A_matrix[len(nodes) + int(_r[0][1:]) - 1][int(_r[1]) - 1] = 1.00
                    A_matrix[int(_r[1]) - 1][len(nodes) + int(_r[0][1:]) - 1] = 1.00
                if int(_r[2]) != 0:
                    A_matrix[len(nodes) + int(_r[0][1:]) - 1][int(_r[2]) - 1] = -1.00
                    A_matrix[int(_r[2]) - 1][len(nodes) + int(_r[0][1:]) - 1] = -1.00
                z_vector[len(nodes) + int(_r[0][1:]) - 1][0] = float(_r[3])
        soln = numpy.dot(numpy.linalg.inv(A_matrix), z_vector)
        for i in range(len(nodes)):
            print("Node {}: {} [V]".format(i, soln[i][0]))
