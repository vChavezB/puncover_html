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

3. Copy static folder of this repo to your HTML_OUT_PATH (See todos)

## TODOS

- Fix sort row for the columns stack,code,remarks. Current implementation only sorts code column independent of column clicked. Check static/js/sorttable.js. 
- Add feature to look for symbols.
- Copy static folder to html output


