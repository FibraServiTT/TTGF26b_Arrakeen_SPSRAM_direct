#!/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from pdkmaster.io.klayout import merge, export2db

from c4m.pdk import gf180mcu
prims = gf180mcu.tech.primitives

import pya
pya: Any

#
# Generate the block in a library
#
print("Generating block")

prefix = "SP6T"
cell_name = "SRAM128x8"

lib = gf180mcu.Library(name=f"{prefix}{cell_name}")
memfab = gf180mcu.SPSRAMFactory(lib=lib, name_prefix=prefix)
mem_cell = memfab.block(words=128, word_size=8, we_size=1, cell_name=cell_name)

# Be sure layout has been generated
mem_cell.layout
# Merge shapes
merge(lib)

#
# Export to GDS
#
print("Exporting GDS file")

# Export to klayout
kldb = export2db(
    mem_cell, gds_layers=gf180mcu.gds_layers,
    add_pin_label=True,
)

# Post-process file for npc layer etc
sp = pya.ShapeProcessor()
OR = pya.EdgeProcessor.ModeOr

# support code
def region_hier(cell, layer_idx):
    s = pya.Shapes()
    sp.merge(kldb, cell, layer_idx, s, True, 0, True, True)
    return pya.Region(s)

# Get the layer numbers
idx_nwell = kldb.layer(64, 20)
idx_diff = kldb.layer(65, 20)
idx_tap = kldb.layer(65, 44)
idx_nsdm = kldb.layer(93, 44)
idx_psdm = kldb.layer(94, 20)
idx_poly = kldb.layer(66, 20)
idx_licon = kldb.layer(66, 44)
idx_npc = kldb.layer(95, 20)
idx_error = kldb.layer(66, 25)

w_ch = 0.17
minw_impl = 0.38
mins_impl = 0.38
minenc_diff_impl = 0.125
mins_polylicon_psdm = 0.11
minw_npc = 0.27
minenc = 0.1
mins_npc = 0.27

for cell in kldb.each_cell():
    #
    ## Split difftap
    #
    r_nwell = pya.Region(cell.shapes(idx_nwell))
    r_diff = pya.Region(cell.shapes(idx_diff))
    r_nsdm = pya.Region(cell.shapes(idx_nsdm))
    r_psdm = pya.Region(cell.shapes(idx_psdm))

    # Generate tap and remove from diff
    r_tap = (r_diff & r_nwell & r_nsdm) + ((r_diff - r_nwell) & r_psdm)
    r_diff = r_diff - r_tap

    cell.shapes(idx_tap).insert(r_tap)
    s = cell.shapes(idx_diff)
    s.clear()
    s.insert(r_diff)

    #
    ## Generate npc layer
    ## min_width: 
    #
    r_poly = pya.Region(cell.shapes(idx_poly))
    r_licon = pya.Region(cell.shapes(idx_licon))
    size = max(0.5*(minw_npc - w_ch), minenc)
    over_size = 0.5*mins_npc

    r = r_licon & r_poly
    r.size(1000*size)

    # Fill space smaller then minimum space
    r.size(1000*over_size).merge().size(-1000*over_size)

    # Remove lines smaller than minimum width
    r.size(-1000*0.5*minw_npc).size(1000*0.5*minw_npc)

    # Add shapes to fix remaining minimum space violations
    # eps = r.space_check(1000*mins_npc, False, pya.Metrics.Square)
    eps = r.space_check(1000*mins_npc)
    r2 = pya.Region()
    for edgepair in eps:
        r2.insert(edgepair.bbox())
    r += r2.size(1000*0.5*minw_npc)

    # Be sure no remaining minimum space violations are remaining
    r.size(1000*over_size).merge().size(-1000*over_size)

    cell.shapes(idx_npc).insert(r)

    #
    ## Remove psdm too close to or covering poly licon
    ## Use hierarchical poly licon, diff and psdm
    #
    r_diff_hier = region_hier(cell, idx_diff)
    r_psdm = pya.Region(cell.shapes(idx_psdm))
    r_psdm_hier = region_hier(cell, idx_psdm)
    r_licon_hier = region_hier(cell, idx_licon)
    r_poly_hier = region_hier(cell, idx_poly)

    # Don't remove psdm needed for diff enclosure
    r_keep = r_diff_hier.sized(1000*minenc_diff_impl)

    # Select licon with distance from psdm smaller or equal minimum
    r_polylicon_hier = r_licon_hier & r_poly_hier
    r_close = r_polylicon_hier.interacting(r_psdm.sized(1000*mins_polylicon_psdm - 1))

    # Size big enough so it meets min. area even after trimmed by r_keep
    r_remove = r_close.sized(1000*0.40) - r_keep

    # Remove slivers and fill min space violations
    size_sliver = 1000*0.5*minw_impl - 1
    size_fill = 1000*0.5*mins_impl - 1
    r_remove.size(-size_sliver).size(size_sliver + size_fill).size(-size_fill)
    r_psdm_hier_trimmed = r_psdm_hier - r_remove

    # Remove slivers on trimmed psdm
    # We do this on hierarchical psdm to account for slivers abuted to psdm
    # in lower hierarchy
    r_psdm_hier_trimmed.size(-size_sliver).size(size_sliver)

    # The actual removed area from the hierarchical.
    r_removed = r_psdm_hier - r_psdm_hier_trimmed

    s_psdm = cell.shapes(idx_psdm)
    s_psdm.clear()
    s_psdm.insert(r_psdm - r_removed)

# Fix npc min. space on top level
cell = kldb.cell(mem_cell.name)

s_npc_all = pya.Shapes()
sp.size(kldb, cell, idx_npc, s_npc_all, 0.0, 0.0, OR, True, True, True)
s_npc = cell.shapes(idx_npc)
eps = pya.Region(s_npc_all).space_check(1000*mins_npc, False, pya.Metrics.Square)
for edgepair in eps:
    s_npc.insert(edgepair.bbox())

kldb.write(f"gds/{lib.name}.gds")

#
# Export LEF view
#
print("Exporting LEF file")

with open(f"lef/{lib.name}.lef", "w") as f:
    # f.write(mem_cell.lef(prim_lookup={
    #     prims["li"]: "li1",
    #     prims["m1"]: "met1",
    #     prims["m2"]: "met2",
    # }))
    f.write(mem_cell.lef())

# Export verilog view
#
print("Exporting behavioural verilog")

with open(f"verilog/{lib.name}.v", "w") as f:
    f.write(mem_cell.verilog())
