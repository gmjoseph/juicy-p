from pathlib import Path

from nes import NES


def main(run_count = -1):
    rom_path = Path(__file__).parent.joinpath(
        '../roms/donkey_kong/donkey_kong.nes'
    )

    nes = NES(rom_path)
    if run_count > 0:
        while nes.ppu._frames < run_count:
            nes.run()
    else:
        while True:
            nes.run()

if __name__ == "__main__":
    main()
