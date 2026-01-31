import pytest
from unittest.mock import MagicMock

from constants import NametableMirroring
from ppu_memory import PPUMemory


@pytest.mark.parametrize(('address', 'mapped_address', 'mirroring'), [
    (0x0, 0x0, None),
    # Edgecase on the border of nametable_0.
    (0x1FFF, 0x1FFF, None),
    # Palette ram index.
    (0x3F00, 0x3F00, None),
    # nametable_0
    (0x2000, 0x2000, None),
    (0x2000, 0x2000, NametableMirroring.HORIZONTAL),
    (0x2000, 0x2000, NametableMirroring.VERTICAL),
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
def test_nametable_addresses(address, mapped_address, mirroring):
    """
    For reads and writes, the PPU should respect mirroring settings.
    If we write to a mirrored address, we should expect to be able
    to read the value from the source address and vice versa.
    """
    memory = PPUMemory()
    memory.nametable_mirroring = mirroring
    # Ensures that the memory is in a predictable state for the
    # reads and writes to follow.
    memory.write(0x00, address)
    memory.write(0x00, mapped_address)

    memory.write(0xba, mapped_address)
    assert 0xba == memory.read_one(address)

    memory.write(0xbe, address)
    assert 0xbe == memory.read_one(mapped_address)


@pytest.mark.parametrize(('address', 'mapped_address'), [
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
    (0x3FFF, 0x3F1F),
    # Unaffected
    (0x2000, 0x2000),
    (0x3EFF, 0x3EFF),
])
def test_palette_addresses(address, mapped_address):
    """
    For reads and writes, the PPU should respect mirroring in the
    PPU palette.
    """
    memory = PPUMemory()
    # Ensures that the memory is in a predictable state for the
    # reads and writes to follow.
    memory.write(0x00, address)
    memory.write(0x00, mapped_address)

    memory.write(0xba, mapped_address)
    assert memory.read_one(address) == 0xba

    memory.write(0xbe, address)
    assert memory.read_one(mapped_address) == 0xbe


def test_address_caching():
    """
    Because the PPU has so much mirroring going on, this ensures
    that once we've resolved a mirrored address to its proper
    address we don't have to repeat the process.
    """
    memory = PPUMemory()
    assert 0x3456 not in memory._address_cache

    memory.read_one(0x3456)
    # 0x3456 should now be in the cache.
    assert 0x3456 in memory._address_cache

    # Both 'read' and 'write' functions should now go to
    # the cache for this instead of the preprocessors.
    memory._run_address_preprocesseors = MagicMock()

    memory.write(0xa, 0x3456)
    assert not memory._run_address_preprocesseors.call_count

    memory.read_one(0x3456)
    assert not memory._run_address_preprocesseors.call_count
