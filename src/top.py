# SPDX-License-Identifier: Apache-2.0
from typing import cast

from pdkmaster import technology as _tch
from pdkmaster.technology import geometry as _geo
from pdkmaster import design as _dsgn

from c4m.pdk import sky130
prims = sky130.tech.primitives

from template import TTTemplate1X1


name = "tt_um_c4m_spsram_direct"

class Top(TTTemplate1X1):
    def __init__(self, *, fab: _dsgn.CellFactory):
        super().__init__(name=name, fab=fab)

    def _create_circuit_(self):
        super()._create_circuit_()

        ckt = self.circuit
        nets = ckt.nets

        memfab = sky130.SPSRAMFactory(thin_layout=False, lib=self.fab.lib)
        mem_cell = memfab.block(words=128, word_size=8, we_size=1, cell_name="SRAM128x8")

        mem = ckt.instantiate(mem_cell, name="mem")

        nets["VGND"].childports += mem.ports["vss"]
        nets["VDPWR"].childports += mem.ports["vdd"]

        nets["clk"].childports += mem.ports["clk"]

        for bit in range(7):
            pin_net = f"ui_in[{bit}]"
            mem_net = f"a[{bit}]"

            nets[pin_net].childports += mem.ports[mem_net]

        nets["ui_in[7]"].childports += mem.ports["we[0]"]

        for bit in range(8):
            pin_net = f"uo_out[{bit}]"
            mem_net = f"q[{bit}]"

            nets[pin_net].childports += mem.ports[mem_net]

            pin_net = f"uio_in[{bit}]"
            mem_net = f"d[{bit}]"

            nets[pin_net].childports += mem.ports[mem_net]

            with open(f"verilog/{mem_cell.name}.v", "w") as f:
                f.write(mem_cell.verilog())

    def _create_layout_(self):
        super()._create_layout_()

        m1 = cast(_tch.MetalWire, prims["m1"])
        via = cast(_tch.Via, prims["via"])
        m2 = cast(_tch.MetalWire, prims["m2"])
        via2 = cast(_tch.Via, prims["via2"])
        m3 = cast(_tch.MetalWire, prims["m3"])
        via3 = cast(_tch.Via, prims["via3"])
        m4 = cast(_tch.MetalWire, prims["m4"])

        ckt = self.circuit
        nets = ckt.nets

        vss = nets["VGND"]
        vdd = nets["VDPWR"]

        c2l = self.c2l

        bnd = self.layout.boundary

        # Place memory instance
        mem_d = c2l.instlayout_data["mem"]

        mem_d.rotate(rotation=_geo.Rotation.MY90)
        mem_d.align(
            _dsgn.C2LFixLeft(prim=None, value=10.0),
            _dsgn.C2LFixBottom(prim=None, value=2.0),
        )

        m3_pitch = sky130.tech.computed.min_pitch(primitive=m3)

        # Connect clk
        net = nets["clk"]

        via1_d = c2l.new_wire(
            net=net, wire=via, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
            align=(
                _dsgn.C2LAbutOnRight(prim=m1, data=mem_d, data_pin=True),
                _dsgn.C2LAlignTop(prim=m1, data=mem_d, data_pin=True),
            )
        )
        via2_d = c2l.new_wire(
            net=net, wire=via2, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
            align=(
                _dsgn.C2LAlignLeft(prim=m2, data=via1_d),
                _dsgn.C2LAlignTop(prim=m2, data=via1_d),
            ),
        )
        via3_d = c2l.new_wire(
            net=net, wire=via3, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
            align=(
                _dsgn.C2LAlignLeft(prim=m3, data=via2_d),
                _dsgn.C2LAlignTop(prim=m3, data=via2_d),
            )
        )

        bb = c2l.bounds(prim=m4, pin=True, net=net)
        c2l.new_multipath(
            _geo.Start(edge=_geo.Line(
                point1=_geo.Point(x=bb.left, y=bb.bottom),
                point2=_geo.Point(x=bb.right, y=bb.bottom),
            )),
            _dsgn.MPGoToVH(data=via3_d),
            prim=m4, net=net,
        )

        # Connect a
        for bit in range(7):
            net = nets[f"ui_in[{bit}]"]

            via2_d = c2l.new_wire(
                net=net, wire=via2, wire_params=dict(rows=2, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LAlignCenterX(prim=m2, data=mem_d, data_pin=True),
                    _dsgn.C2LAlignTop(prim=m2, data=mem_d, data_pin=True),
                )
            )

            bb = c2l.bounds(prim=m4, pin=True, net=net)
            via3_d = c2l.new_wire(
                net=net, wire=via3, wire_params=dict(rows=2, bottom_enclosure="tall", top_enclosure="tall"),
                origin=_geo.Point(x=bb.center.x, y=bb.bottom),
            )

            c2l.new_multipath(
                _dsgn.MPStart(data=via2_d, position="top", width=m3.min_width),
                _geo.GoUp(0.5*m3.min_width + bit*m3_pitch),
                _dsgn.MPGoToHV(data=via3_d),
                prim=m3, net=net,
            )

        # Connect we
        net = nets["ui_in[7]"]

        via2_d = c2l.new_wire(
            net=net, wire=via2, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
            align=(
                _dsgn.C2LAlignRight(prim=m2, data=mem_d, data_pin=True),
                _dsgn.C2LAbutOnTop(prim=m2, data=mem_d, data_pin=True),
            )
        )
        via3_d = c2l.new_wire(
            net=net, wire=via3, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
            align=(
                _dsgn.C2LAlignLeft(prim=m3, data=via2_d),
                _dsgn.C2LAlignTop(prim=m3, data=via2_d),
            )
        )

        bb = c2l.bounds(prim=m4, pin=True, net=net)
        c2l.new_multipath(
            _geo.Start(edge=_geo.Line(
                point1=_geo.Point(x=bb.left, y=bb.bottom),
                point2=_geo.Point(x=bb.right, y=bb.bottom),
            )),
            _dsgn.MPGoToVH(data=via3_d),
            prim=m4, net=net,
        )

        for bit in range(8):
            # Connect d
            net = nets[f"uio_in[{bit}]"]
            
            via2_d = c2l.new_wire(
                net=net, wire=via2, wire_params=dict(columns=2, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LAlignLeft(prim=m2, data=mem_d, data_pin=True),
                    _dsgn.C2LAbutOnBottom(prim=m2, data=mem_d, data_pin=True),
                )
            )

            bb = c2l.bounds(prim=m4, pin=True, net=net)
            via3_d = c2l.new_wire(
                net=net, wire=via3, wire_params=dict(rows=2, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LFixX(bb.center.x),
                    _dsgn.C2LAlignBottom(prim=m3, data=via2_d),
                ),
            )

            via2_d.extend_bb(prim=m3, left=via3_d)
            via3_d.extend_bb(prim=m4, top=bnd.top)

            # Connect q
            net = nets[f"uo_out[{bit}]"]
            
            via2_d = c2l.new_wire(
                net=net, wire=via2, wire_params=dict(columns=2, bottom_enclosure="wide", top_enclosure="wide"),
                align=(
                    _dsgn.C2LAlignLeft(prim=m2, data=mem_d, data_pin=True),
                    _dsgn.C2LAlignBottom(prim=m2, data=mem_d, data_pin=True),
                )
            )

            bb = c2l.bounds(prim=m4, pin=True, net=net)
            via3_d = c2l.new_wire(
                net=net, wire=via3, wire_params=dict(rows=2, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LFixX(bb.center.x),
                    _dsgn.C2LAlignBottom(prim=m3, data=via2_d),
                ),
            )

            via2_d.extend_bb(prim=m3, left=via3_d)
            via3_d.extend_bb(prim=m4, top=bnd.top)

        w = 11.0
        s = 0.4

        bottom = 2.0
        top = bnd.top - 2.0

        left = mem_d.left
        right = left + w
        vddm4pin_shape = _geo.Rect(left=left, bottom=bottom, right=right, top=top)
        c2l.new_wire(net=vdd, wire=m4, pin=True, shape=vddm4pin_shape)

        left = right + s
        right = left + w
        vssm4pin_shape = _geo.Rect(left=left, bottom=bottom, right=right, top=top)
        vssm4pin_d = c2l.new_wire(net=vss, wire=m4, pin=True, shape=vssm4pin_shape)

        lrs = set(
            _geo.leftright(left=shape.bounds.left, right=shape.bounds.right)
            for shape in filter(
                lambda s: s.bounds.bottom < (2.0 + _geo.epsilon),
                mem_d.filter_shapes(prim=m2, pin=True, depth=1, net=vss, split=True),
            )
        )
        for lr in lrs:
            via2_d = c2l.new_wire(
                net=vss, wire=via2, wire_params=dict(rows=4, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LFixX(lr.mid),
                    _dsgn.C2LFixBottom(prim=m3, value=2.0),
                ),
            )
        left = min(lr.left for lr in lrs)
        right = max(lr.right for lr in lrs)
        via2_d.extend_bb(prim=m3, left=left, right=right)

        bb = via2_d.bounds(prim=m3)
        c2l.new_wire(
            net=vss, wire=via3, wire_params=dict(
                bottom_width=vssm4pin_shape.width, bottom_height=bb.height,
                top_width=vssm4pin_shape.width, top_height=bb.height,
            ), origin=_geo.Point(x=vssm4pin_shape.center.x, y=bb.center.y),
        )

        d_align = via2_d

        w = d_align.bounds(prim=m3).height

        lrs = set(
            _geo.leftright(left=shape.bounds.left, right=shape.bounds.right)
            for shape in filter(
                lambda s: s.bounds.bottom < (2.0 + _geo.epsilon),
                mem_d.filter_shapes(prim=m2, pin=True, depth=1, net=vdd, split=True),
            )
        )
        s = sky130.tech.computed.min_space(primitive1=m3, width=w)
        for lr in lrs:
            via2_d = c2l.new_wire(
                net=vdd, wire=via2, wire_params=dict(rows=4, bottom_enclosure="tall", top_enclosure="tall"),
                align=(
                    _dsgn.C2LFixX(lr.mid),
                    _dsgn.C2LMinSpaceOnBottom(prim=m3, ref_data=d_align, space=s),
                ),
            )
        left = min(lr.left for lr in lrs)
        right = max(lr.right for lr in lrs)
        via2_d.extend_bb(prim=m3, left=left, right=right)

        bb = via2_d.bounds(prim=m3)
        c2l.new_wire(
            net=vdd, wire=via3, wire_params=dict(
                bottom_width=vddm4pin_shape.width, bottom_height=bb.height,
                top_width=vddm4pin_shape.width, top_height=bb.height,
            ), origin=_geo.Point(x=vddm4pin_shape.center.x, y=bb.center.y),
        )

        # uio_oe and uio_out are shorted to VGND
        gnd_net_names = (
            *(f"uio_out[{bit}]" for bit in range(8)),
            *(f"uio_oe[{bit}]" for bit in range(8)),
        )

        d_first = d_last = None
        for n, net_name in enumerate(gnd_net_names):
            net = nets[net_name]

            bb = c2l.bounds(prim=m4, pin=True, net=net)
            via3_d = c2l.new_wire(
                net=vss, wire=via3, wire_params=dict(rows=2, bottom_enclosure="tall", top_enclosure="tall"),
                origin=_geo.Point(x=bb.center.x, y=bb.bottom),
            )

            if n == 0:
                d_first = via3_d
            d_last = via3_d
        assert d_first is not None
        assert d_last is not None

        d_first.extend_bb(prim=m3, left=d_last)

        via3_d = c2l.new_wire(
            net=vss, wire=via3, wire_params=dict(
                rows=4, columns=4, bottom_enclosure="tall", top_enclosure="tall",
            ), align=(
                _dsgn.C2LAlignLeft(prim=m3, data=d_last),
                _dsgn.C2LAlignTop(prim=m4, data=vssm4pin_d),
            ),
        )
        via3_d.extend_bb(prim=m3, top=d_last)

