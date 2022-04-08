#!/usr/bin/env python3

from .components import Resistor, Capacitor, Inductor, VSource, ISource
from abc import ABC, abstractmethod
from .common import v_format, i_format, dv_format, di_format

#################################################################

# Top-Level Classes for Strategy Pattern #

class EqnStrStrategy(ABC):
    @abstractmethod
    def gen_eqn_from_branch(self, _b):
        pass
    def gen_eqns(self, branch_dicts, nodes):
        return [self.gen_eqn_from_branch(_b, nodes) for _b in branch_dicts] + self.gen_kcl_eqns(branch_dicts, nodes)
    def gen_kcl_eqns(self, branch_dicts, nodes):
        kcl_dict = dict(zip(nodes, [[]] * len(nodes)))
        for b in branch_dicts:
            if b["node_plus"] != "0":
                # TODO: Why does this syntax not work?
                # kcl_dict[b["node_plus"]].append("-({})".format(i_format(b["branch_idx"],  nodes)))
                l_plus  = len(kcl_dict[b["node_plus"]])
                other_l = [len(kcl_dict[n]) for n in kcl_dict.keys() if n != b["node_plus"]]
                kcl_dict[b["node_plus"]]  = kcl_dict[b["node_plus"]]  + ["-({})".format(i_format(b["branch_idx"],  nodes))]
                assert len(kcl_dict[b["node_plus"]])  == l_plus  + 1
                assert [len(kcl_dict[n]) for n in kcl_dict.keys() if n != b["node_plus"]] == other_l
            if b["node_minus"] != "0":
                l_minus = len(kcl_dict[b["node_minus"]])
                other_l = [len(kcl_dict[n]) for n in kcl_dict.keys() if n != b["node_minus"]]
                kcl_dict[b["node_minus"]] = kcl_dict[b["node_minus"]] + ["+({})".format(i_format(b["branch_idx"],  nodes))]
                assert len(kcl_dict[b["node_minus"]]) == l_minus + 1
                assert [len(kcl_dict[n]) for n in kcl_dict.keys() if n != b["node_minus"]] == other_l
        return ["".join(v) for v in kcl_dict.values()]

#################################################################

# Strategies #

class EqnStrOpPtStrategy(EqnStrStrategy):
    def __init__(self):
        pass
    def gen_eqn_from_branch(self, _b, _n):
        if   _b["component"] == Resistor:
            return "(({})-({}))-(({})*({}))".format(v_format(_b["node_plus"],  _n),
                                                    v_format(_b["node_minus"], _n),
                                                    i_format(_b["branch_idx"], _n),
                                                             _b["value"])
        elif _b["component"] == Capacitor:
            return "(({})-({}))".format(i_format(_b["branch_idx"], _n), 0.00)
        elif _b["component"] == Inductor:
            return "((({})-({}))-({}))".format(v_format(_b["node_plus"],  _n),
                                               v_format(_b["node_minus"], _n), 0.00)
        elif _b["component"] == VSource:
            return "((({})-({}))-({}))".format(v_format(_b["node_plus"],  _n),
                                               v_format(_b["node_minus"], _n),
                                                        _b["value"])
        elif _b["component"] == ISource:
            return "(({})-({}))".format(i_format(_b["branch_idx"], _n),
                                                 _b["value"])
        else:
            assert False

class EqnStrTransientStrategy(EqnStrStrategy):
    def __init__(self):
        pass
    def gen_eqn_from_branch(self, _b, _n):
        if   _b["component"] == Resistor:
            return "(({})-({}))-(({})*({}))".format(v_format(_b["node_plus"],  _n, trans=True),
                                                    v_format(_b["node_minus"], _n, trans=True),
                                                    i_format(_b["branch_idx"], _n, trans=True),
                                                             _b["value"])
        elif _b["component"] == Capacitor:
            if "ic" in _b.keys():
                # TODO: modify to support nonzero start times
                prefix = "((({})-({}))-({})) if t == 0.00 else ".format(v_format(_b["node_plus"], _n, trans=True),
                                                                        v_format(_b["node_minus"], _n, trans=True),
                                                                                 _b["ic"])
            else:
                prefix = ""
            return prefix + "((({})*dt)-(({})*(({})-({}))))".format(i_format(_b["branch_idx"],  _n, trans=True),
                                                                             _b["value"],
                                                                   dv_format(_b["node_plus"],  _n),
                                                                   dv_format(_b["node_minus"], _n))
        elif _b["component"] == Inductor:
            if "ic" in _b.keys():
                # TODO: modify to support nonzero start times
                prefix = "(({})-({})) if t == 0.00 else ".format(i_format(_b["branch_idx"], _n, trans=True),
                                                                          _b["ic"])
            else:
                prefix = ""
            return prefix + "(((({})-({}))*dt)-(({})*(({}))))".format(v_format(_b["node_plus"],   _n, trans=True),
                                                                      v_format(_b["node_minus"],  _n, trans=True),
                                                                               _b["value"],
                                                                     di_format(_b["branch_idx"], _n))
        elif _b["component"] == VSource:
            return "((({})-({}))-({}))".format(v_format(_b["node_plus"],  _n, trans=True),
                                               v_format(_b["node_minus"], _n, trans=True),
                                                        _b["value"])
        elif _b["component"] == ISource:
            return "(({})-({}))".format(i_format(_b["branch_idx"], _n, trans=True),
                                                 _b["value"])
        else:
            assert False

def gen_eqns_top(parse_dict):
    # TODO need to support multiple test types?
    # TODO disable ic if uic arg is not provided to trans
    # TODO wrap logic in a context type
    if   parse_dict["ctrl"][0]["test_type"] == "op_pt":
        return EqnStrOpPtStrategy().gen_eqns(parse_dict["branches"], parse_dict["nodes"])
    elif parse_dict["ctrl"][0]["test_type"] == "tran" :
        return EqnStrTransientStrategy().gen_eqns(parse_dict["branches"], parse_dict["nodes"])
    else:
        assert False

#################################################################

if __name__ == "__main__":
    import netlist
    # with open("op_pt.cir", "r") as f:
    #     print(gen_eqns_top(netlist.parse(f.read())))
    # with open("tran.cir", "r") as f:
    #     print(gen_eqns_top(netlist.parse(f.read())))
    with open("op_pt_divider.cir", "r") as f:
        txt = f.read()
        print(gen_eqns_top(netlist.parse(txt)))
