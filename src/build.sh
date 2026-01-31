#!/bin/bash

clear
PATH=/System/Library/Frameworks:$PATH
# echo $PATH

# clang++ -std=c++11 -I"./include/" -L"./lib/" \

# No ASLR for debugging purposes.
# clang++ -std=c++11 -Wall \

# May need plist later?
# -sectcreate __TEXT __info_plist ./Info.plist \

# --debug: produce DWARF debug symbols
# -glldb: optimize debug information for lldb
debug="0"
release="1"
perf="2"

sources="
Cartridge.cpp
Clock.cpp
CPU.cpp
CPUMemory.cpp
CPUOperations.cpp
NES.cpp
PPU.cpp
PPUDebug.cpp
PPUMemory.cpp
PPUUtils.cpp
Renderer.cpp
AppDelegate.mm
MainView.mm
PPUWindow.mm
PPUWindowModel.mm
"

# TODO
# This is pretty much spaghetti code.
binary_name=""

# For some reason all of these need a space after
# the last multiline -o $binary_name which itself
# shouldn't need a \ but whatever for now...

if [ $1 -eq $debug ]; then
    binary_name="juicy-debug"
    echo $binary_name
    clang++ \
    --debug \
    -glldb \
    -std=c++11 \
    -fobjc-arc \
    -framework Appkit \
    -framework Foundation \
    $sources \
    main.mm \
    -o $binary_name \

    success=$?
fi

if [ $1 -eq $release ]; then
    binary_name="juicy"
    echo $binary_name
    clang++ \
    -O3 \
    -std=c++11 \
    -fobjc-arc \
    -framework Appkit \
    -framework Foundation \
    $sources \
    main.mm \
    -o $binary_name \

    success=$?
fi

if [ $1 -eq $perf ]; then
    binary_name="juicy-perf"
    echo $binary_name
    clang++ \
    --debug \
    -glldb \
    -std=c++11 \
    -fobjc-arc \
    -framework Appkit \
    -framework Foundation \
    $sources \
    main.cpp \
    -o $binary_name \

    success=$?
fi

if [ $success -eq 0 ]; then
    mkdir -p ../build
    # In case there was a debug build.
    # It's a folder
    mv "$binary_name.dSYM" ../build/
    mv $binary_name ../build/
    time ../build/$binary_name
else
    echo "Build failed." >&2
    exit 1
fi
