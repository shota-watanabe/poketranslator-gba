"""GBA ROM reader, writer, pointer scanner, and header manager."""

import os
from typing import List, Tuple, Optional, Dict


class GbaRom:
    """Manages reading, writing, pointer remapping, and header checksums of a GBA ROM."""

    GBA_ROM_BASE = 0x08000000
    GBA_ROM_EXPANDED_BASE = 0x09000000
    STANDARD_SIZE_16MB = 16 * 1024 * 1024
    MAX_SIZE_32MB = 32 * 1024 * 1024

    def __init__(self, data: bytes, filename: str = "rom.gba"):
        self.filename = filename
        self.data = bytearray(data)
        self.original_data = bytes(data)
        self._validate()
        self.free_space_offset = self._detect_initial_free_space()

    @classmethod
    def load(cls, path: str) -> "GbaRom":
        """Loads a GBA ROM from a file path."""
        with open(path, "rb") as f:
            data = f.read()
        return cls(data, filename=os.path.basename(path))

    def _validate(self) -> None:
        """Validates that the file is a GBA ROM."""
        if len(self.data) < 0x200:
            raise ValueError(f"ROM file is too small ({len(self.data)} bytes), invalid GBA ROM.")

    @property
    def game_title(self) -> str:
        """Reads the 12-byte Game Title from the GBA header."""
        raw = bytes(self.data[0xA0:0xAC])
        return raw.split(b"\x00")[0].decode("ascii", errors="replace").strip()

    @property
    def game_code(self) -> str:
        """Reads the 4-byte Game Code from the GBA header (e.g. BPRE for FireRed US)."""
        raw = bytes(self.data[0xAC:0xB0])
        return raw.decode("ascii", errors="replace").strip()

    @property
    def maker_code(self) -> str:
        """Reads the 2-byte Maker Code (e.g. 01 for Nintendo)."""
        raw = bytes(self.data[0xB0:0xB2])
        return raw.decode("ascii", errors="replace").strip()

    @property
    def software_version(self) -> int:
        """Reads the software version byte."""
        return self.data[0xBC]

    @property
    def header_checksum(self) -> int:
        """Reads the header checksum byte stored at 0xBD."""
        return self.data[0xBD]

    def calculate_header_checksum(self) -> int:
        """Calculates GBA header checksum using standard GBATEK formula."""
        checksum = 0
        for b in self.data[0xA0:0xBD]:
            checksum = (checksum - b) & 0xFF
        checksum = (checksum - 0x19) & 0xFF
        return checksum

    def fix_header_checksum(self) -> None:
        """Re-computes and overwrites the header checksum at 0xBD."""
        self.data[0xBD] = self.calculate_header_checksum()

    def verify_header_checksum(self) -> bool:
        """Checks if current header checksum matches the calculated GBATEK checksum."""
        return self.header_checksum == self.calculate_header_checksum()

    def is_firered(self) -> bool:
        """Returns True if the base ROM is Pokémon FireRed (BPRE, BPRJ, BPRP, etc.)."""
        return self.game_code.startswith("BPR")

    def is_emerald(self) -> bool:
        """Returns True if the base ROM is Pokémon Emerald (BPEE, BPEJ, BPEP, etc.)."""
        return self.game_code.startswith("BPE")

    def is_ruby_sapphire(self) -> bool:
        """Returns True if the base ROM is Ruby (AXVE/AXVJ) or Sapphire (AXPE/AXPJ)."""
        return self.game_code.startswith("AXV") or self.game_code.startswith("AXP")

    def detect_engine(self) -> str:
        """Detects whether ROM is standard FireRed, Emerald, CFRU (Complete FireRed Upgrade), etc."""
        # Check CFRU signature
        # CFRU commonly writes signature strings or flags in the expanded area
        cfru_signatures = [b"CFRU", b"Complete Fire Red Upgrade", b"DPE", b"Dynamic Pokemon Expansion"]
        for sig in cfru_signatures:
            if sig in self.data:
                return "CFRU (Complete FireRed Upgrade / Radical Red / Unbound)"

        if self.is_firered():
            return "Pokémon FireRed Engine"
        elif self.is_emerald():
            return "Pokémon Emerald Engine"
        elif self.is_ruby_sapphire():
            return "Pokémon Ruby/Sapphire Engine"
        return f"Unknown GBA Engine ({self.game_code})"

    def expand_to_32mb(self) -> None:
        """Expands ROM to 32MB (0x02000000 bytes) with 0xFF padding."""
        if len(self.data) < self.MAX_SIZE_32MB:
            padding_len = self.MAX_SIZE_32MB - len(self.data)
            self.data.extend(b"\xFF" * padding_len)
            if self.free_space_offset < len(self.original_data):
                self.free_space_offset = len(self.original_data)

    def _detect_initial_free_space(self) -> int:
        """Finds a safe starting offset for free space allocation."""
        if len(self.data) > self.STANDARD_SIZE_16MB:
            # Already expanded: search backward from end or start from original length
            return len(self.data) - 0x200000  # 2MB before end or at end of existing data

        # For 16MB ROM, scan backwards for a large block of 0xFFs
        block_size = 0x20000
        for offset in range(len(self.data) - block_size, 0x700000, -0x1000):
            if self.data[offset:offset + block_size] == b"\xFF" * block_size:
                return offset
        return len(self.data)

    def allocate_space(self, size: int, alignment: int = 4) -> int:
        """Allocates free space in the ROM for repointed text/data, aligning as needed."""
        # Align offset
        remainder = self.free_space_offset % alignment
        if remainder != 0:
            self.free_space_offset += alignment - remainder

        target_offset = self.free_space_offset
        needed_end = target_offset + size

        # Auto-expand if exceeding current ROM size
        if needed_end > len(self.data):
            self.expand_to_32mb()
            if needed_end > self.MAX_SIZE_32MB:
                raise OverflowError("ROM has reached maximum 32MB capacity. Cannot allocate more space.")

        self.free_space_offset = needed_end
        return target_offset

    def offset_to_ptr(self, offset: int) -> int:
        """Converts ROM file offset to GBA memory address."""
        if offset < 0x01000000:
            return self.GBA_ROM_BASE + offset
        else:
            return self.GBA_ROM_EXPANDED_BASE + (offset - 0x01000000)

    def ptr_to_offset(self, ptr: int) -> Optional[int]:
        """Converts GBA memory address (0x08XXXXXX or 0x09XXXXXX) to ROM file offset."""
        if 0x08000000 <= ptr < 0x09000000:
            offset = ptr - 0x08000000
            return offset if offset < len(self.data) else None
        elif 0x09000000 <= ptr < 0x0A000000:
            offset = ptr - 0x09000000 + 0x01000000
            return offset if offset < len(self.data) else None
        return None

    def read_ptr(self, offset: int) -> Tuple[int, Optional[int]]:
        """Reads 32-bit little-endian pointer from offset. Returns (gba_ptr, file_offset)."""
        raw = self.data[offset:offset + 4]
        if len(raw) < 4:
            return 0, None
        ptr = int.from_bytes(raw, byteorder="little")
        return ptr, self.ptr_to_offset(ptr)

    def write_ptr(self, offset: int, target_offset: int) -> None:
        """Writes 32-bit little-endian pointer pointing to target_offset."""
        gba_ptr = self.offset_to_ptr(target_offset)
        self.data[offset:offset + 4] = gba_ptr.to_bytes(4, byteorder="little")

    def find_all_pointers_to(self, target_offset: int) -> List[int]:
        """Scans the ROM for all 32-bit pointers referencing target_offset (aligned and unaligned script pointers)."""
        gba_ptr = self.offset_to_ptr(target_offset)
        ptr_bytes = gba_ptr.to_bytes(4, byteorder="little")
        results = []
        start = 0
        while True:
            idx = self.data.find(ptr_bytes, start)
            if idx == -1:
                break
            results.append(idx)
            start = idx + 1
        return results

    def repoint(self, old_offset: int, new_offset: int) -> int:
        """Finds all pointers pointing to old_offset and rewrites them to new_offset.
        
        Returns the number of pointers rewritten.
        """
        ptrs = self.find_all_pointers_to(old_offset)
        for p in ptrs:
            self.write_ptr(p, new_offset)
        return len(ptrs)

    def write_string_with_repoint(self, old_offset: int, old_len: int, new_bytes: bytes) -> int:
        """Writes new_bytes. If fits in old_len, writes in-place.
        Otherwise allocates new space, writes there, and repoints all references.
        
        Returns the offset where the string was placed.
        """
        if len(new_bytes) <= old_len:
            # Fits in place: pad remaining bytes with 0xFF
            self.data[old_offset:old_offset + len(new_bytes)] = new_bytes
            pad_len = old_len - len(new_bytes)
            if pad_len > 0:
                self.data[old_offset + len(new_bytes):old_offset + old_len] = b"\xFF" * pad_len
            return old_offset
        else:
            # Needs repointing
            new_offset = self.allocate_space(len(new_bytes), alignment=4)
            self.data[new_offset:new_offset + len(new_bytes)] = new_bytes
            self.repoint(old_offset, new_offset)
            return new_offset

    def export_rom(self, path: str) -> None:
        """Fixes header checksum and saves ROM to path."""
        self.fix_header_checksum()
        with open(path, "wb") as f:
            f.write(self.data)

    def save(self, path: str) -> None:
        """Alias for export_rom."""
        self.export_rom(path)

    def save_to_file(self, path: str) -> None:
        """Alias for export_rom."""
        self.export_rom(path)

    def create_ips_patch(self) -> bytes:
        """Generates an IPS patch representing changes between original and modified ROM."""
        patch = bytearray(b"PATCH")
        orig = self.original_data
        curr = self.data
        max_compare = min(len(orig), len(curr))

        i = 0
        while i < max_compare:
            if orig[i] != curr[i]:
                # Found differing block
                start = i
                if start >= 0xFFFFFF:
                    # IPS format only supports 24-bit offsets (up to 16MB)
                    break
                while i < max_compare and (orig[i] != curr[i] or (i + 1 < max_compare and orig[i + 1] != curr[i + 1])):
                    if i - start >= 0xFFFF:
                        break
                    i += 1
                diff_len = i - start
                # Record: 3 bytes offset, 2 bytes length, diff bytes
                patch.extend(start.to_bytes(3, byteorder="big"))
                patch.extend(diff_len.to_bytes(2, byteorder="big"))
                patch.extend(curr[start:i])
            else:
                i += 1

        # Check for expanded data appended at end (within 16MB limit for IPS)
        if len(curr) > len(orig):
            start = len(orig)
            while start < len(curr) and start < 0xFFFFFF:
                chunk_len = min(0xFFFF, min(len(curr) - start, 0xFFFFFF - start))
                patch.extend(start.to_bytes(3, byteorder="big"))
                patch.extend(chunk_len.to_bytes(2, byteorder="big"))
                patch.extend(curr[start:start + chunk_len])
                start += chunk_len

        patch.extend(b"EOF")
        return bytes(patch)
