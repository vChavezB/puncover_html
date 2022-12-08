# Puncover HTML offline

Script to generate an offline HTML version of the [puncover](https://github.com/HBehrens/puncover) project. 
The puncover project allows to generate a website with the relevant information from a binary application (.elf). 
Unfortunately puncover creates a local server and offline access such as report generation is not possible. 

This script creates a local copy of the server running when you execute the puncover script.

## Motivation

Puncover is a nice tool to check locally for the information provided by map files. However, when you want to do a code review I do not want
to install the toolchain to see the output of puncover. I rather have an offline  HTML (e.g., codechecker, pvs studio, cppcheck) which I can
integrate in CI/CD.

## How to Use

1. Run puncover in a separate terminal or background process

Separate terminal

```bash
puncover --elf_file My_Cool_project.elf --gcc_tools_base /my_toolchain/bin/arm-none-eabi-
```

Background 

```bash
puncover --elf_file My_Cool_project.elf --gcc_tools_base /my_toolchain/bin/arm-none-eabi- &
```

2. Run this script

```bash
puncover_html.py HTML_OUT_PATH
```

## TODOS

- Add feature to look for symbols (i.e. button "Analyze text snippet"). 
   - Priority: LOW
     Puncover does this by using [rack.html.jinja](https://github.com/HBehrens/puncover/blob/3ca21079d1cda26e49070a38e75a473a1109859b/puncover/renderers.py#L342) template and the info it has on symbols.
     - Javascript to index all symbols
     - Look for symbols in the text editor
     - Add the stats simlar to the rack.html.jinja 
     
     Feature is wished but not necessary to analyze reports with CI/CD.


