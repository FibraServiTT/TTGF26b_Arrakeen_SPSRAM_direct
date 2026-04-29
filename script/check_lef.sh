#!/bin/sh
# To be run in top directory
magic -T pdk/sky130A.tech -dnull -noconsole <<EOF
lef read lef/tt_um_c4m_spsram_direct.lef
EOF
