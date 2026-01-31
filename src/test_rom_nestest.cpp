#include "NES.h"
#include <stdint.h>
#include <unordered_map>
#include <vector>
#include <stdio.h>

std::vector<std::unordered_map<std::string, uint64_t>>
_parse_log_entries() {
    std::string log_path = "../roms/nestest/nestest.log";
    FILE* f = fopen(log_path.c_str(), "rb");
    if (NULL == f) {
        printf("Failed to get log entires\n");
        exit(1);
    }

    std::vector<std::unordered_map<std::string, uint64_t>> entries;

    char buffer[255] = { 0 };
    while (fgets((char*)buffer, 255, f)) {
        std::string line = std::string(buffer);
        // printf("%s\n", line.c_str());
        // Most of the values are base 16 except ppu, scanline and cycles.
        uint64_t pc = std::stoull(line.substr(0, 4), 0, 16);
        uint64_t a = std::stoull(line.substr(50, 2), 0, 16);
        uint64_t x = std::stoull(line.substr(55, 2), 0, 16);
        uint64_t y = std::stoull(line.substr(60, 2), 0, 16);
        uint64_t p = std::stoull(line.substr(65, 2), 0, 16);
        uint64_t sp = std::stoull(line.substr(71, 2), 0, 16);
        uint64_t ppu_cycles = std::stoull(line.substr(78, 3));
        uint64_t scanline = std::stoull(line.substr(82, 3));
        uint64_t cpu_cycles = std::stoull(line.substr(90, line.length()));

        std::unordered_map<std::string, uint64_t> entry = {
            { "pc", pc },
            { "a", a },
            { "x", x },
            { "y", y },
            { "p", p },
            { "sp", sp },
            { "ppu_cycles", ppu_cycles },
            { "scanline", scanline },
            { "cpu_cycles", cpu_cycles }
        };
        entries.emplace_back(entry);
    }

    fclose(f);
    return entries;
}

void
print_failure_state(
    std::unordered_map<std::string, uint64_t>& entry,
    NES& nes
) {
    printf(
        "%llx %llx %llx %llx %llx %llx %llu %llu %llu (entry)\n",
        entry["pc"],
        entry["a"],
        entry["x"],
        entry["y"],
        entry["p"],
        entry["sp"],
        entry["cpu_cycles"],
        entry["ppu_cycles"],
        entry["scanline"]
    );
    printf(
        "%x %x %x %x %x %x %llu %llu %u (cpu)\n",
        nes.cpu.pc,
        nes.cpu.a,
        nes.cpu.x,
        nes.cpu.y,
        nes.cpu.p,
        nes.cpu.sp,
        nes.cpu.clock.cpu_cycles,
        nes.cpu.clock.ppu_cycles,
        nes.ppu.scanline
    );
}

int
main() {
    std::string filepath = "../roms/nestest/nestest.nes";
    auto entries = _parse_log_entries();

    NES nes = NES(filepath);
    nes.cpu.pc = 0xc000;

    for (auto& entry : entries) {
        if (nes.cpu.a != entry["a"]) {
            printf("Failed a\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.x != entry["x"]) {
            printf("Failed x\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.y != entry["y"]) {
            printf("Failed y\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.p != entry["p"]) {
            printf("Failed p\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.pc != entry["pc"]) {
            printf("Failed pc\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.sp != entry["sp"]) {
            printf("Failed sp\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.cpu.clock.cpu_cycles != entry["cpu_cycles"]) {
            printf("Failed cpu cycles\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.ppu.clock.ppu_cycles != entry["ppu_cycles"]) {
            printf("Failed ppu cycles\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        if (nes.ppu.scanline != entry["scanline"]) {
            printf("Failed scanline\n");
            print_failure_state(entry, nes);
            exit(1);
        }
        nes.cpu.next(false);
    }
    return 0;
}