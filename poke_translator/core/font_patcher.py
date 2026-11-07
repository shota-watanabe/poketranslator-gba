"""GBA Japanese Kana Font Patcher and Glyph Generator.
Injects Katakana and Hiragana glyphs into GBA Pokemon ROMs (FireRed/Emerald)
and configures font width tables so Japanese text displays natively.
"""

from typing import Dict, List, Tuple, Optional
from .rom import GbaRom
from .charmap import KANA_TABLE, JP_EXTRA_GLYPH_SOURCES

# ---------------------------------------------------------------------------
# Known Font and Width Table Offsets for Pokemon FireRed (BPRE v1.0)
# Each entry includes the Official Nintendo Japanese Font Sheet offsets
# embedded in every English FireRed ROM!
# ---------------------------------------------------------------------------
FIRERED_FONT_CONFIGS = [
    {
        "name": "Small Font (Bag / Items / Battle UI / Stats)",
        "gfx_offset": 0x1EAF00,
        "width_offset": 0x1EEF00,
        "glyph_size": 32,
        "default_width": 8,
        "jp_gfx_offset": 0x1EF100,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
    {
        "name": "Standard / Keyboard Font",
        "gfx_offset": 0x1F3100,
        "width_offset": 0x1FB100,
        "glyph_size": 64,
        "default_width": 8,
        "jp_gfx_offset": 0x1FB300,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
    {
        "name": "Black Dialogue Font",
        "gfx_offset": 0x1FF300,
        "width_offset": 0x207300,
        "glyph_size": 64,
        "default_width": 10,
        "jp_gfx_offset": 0x207500,
        "jp_width_offset": 0x20F500,
        "jp_glyph_size": 64,
    },
    {
        "name": "Blue Menu Font",
        "gfx_offset": 0x20F618,
        "width_offset": 0x217618,
        "glyph_size": 64,
        "default_width": 10,
        "jp_gfx_offset": 0x217818,
        "jp_width_offset": 0x21F818,
        "jp_glyph_size": 64,
    },
    {
        "name": "Red Menu Font",
        "gfx_offset": 0x21F930,
        "width_offset": 0x227930,
        "glyph_size": 64,
        "default_width": 10,
        "jp_gfx_offset": 0x227B30,
        "jp_width_offset": 0x22FB30,
        "jp_glyph_size": 64,
    },
]

# Emerald (BPEE) font and width tables + embedded Official JP font sheets
EMERALD_FONT_CONFIGS = [
    {
        "name": "Emerald Font 0 (Small 1)",
        "gfx_offset": 0x633CE4,
        "width_offset": 0x63BCE4,
        "glyph_size": 64,
        "default_width": 8,
        "jp_gfx_offset": 0x6544E4,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
    {
        "name": "Emerald Font 1 (Normal / UI)",
        "gfx_offset": 0x63BEE4,
        "width_offset": 0x643EE4,
        "glyph_size": 64,
        "default_width": 8,
        "jp_gfx_offset": 0x6584E4,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
    {
        "name": "Emerald Font 2 (Small 2)",
        "gfx_offset": 0x62BAE4,
        "width_offset": 0x633AE4,
        "glyph_size": 64,
        "default_width": 8,
        "jp_gfx_offset": 0x6544E4,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
    {
        "name": "Emerald Font 3 (Main Dialogue)",
        "gfx_offset": 0x6440E4,
        "width_offset": 0x64C0E4,
        "glyph_size": 64,
        "default_width": 10,
        "jp_gfx_offset": 0x66C8E4,
        "jp_width_offset": 0x6748E4,
        "jp_glyph_size": 64,
    },
    {
        "name": "Emerald Font 4 (Bold / Context)",
        "gfx_offset": 0x64C2E4,
        "width_offset": 0x6542E4,
        "glyph_size": 64,
        "default_width": 8,
        "jp_gfx_offset": 0x6584E4,
        "jp_width_offset": None,
        "jp_glyph_size": 32,
    },
]

# ---------------------------------------------------------------------------
# 8x12 Dot Matrix Patterns for Katakana (12 rows of 8 pixels)
# 0 = background, 1 = foreground pixel
# ---------------------------------------------------------------------------
KANA_DOT_PATTERNS: Dict[str, List[int]] = {
    # 8-bit integers per row (0 = left, 7 = right: 0b10000000 is left pixel)
    'ア': [0x7E, 0x06, 0x06, 0x0C, 0x18, 0x3E, 0x66, 0x46, 0x06, 0x06, 0x06, 0x00],
    'イ': [0x18, 0x38, 0x34, 0x64, 0x44, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x00],
    'ウ': [0x10, 0x10, 0x7E, 0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x3E, 0x00, 0x00],
    'エ': [0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00, 0x00],
    'オ': [0x18, 0x18, 0x7E, 0x18, 0x18, 0x38, 0x58, 0x4C, 0x06, 0x02, 0x00, 0x00],
    'カ': [0x7C, 0x44, 0x44, 0x4C, 0x5C, 0x68, 0x44, 0x46, 0x02, 0x02, 0x00, 0x00],
    'キ': [0x3C, 0x7E, 0x18, 0x7E, 0x18, 0x18, 0x30, 0x60, 0x40, 0x00, 0x00, 0x00],
    'ク': [0x38, 0x64, 0x44, 0x08, 0x10, 0x20, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00],
    'ケ': [0x10, 0x3C, 0x54, 0x94, 0x14, 0x14, 0x14, 0x14, 0x14, 0x00, 0x00, 0x00],
    'コ': [0x7E, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x7E, 0x00, 0x00, 0x00],
    'サ': [0x18, 0x7E, 0x38, 0x54, 0x14, 0x14, 0x14, 0x24, 0x44, 0x00, 0x00, 0x00],
    'シ': [0x40, 0x20, 0x00, 0x40, 0x20, 0x00, 0x44, 0x28, 0x10, 0x20, 0x40, 0x00],
    'ス': [0x7E, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x44, 0x44, 0x44, 0x00, 0x00, 0x00],
    'セ': [0x18, 0x7E, 0x58, 0x58, 0x58, 0x58, 0x78, 0x04, 0x04, 0x00, 0x00, 0x00],
    'ソ': [0x40, 0x20, 0x00, 0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x00, 0x00, 0x00],
    'タ': [0x10, 0x7C, 0x14, 0x7E, 0x14, 0x24, 0x44, 0x44, 0x00, 0x00, 0x00, 0x00],
    'チ': [0x38, 0x7C, 0x10, 0x7E, 0x10, 0x18, 0x30, 0x60, 0x40, 0x00, 0x00, 0x00],
    'ツ': [0x48, 0x24, 0x00, 0x48, 0x24, 0x00, 0x04, 0x08, 0x10, 0x20, 0x40, 0x00],
    'テ': [0x3C, 0x7E, 0x18, 0x18, 0x18, 0x30, 0x60, 0x7E, 0x00, 0x00, 0x00, 0x00],
    'ト': [0x10, 0x10, 0x18, 0x1C, 0x16, 0x12, 0x10, 0x10, 0x10, 0x00, 0x00, 0x00],
    'ナ': [0x18, 0x7E, 0x18, 0x18, 0x18, 0x34, 0x62, 0x42, 0x00, 0x00, 0x00, 0x00],
    'ニ': [0x7E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ヌ': [0x38, 0x7E, 0x14, 0x24, 0x44, 0x7E, 0x14, 0x24, 0x42, 0x00, 0x00, 0x00],
    'ネ': [0x10, 0x7C, 0x14, 0x14, 0x7C, 0x14, 0x14, 0x14, 0x00, 0x00, 0x00, 0x00],
    'ノ': [0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ハ': [0x42, 0x42, 0x24, 0x24, 0x18, 0x18, 0x24, 0x42, 0x00, 0x00, 0x00, 0x00],
    'ヒ': [0x78, 0x0C, 0x06, 0x06, 0x06, 0x7E, 0x06, 0x06, 0x00, 0x00, 0x00, 0x00],
    'フ': [0x7E, 0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ヘ': [0x08, 0x14, 0x22, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ホ': [0x18, 0x7E, 0x18, 0x5A, 0x5A, 0x5A, 0x5A, 0x18, 0x00, 0x00, 0x00, 0x00],
    'マ': [0x7E, 0x44, 0x28, 0x10, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ミ': [0x60, 0x30, 0x00, 0x60, 0x30, 0x00, 0x78, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ム': [0x10, 0x20, 0x40, 0x7E, 0x12, 0x24, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00],
    'メ': [0x22, 0x14, 0x08, 0x14, 0x22, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    'モ': [0x18, 0x7E, 0x18, 0x7E, 0x18, 0x18, 0x38, 0x70, 0x00, 0x00, 0x00, 0x00],
    'ヤ': [0x3E, 0x44, 0x44, 0x44, 0x3C, 0x14, 0x24, 0x44, 0x00, 0x00, 0x00, 0x00],
    'ユ': [0x7C, 0x44, 0x44, 0x7C, 0x10, 0x10, 0x10, 0x10, 0x00, 0x00, 0x00, 0x00],
    'ヨ': [0x7E, 0x06, 0x06, 0x3E, 0x06, 0x06, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ラ': [0x3C, 0x04, 0x7C, 0x08, 0x10, 0x20, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00],
    'リ': [0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x22, 0x02, 0x00, 0x00, 0x00, 0x00],
    'ル': [0x44, 0x44, 0x44, 0x44, 0x28, 0x10, 0x28, 0x44, 0x00, 0x00, 0x00, 0x00],
    'レ': [0x40, 0x40, 0x40, 0x40, 0x44, 0x28, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ロ': [0x7E, 0x42, 0x42, 0x42, 0x42, 0x42, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ワ': [0x7C, 0x44, 0x44, 0x44, 0x44, 0x44, 0x24, 0x1C, 0x00, 0x00, 0x00, 0x00],
    'ヲ': [0x7E, 0x18, 0x7E, 0x18, 0x30, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    'ン': [0x40, 0x20, 0x00, 0x42, 0x24, 0x18, 0x24, 0x42, 0x00, 0x00, 0x00, 0x00],
    'ー': [0x00, 0x00, 0x00, 0x7E, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '「': [0x3C, 0x30, 0x30, 0x30, 0x30, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '」': [0x00, 0x00, 0x00, 0x0C, 0x0C, 0x0C, 0x0C, 0x3C, 0x00, 0x00, 0x00, 0x00],
    '・': [0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '。': [0x00, 0x00, 0x00, 0x00, 0x00, 0x38, 0x44, 0x38, 0x00, 0x00, 0x00, 0x00],
    '、': [0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30, 0x00, 0x00, 0x00, 0x00],
}


def add_dakuten(pattern: List[int]) -> List[int]:
    """Adds dakuten dots to the top-right of the character pattern."""
    out = list(pattern)
    out[0] = out[0] | 0x03
    out[1] = out[1] | 0x06
    return out


def add_handakuten(pattern: List[int]) -> List[int]:
    """Adds handakuten circle to the top-right of the character pattern."""
    out = list(pattern)
    out[0] = out[0] | 0x06
    out[1] = out[1] | 0x09
    out[2] = out[2] | 0x06
    return out


def make_small(pattern: List[int]) -> List[int]:
    """Scales pattern down into small kana."""
    out = [0] * 12
    # Shift down and right
    for r in range(min(8, len(pattern))):
        out[r + 4] = (pattern[r] >> 2) & 0x3F
    return out


# Dynamically generate patterns for Dakuten / Handakuten / Small Kana
DAKUTEN_MAP = {
    'ガ': 'カ', 'ギ': 'キ', 'グ': 'ク', 'ゲ': 'ケ', 'ゴ': 'コ',
    'ザ': 'サ', 'ジ': 'シ', 'ズ': 'ス', 'ゼ': 'セ', 'ゾ': 'ソ',
    'ダ': 'タ', 'ヂ': 'チ', 'ヅ': 'ツ', 'デ': 'テ', 'ド': 'ト',
    'バ': 'ハ', 'ビ': 'ヒ', 'ブ': 'フ', 'ベ': 'ヘ', 'ボ': 'ホ',
    'ヴ': 'ウ',
}

HANDAKUTEN_MAP = {
    'パ': 'ハ', 'ピ': 'ヒ', 'プ': 'フ', 'ペ': 'ヘ', 'ポ': 'ホ',
}

SMALL_KANA_MAP = {
    'ァ': 'ア', 'ィ': 'イ', 'ゥ': 'ウ', 'ェ': 'エ', 'ォ': 'オ',
    'ッ': 'ツ', 'ャ': 'ヤ', 'ュ': 'ユ', 'ョ': 'ヨ',
}

for d_char, base_char in DAKUTEN_MAP.items():
    if base_char in KANA_DOT_PATTERNS:
        KANA_DOT_PATTERNS[d_char] = add_dakuten(KANA_DOT_PATTERNS[base_char])

for h_char, base_char in HANDAKUTEN_MAP.items():
    if base_char in KANA_DOT_PATTERNS:
        KANA_DOT_PATTERNS[h_char] = add_handakuten(KANA_DOT_PATTERNS[base_char])

for s_char, base_char in SMALL_KANA_MAP.items():
    if base_char in KANA_DOT_PATTERNS:
        KANA_DOT_PATTERNS[s_char] = make_small(KANA_DOT_PATTERNS[base_char])


def encode_tile_row(pixels: List[int]) -> bytes:
    """Encodes 8 pixels (0..3) into 2 bytes packed in GBA DecompressGlyphTile 2bpp format.
    
    In GBA DecompressGlyphTile (0x2F8C):
    - b1 (high byte, offset +1) encodes the LEFT 4 pixels (cols 0..3), MSB-first (bits 7..6 = col 0).
    - b0 (low byte, offset +0) encodes the RIGHT 4 pixels (cols 4..7), MSB-first (bits 7..6 = col 4).
    """
    b1 = ((pixels[0] & 3) << 6) | ((pixels[1] & 3) << 4) | ((pixels[2] & 3) << 2) | (pixels[3] & 3)
    b0 = ((pixels[4] & 3) << 6) | ((pixels[5] & 3) << 4) | ((pixels[6] & 3) << 2) | (pixels[7] & 3)
    return bytes([b0, b1])


def _fill_bg_pixels(tile_bytes: bytes, start_row: int, end_row: int) -> bytes:
    """Converts 2bpp pixel value 0 (0b00) to 3 (0b11, background fill) in rows start_row..end_row-1."""
    out = bytearray(tile_bytes)
    for r in range(start_row, min(end_row, len(out) // 2)):
        for idx in (r * 2, r * 2 + 1):
            b = out[idx]
            any_bit = ((b >> 1) | b) & 0x55
            zero_mask = (~(any_bit | (any_bit << 1))) & 0xFF
            out[idx] = b | zero_mask
    return bytes(out)


def extract_official_jp_glyph(
    rom_data: bytes,
    jp_gfx_offset: int,
    jp_glyph_size: int,
    src_gid: int,
    dst_glyph_size: int,
) -> bytes:
    """Extracts a single glyph from the ROM's built-in Official Nintendo Japanese font sheet
    and converts it to linear Latin font table tile order ([Top, Bot] or [TL, TR, BL, BR]).
    """
    if jp_glyph_size == 32:
        # 16 glyphs per row sheet (8x16 glyphs)
        off = jp_gfx_offset + (src_gid >> 4) * 512 + (src_gid & 15) * 16
        t_top = bytes(rom_data[off : off + 16])
        t_bot = bytes(rom_data[off + 256 : off + 272])
        if dst_glyph_size == 32:
            # Small font: fill background (0 -> 3) in rows 1..7 of top tile and rows 0..5 of bottom tile
            t_top = _fill_bg_pixels(t_top, 1, 8)
            t_bot = _fill_bg_pixels(t_bot, 0, 5)
            return t_top + t_bot
        else:
            # Standard 64B font: fill background (0 -> 3) in rows 0..7 of top tile and rows 0..6 of bottom tile
            t_top = _fill_bg_pixels(t_top, 0, 8)
            t_bot = _fill_bg_pixels(t_bot, 0, 6)
            empty = bytes(16)
            return t_top + empty + t_bot + empty
    else:
        # 8 glyphs per row sheet (64-byte 16x16 glyphs, already has background=3 in cols 0..9)
        off = jp_gfx_offset + (src_gid >> 3) * 512 + (src_gid & 7) * 32
        t_tl = bytes(rom_data[off : off + 16])
        t_tr = bytes(rom_data[off + 16 : off + 32])
        t_bl = bytes(rom_data[off + 256 : off + 272])
        t_br = bytes(rom_data[off + 272 : off + 288])
        if dst_glyph_size == 32:
            return t_tl + t_bl
        return t_tl + t_tr + t_bl + t_br


def has_official_jp_font(rom_data: bytes, jp_gfx_offset: Optional[int]) -> bool:
    """Checks whether the ROM contains an intact Official Nintendo Japanese font sheet at jp_gfx_offset."""
    if not jp_gfx_offset or jp_gfx_offset + 1024 > len(rom_data):
        return False
    sample = rom_data[jp_gfx_offset + 16 : jp_gfx_offset + 256]
    non_trivial = sum(1 for b in sample if b not in (0x00, 0xFF))
    return non_trivial >= 16


def pattern_to_2bpp_glyph(pattern: List[int], glyph_size: int = 64) -> bytes:
    """Converts a 12-row 8-pixel pattern into a GBA 2bpp glyph (32 or 64 bytes).
    
    In GBA 2bpp format:
    Each byte encodes 4 pixels (2 bits per pixel):
      0 = Transparent (background)
      1 = Text foreground color
      2 = Drop shadow / outline color
    """
    grid = [[0 for _ in range(8)] for _ in range(16)]
    v_offset = 2
    for r_idx, row_bits in enumerate(pattern):
        r = r_idx + v_offset
        if r >= 16:
            break
        for c in range(8):
            if (row_bits >> (7 - c)) & 1:
                grid[r][c] = 1

    # Add drop shadow (value 2) below and down-right for clean contrast
    for r in range(15):
        for c in range(8):
            if grid[r][c] == 1:
                if grid[r + 1][c] == 0:
                    grid[r + 1][c] = 2
                if c + 1 < 8 and grid[r + 1][c + 1] == 0:
                    grid[r + 1][c + 1] = 2

    # Encode top 8 rows (Tile 0 / TL) and bottom 8 rows (Tile 1 / BL)
    tile_top = bytearray()
    for r in range(8):
        tile_top.extend(encode_tile_row(grid[r]))

    tile_bot = bytearray()
    for r in range(8, 16):
        tile_bot.extend(encode_tile_row(grid[r]))

    if glyph_size == 32:
        return bytes(tile_top + tile_bot)
    else:
        empty_tile = bytes(16)
        # GBA 16x16 4-tile order: TL, TR, BL, BR
        return bytes(tile_top + empty_tile + tile_bot + empty_tile)


# Byte signatures of Official Nintendo Japanese font sheets (glyph 1 "あ")
_JP_MALE_64_SIG = b"\xff\xff\xff\xff\xbf\xfdU\xd5\xaa\xe9V\xf5\x99\xd9ji\x00\xf0\x00\xf0\x00\xf0\x00\xb0\x00\xb0\x00\xf0\x00\xb0\x00`"
_JP_SMALL_32_SIG = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06XU\xa8\xa6X\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18`&`\x06`"
_JP_NORM_32_FR_SIG = b"\x00\x00\x00\x06XU\xa8\xa6\x18\x06X\x15\x96fff\x00\x00\x00\x00\x00`\x18`&`\x06`\x06`\x06`"
_JP_NORM_32_EM_SIG = b"\x00\x00\x00\x00\x00\x00\x00\x06XU\xa8\xa6\x18\x06X\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00`\x18`&`\x06`"


def discover_font_configs(rom: GbaRom) -> List[Dict]:
    """Dynamically discovers all Latin font tables and built-in Official Japanese font sheets
    in any GBA Pokemon ROM (Vanilla FireRed/Emerald, CFRU, pokeemerald, pokefirered).
    """
    data = bytes(rom.original_data)
    data_len = len(data)

    # 1. Locate built-in Official Japanese font sheets by signature
    idx_male64 = data.find(_JP_MALE_64_SIG)
    jp_male_64 = (idx_male64 - 32) if idx_male64 >= 32 else None

    idx_small32 = data.find(_JP_SMALL_32_SIG)
    jp_small_32 = (idx_small32 - 16) if idx_small32 >= 16 else None

    idx_norm32 = data.find(_JP_NORM_32_FR_SIG)
    if idx_norm32 == -1:
        idx_norm32 = data.find(_JP_NORM_32_EM_SIG)
    jp_norm_32 = (idx_norm32 - 16) if idx_norm32 >= 16 else jp_small_32

    jp_sheet_offsets = {off for off in (jp_male_64, jp_small_32, jp_norm_32, 0x207500, 0x217818, 0x227B30, 0x66C8E4, 0x5E3178, 0x5EB378, 0x5F3578) if off is not None}

    # 2. Start with static configs whose offsets actually match valid width tables in this ROM
    base_configs = FIRERED_FONT_CONFIGS if rom.is_firered() else EMERALD_FONT_CONFIGS
    configs_by_gfx: Dict[int, Dict] = {}

    for cfg in base_configs:
        g_off = cfg["gfx_offset"]
        w_off = cfg["width_offset"]
        if w_off + 256 <= data_len:
            w_tbl = data[w_off : w_off + 256]
            if all(0 <= b <= 16 for b in w_tbl) and all(3 <= w_tbl[c] <= 10 for c in range(0xBB, 0xD5)):
                configs_by_gfx[g_off] = dict(cfg)

    # 3. Dynamically scan code literal pools (0x000000..0x350000) for (gfx_offset, width_offset) pairs
    max_code = min(data_len - 12, 0x350000)
    for p_off in range(0, max_code, 4):
        v1 = int.from_bytes(data[p_off : p_off + 4], "little") - 0x08000000
        if not (0x100000 <= v1 < data_len - 0x4000) or v1 in jp_sheet_offsets or v1 in configs_by_gfx:
            continue
        for delta in (4, 8):
            v2 = int.from_bytes(data[p_off + delta : p_off + delta + 4], "little") - 0x08000000
            if v2 in (v1 + 0x8000, v1 + 0x4000, v1 - 0x200) and 0x100000 <= v2 < data_len - 256:
                w_tbl = data[v2 : v2 + 256]
                if all(0 <= b <= 16 for b in w_tbl) and all(3 <= w_tbl[c] <= 10 for c in range(0xBB, 0xD5)):
                    gsz = 32 if (v2 == v1 + 0x4000) else 64
                    # Determine whether this is a Small, Narrow UI, or Main Dialogue font
                    row0_bytes = data[v1 + 0xBB * gsz : v1 + 0xBB * gsz + 2]
                    if gsz == 32 or row0_bytes == b"\x00\x00":
                        jp_src = jp_small_32 or jp_norm_32
                        jp_gsz = 32
                        def_w = 8
                        jp_w_off = None
                    elif row0_bytes == b"\xC0\xFF" and jp_norm_32 is not None:
                        jp_src = jp_norm_32
                        jp_gsz = 32
                        def_w = 8
                        jp_w_off = None
                    elif jp_male_64 is not None:
                        jp_src = jp_male_64
                        jp_gsz = 64
                        def_w = 10
                        # Check if jp_male_64 has a width table at +0x8000 or -0x200
                        jp_w_off = None
                        for cand_w in (jp_male_64 + 0x8000, jp_male_64 - 0x200):
                            if 0 <= cand_w <= data_len - 256 and all(4 <= data[cand_w + c] <= 12 for c in range(1, 0x50)):
                                jp_w_off = cand_w
                                break
                    else:
                        jp_src = jp_norm_32
                        jp_gsz = 32
                        def_w = 8
                        jp_w_off = None

                    configs_by_gfx[v1] = {
                        "name": f"Discovered Font @ 0x{v1:X}",
                        "gfx_offset": v1,
                        "width_offset": v2,
                        "glyph_size": gsz,
                        "default_width": def_w,
                        "jp_gfx_offset": jp_src,
                        "jp_width_offset": jp_w_off,
                        "jp_glyph_size": jp_gsz,
                    }
                    break

    return list(configs_by_gfx.values()) if configs_by_gfx else list(base_configs)


def patch_kana_font(rom: GbaRom, char_width: int = 9) -> Dict[str, int]:
    """Injects Japanese Hiragana, Katakana, and punctuation glyphs and updates character width tables.
    
    Uses the ROM's built-in Official Nintendo Japanese font sheets when available,
    falling back to hardware-accurate generated 2bpp glyphs on blank test ROMs.
    """
    configs = discover_font_configs(rom)
    patched_count = 0

    for cfg in configs:
        gfx_base = cfg["gfx_offset"]
        width_base = cfg["width_offset"]
        glyph_size = cfg["glyph_size"]
        default_w = cfg.get("default_width", char_width)
        jp_gfx_base = cfg.get("jp_gfx_offset")
        jp_width_base = cfg.get("jp_width_offset")
        jp_glyph_size = cfg.get("jp_glyph_size", glyph_size)

        if gfx_base + (256 * glyph_size) > len(rom.data):
            continue

        use_official = has_official_jp_font(rom.original_data, jp_gfx_base)

        if use_official and jp_gfx_base is not None:
            # 1. Copy all 160 Official Nintendo Hiragana (0x01..0x50) and Katakana (0x51..0xA0)
            glyph_mappings = [(gid, gid) for gid in range(0x01, 0xA1)]
            # 2. Copy Official Japanese punctuation (ー, 。, 「, 」, 『, 』) into 0xF1..0xF6
            for dst_gid, src_gid in JP_EXTRA_GLYPH_SOURCES.items():
                glyph_mappings.append((dst_gid, src_gid))

            for dst_gid, src_gid in glyph_mappings:
                glyph_bytes = extract_official_jp_glyph(
                    rom.original_data,
                    jp_gfx_base,
                    jp_glyph_size,
                    src_gid,
                    glyph_size,
                )
                char_offset = gfx_base + (dst_gid * glyph_size)
                if char_offset + glyph_size <= len(rom.data):
                    rom.data[char_offset : char_offset + glyph_size] = glyph_bytes
                    patched_count += 1

                # Update font width table entry from Official JP width table if present
                width_offset = width_base + dst_gid
                if width_offset < len(rom.data):
                    if jp_width_base and (jp_width_base + src_gid) < len(rom.original_data):
                        jp_w = rom.original_data[jp_width_base + src_gid]
                        rom.data[width_offset] = jp_w if 4 <= jp_w <= 12 else default_w
                    else:
                        rom.data[width_offset] = default_w
        else:
            # Fallback for mock/custom ROMs without Official JP font sheets
            for byte_val, kata, hira in KANA_TABLE:
                pattern = KANA_DOT_PATTERNS.get(kata)
                if not pattern:
                    continue

                glyph_bytes = pattern_to_2bpp_glyph(pattern, glyph_size=glyph_size)
                char_offset = gfx_base + (byte_val * glyph_size)

                if char_offset + glyph_size <= len(rom.data):
                    rom.data[char_offset : char_offset + glyph_size] = glyph_bytes
                    patched_count += 1

                width_offset = width_base + byte_val
                if width_offset < len(rom.data):
                    rom.data[width_offset] = default_w

    return {
        "status": "success",
        "patched_glyphs": patched_count,
        "char_width": char_width,
    }
