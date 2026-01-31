clear
PATH=/System/Library/Frameworks:$PATH

sources="
Cartridge.cpp
Clock.cpp
CPU.cpp
CPUMemory.cpp
CPUOperations.cpp
NES.cpp
PPU.cpp
PPUMemory.cpp
PPUUtils.cpp
Renderer.cpp
"

mkdir -p ../build

compile_test () {
    test_name=$1
    # Takes ages to compile with O3 but the code is extremely fast.
    # clang++ -O3 -std=c++11 \
    clang++ -std=c++11 \
    $sources \
    $test_name.cpp \
    -o $test_name \

    if [ $? -eq 0 ]
        then
            mv $test_name ../build
    else
        echo "Test $1 build failed." >&2
        exit 1;
    fi
}

run_test () {
    test_name=$1
    time ../build/$test_name
}

tests="
    test_clock
    test_cpu
    test_donkey_kong
    test_input
    test_io_db
    test_oam
    test_performance
    test_ppu_memory
    test_ppu_render
    test_ppu_utils
    test_ppu
    test_rom_nestest
"

# Runs a single test
if [ ! -z "$1" ]
    then
        echo $1
        compile_test $1
        run_test $1
else
    for test in $tests; do
        echo $test
        compile_test $test
        run_test $test
    done
fi


