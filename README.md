# Sky130 Tiny Tapeout Single Port SRAM

This is design for a single port SRAM block with pins connected directly to TT tile pins. It's 128 words of 8 bits which fits in a 1x1 tile.

```shell
uv sync
mkdir gds lef verilog
uv run src/generate_views.py
```

## Build the LibreLane Design

Install Nix for LibreLane: https://librelane.readthedocs.io/en/stable/installation/nix_installation/index.html

Enable a Nix shell with dev branch of LibreLane: `nix shell github:librelane/librelane/dev`

Build the design: `librelane config.yaml`

View the design in OpenROAD: `librelane config.yaml --last-run --flow OpenInOpenROAD`
