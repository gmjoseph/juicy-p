import pytest

from constants import NametableMirroring
from constants import PPUAddress
from constants import PPURegister
from ppu_utils import maybe_resolve_nametable_address
from ppu_utils import maybe_resolve_palette_address
from ppu_utils import resolve_register


@pytest.mark.parametrize(('address', 'expected_register'), [
    (0x0, None),
    (0x4000, None),
    (0x8000, None),
    # Test literals
    (0x2000, PPURegister.PPUCTRL),
    (0x2001, PPURegister.PPUMASK),
    (0x2002, PPURegister.PPUSTATUS),
    (0x2003, PPURegister.OAMADDR),
    (0x2004, PPURegister.OAMDATA),
    (0x2005, PPURegister.PPUSCROLL),
    (0x2006, PPURegister.PPUADDR),
    (0x2007, PPURegister.PPUDATA),
    (0x4014, PPURegister.OAMDMA),
    # Test that enums and produce the right register.
    (PPUAddress.PPUCTRL_ADDRESS, PPURegister.PPUCTRL),
    (PPUAddress.PPUMASK_ADDRESS, PPURegister.PPUMASK),
    (PPUAddress.PPUSTATUS_ADDRESS, PPURegister.PPUSTATUS),
    (PPUAddress.OAMADDR_ADDRESS, PPURegister.OAMADDR),
    (PPUAddress.OAMDATA_ADDRESS, PPURegister.OAMDATA),
    (PPUAddress.PPUSCROLL_ADDRESS, PPURegister.PPUSCROLL),
    (PPUAddress.PPUADDR_ADDRESS, PPURegister.PPUADDR),
    (PPUAddress.PPUDATA_ADDRESS, PPURegister.PPUDATA),
    (PPUAddress.OAMDMA_ADDRESS, PPURegister.OAMDMA),
    # Test mirroring in the middle of the space.
    (0x2aa8, PPURegister.PPUCTRL),
    (0x2aa9, PPURegister.PPUMASK),
    (0x2aaa, PPURegister.PPUSTATUS),
    (0x2aab, PPURegister.OAMADDR),
    (0x2aac, PPURegister.OAMDATA),
    (0x2aad, PPURegister.PPUSCROLL),
    (0x2aae, PPURegister.PPUADDR),
    (0x2aaf, PPURegister.PPUDATA),
    # Test mirroring at the end of the space.
    (0x3ff8, PPURegister.PPUCTRL),
    (0x3ff9, PPURegister.PPUMASK),
    (0x3ffa, PPURegister.PPUSTATUS),
    (0x3ffb, PPURegister.OAMADDR),
    (0x3ffc, PPURegister.OAMDATA),
    (0x3ffd, PPURegister.PPUSCROLL),
    (0x3ffe, PPURegister.PPUADDR),
    (0x3fff, PPURegister.PPUDATA),
])
def test_resolve_register(address, expected_register):
    """
    Since the PPU registers are memory mapped and mirrored, we
    should be able to get the right register for an address even
    if it's a mirrored one.
    """
    assert expected_register == resolve_register(address)


@pytest.mark.parametrize(('address', 'expected_address', 'mirroring'), [
    (0x0, 0x0, None),
    # Edgecase on the border of nametable_0.
    (0x1FFF, 0x1FFF, None),
    # Palette ram index.
    (0x3F00, 0x3F00, None),
    # nametable_0
    (0x2000, 0x2000, None),
    (0x2000, 0x2000, NametableMirroring.HORIZONTAL),
    (0x2000, 0x2000, NametableMirroring.VERTICAL),
    # (0x2001, 0x2001, None),
    # (0x2001, 0x2001, NametableMirroring.HORIZONTAL),
    # (0x2001, 0x2001, NametableMirroring.VERTICAL),
    (0x23FF, 0x23FF, None),
    (0x23FF, 0x23FF, NametableMirroring.HORIZONTAL),
    (0x23FF, 0x23FF, NametableMirroring.VERTICAL),
    # nametable_1
    (0x2400, 0x2400, None),
    (0x2400, 0x2000, NametableMirroring.HORIZONTAL),
    (0x2400, 0x2400, NametableMirroring.VERTICAL),
    (0x27FF, 0x27FF, None),
    (0x27FF, 0x23FF, NametableMirroring.HORIZONTAL),
    (0x27FF, 0x27FF, NametableMirroring.VERTICAL),
    # nametable_2
    (0x2800, 0x2800, None),
    (0x2800, 0x2800, NametableMirroring.HORIZONTAL),
    (0x2800, 0x2000, NametableMirroring.VERTICAL),
    (0x2BFF, 0x2BFF, None),
    (0x2BFF, 0x2BFF, NametableMirroring.HORIZONTAL),
    (0x2BFF, 0x23FF, NametableMirroring.VERTICAL),
    # nametable_3
    (0x2C00, 0x2C00, None),
    (0x2C00, 0x2800, NametableMirroring.HORIZONTAL),
    (0x2C00, 0x2400, NametableMirroring.VERTICAL),
    (0x2FFF, 0x2FFF, None),
    (0x2FFF, 0x2BFF, NametableMirroring.HORIZONTAL),
    (0x2FFF, 0x27FF, NametableMirroring.VERTICAL),
    # Nametable mirrors
    (0x3000, 0x2000, None),
    (0x3C00, 0x2800, NametableMirroring.HORIZONTAL),
    (0x3C00, 0x2400, NametableMirroring.VERTICAL),
    (0x3EFF, 0x2EFF, None),
    (0x3EFF, 0x2AFF, NametableMirroring.HORIZONTAL),
    (0x3EFF, 0x26FF, NametableMirroring.VERTICAL),
])
def test_maybe_resolve_nametable_address(address, expected_address, mirroring):
    """
    There is a variety of mirroring that happens in name table
    accesses. This tests that we resolve an address to the
    mirrored location correctly.
    """
    assert expected_address == maybe_resolve_nametable_address(address, mirroring)


@pytest.mark.parametrize(('address', 'expected_address'), [
    (0x0, 0x0),
    (0x3F00, 0x3F00),
    (0x3F04, 0x3F04),
    (0x3F08, 0x3F08),
    (0x3F0C, 0x3F0C),
    (0x3F10, 0x3F00),
    (0x3F14, 0x3F04),
    (0x3F18, 0x3F08),
    (0x3F1C, 0x3F0C),
    # These are all palette ram mirrors.
    (0x3F00, 0x3F00),
    (0x3F20, 0x3F00),
    (0x3F01, 0x3F01),
    (0x3F21, 0x3F01),
    (0x3F0A, 0x3F0A),
    (0x3FEA, 0x3F0A),
    (0x3F3F, 0x3F1F),
    (0x3FFF, 0x3F1F),
    # Unaffected
    (0x2000, 0x2000),
    (0x3EFF, 0x3EFF),
])
def test_maybe_resolve_palette_address(address, expected_address):
    """
    Four addresses are mirrored in the PPU palette.
    """
    assert expected_address == maybe_resolve_palette_address(address)