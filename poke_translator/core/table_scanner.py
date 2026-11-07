"""Enhanced scanner and extractor for Pokemon ROM hack tables, menus, and dialogue scripts.
Supports Title Case (Pokemon Gaia, Unbound, etc.), Expanded Tables, and Repointed Data.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from .rom import GbaRom
from .charmap import decode_gba_string, encode_gba_string
from .dictionary import auto_translate_text
from .dialogue_data import format_gba_dialogue


# ---------------------------------------------------------------------------
# Common English dialogue words vocabulary for filtering out ARM binary garbage
# ---------------------------------------------------------------------------
COMMON_DIALOGUE_WORDS = {
    'the', 'to', 'and', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'with', 'as',
    'i', 'his', 'they', 'be', 'at', 'one', 'have', 'this', 'from', 'or', 'had', 'by', 'not', 'word', 'but',
    'what', 'some', 'we', 'can', 'out', 'other', 'were', 'all', 'there', 'when', 'up', 'use', 'your', 'how',
    'said', 'an', 'each', 'she', 'which', 'do', 'their', 'time', 'if', 'will', 'way', 'about', 'many', 'then',
    'them', 'write', 'would', 'like', 'so', 'these', 'her', 'long', 'make', 'thing', 'see', 'him', 'two', 'has',
    'look', 'more', 'day', 'could', 'go', 'come', 'did', 'number', 'sound', 'no', 'most', 'people', 'my', 'over',
    'know', 'water', 'than', 'call', 'first', 'who', 'may', 'down', 'side', 'been', 'now', 'find', 'any', 'new',
    'work', 'part', 'take', 'get', 'place', 'made', 'live', 'where', 'after', 'back', 'little', 'only', 'round',
    'man', 'year', 'came', 'show', 'every', 'good', 'me', 'give', 'our', 'under', 'name', 'very', 'through', 'just',
    'great', 'think', 'say', 'help', 'low', 'line', 'turn', 'much', 'mean', 'before', 'move', 'right', 'boy', 'old',
    'too', 'same', 'tell', 'does', 'set', 'three', 'want', 'air', 'well', 'also', 'play', 'small', 'end', 'put',
    'home', 'read', 'hand', 'port', 'large', 'even', 'land', 'here', 'must', 'big', 'high', 'such', 'why', 'ask',
    'men', 'change', 'went', 'light', 'kind', 'off', 'need', 'house', 'try', 'us', 'again', 'animal', 'point',
    'mother', 'world', 'near', 'build', 'self', 'earth', 'father', 'head', 'stand', 'own', 'page', 'should',
    'country', 'found', 'answer', 'school', 'grow', 'study', 'still', 'learn', 'keep', 'eye', 'never', 'last',
    'let', 'thought', 'city', 'tree', 'hard', 'start', 'might', 'story', 'saw', 'far', 'sea', 'left', 'late', 'run',
    'don', 'while', 'press', 'close', 'night', 'real', 'life', 'few', 'north', 'open', 'seem', 'together', 'next',
    'white', 'children', 'begin', 'got', 'walk', 'always', 'those', 'both', 'mark', 'often', 'letter', 'until',
    'care', 'second', 'book', 'took', 'eat', 'room', 'friend', 'began', 'idea', 'stop', 'once', 'base', 'hear',
    'cut', 'sure', 'watch', 'color', 'main', 'enough', 'girl', 'young', 'ready', 'above', 'ever', 'red', 'feel',
    'talk', 'soon', 'family', 'leave', 'door', 'black', 'short', 'question', 'happen', 'complete', 'area', 'rock',
    'order', 'fire', 'south', 'piece', 'told', 'knew', 'pass', 'since', 'top', 'whole', 'king', 'nothing', 'course',
    'stay', 'full', 'blue', 'decide', 'deep', 'moon', 'island', 'foot', 'system', 'busy', 'test', 'record',
    'common', 'gold', 'possible', 'dry', 'wonder', 'laugh', 'thousand', 'ago', 'ran', 'check', 'game', 'hot',
    'miss', 'brought', 'heat', 'bring', 'yes', 'distant', 'fill', 'east', 'among', 'power', 'town', 'fine', 'certain',
    'fly', 'fall', 'lead', 'cry', 'dark', 'machine', 'note', 'wait', 'plan', 'figure', 'star', 'box', 'field', 'rest',
    'correct', 'able', 'done', 'stood', 'front', 'teach', 'week', 'final', 'gave', 'green', 'oh', 'quick', 'warm',
    'free', 'minute', 'strong', 'special', 'mind', 'behind', 'clear', 'fact', 'space', 'heard', 'best', 'hour',
    'better', 'during', 'hundred', 'five', 'remember', 'step', 'early', 'hold', 'west', 'ground', 'reach', 'fast',
    'listen', 'six', 'table', 'travel', 'less', 'morning', 'ten', 'simple', 'several', 'toward', 'against',
    'slow', 'center', 'love', 'person', 'money', 'serve', 'appear', 'road', 'map', 'rule', 'pull', 'cold', 'notice',
    'voice', 'energy', 'hunt', 'bed', 'brother', 'egg', 'ride', 'believe', 'perhaps', 'pick', 'sudden', 'count',
    'reason', 'art', 'region', 'size', 'speak', 'ice', 'matter', 'pair', 'include', 'felt', 'grand', 'ball', 'yet',
    'drop', 'heart', 'am', 'present', 'heavy', 'dance', 'wide', 'forest', 'sit', 'race', 'window', 'store', 'train',
    'sleep', 'prove', 'wall', 'catch', 'wish', 'sky', 'board', 'written', 'wild', 'kept', 'grass', 'sign', 'visit',
    'past', 'fun', 'bright', 'weather', 'finish', 'happy', 'hope', 'strange', 'gone', 'jump', 'village', 'meet',
    'buy', 'raise', 'solve', 'whether', 'push', 'seven', 'shall', 'held', 'describe', 'floor', 'either', 'safe',
    'type', 'copy', 'phrase', 'silent', 'tall', 'sand', 'soil', 'value', 'fight', 'natural', 'view', 'sense', 'else',
    'quite', 'broke', 'case', 'middle', 'son', 'lake', 'moment', 'child', 'speed', 'pay', 'age', 'section', 'cloud',
    'surprise', 'quiet', 'stone', 'tiny', 'climb', 'cool', 'poor', 'lot', 'bottom', 'key', 'single', 'twenty',
    'smile', 'hole', 'trade', 'trip', 'receive', 'mouth', 'exact', 'trouble', 'shout', 'except', 'wrote', 'join',
    'clean', 'break', 'lady', 'bad', 'team', 'cost', 'lost', 'wear', 'equal', 'sent', 'choose', 'fell', 'fit', 'fair',
    'bank', 'collect', 'save', 'please', 'protect', 'whose', 'ring', 'character', 'radio', 'human', 'modern', 'hit',
    'student', 'corner', 'party', 'danger', 'rich', 'thick', 'process', 'guess', 'sharp', 'rather', 'crowd', 'famous',
    'fear', 'sight', 'thin', 'hurry', 'chief', 'clock', 'mine', 'enter', 'major', 'fresh', 'search', 'send', 'yellow',
    'allow', 'print', 'spot', 'continue', 'block', 'hat', 'sell', 'success', 'deal', 'term', 'spread', 'camp',
    'determine', 'nine', 'level', 'chance', 'gather', 'shop', 'select', 'wrong', 'gray', 'prepare', 'claim',
    'pretty', 'skill', 'solution', 'thank', 'match', 'especially', 'afraid', 'huge', 'similar', 'guide', 'experience',
    'total', 'basic', 'valley', 'arrive', 'master', 'track', 'shore', 'share', 'station', 'dad', 'bar', 'offer',
    'instant', 'market', 'dear', 'enemy', 'reply', 'occur', 'support', 'speech', 'path', 'teeth', 'shell',
    'pokemon', 'pokémon', 'trainer', 'gym', 'badge', 'battle', 'route', 'town', 'city', 'champion', 'league',
    'item', 'attack', 'potion', 'ball', 'mart', 'center', 'professor', 'redwood', 'oak', 'orbtus', 'pokedex', 'pokédex',
    'creature', 'ruins', 'library', 'residence', 'house', 'tunnel', 'cave', 'forest', 'elder', 'marshal', 'hello',
    'today', 'something', 'anything', 'everything', 'everyone', 'someone', 'anyone', 'into', 'onto', 'within',
    'without', 'already', 'really', 'actually', 'friends', 'partners', 'adventure', 'adventures', 'world', 'welcome',
}


def is_real_english_dialogue(text: str) -> bool:
    """Accurately identifies genuine English script dialogue, rejecting binary/ARM garbage."""
    if not text or len(text) < 8 or r"\x" in text:
        return False
    # Reject strings with binary symbol tokens that never appear in real dialogue
    if any(tok in text for tok in ("[PK]", "[MN]", "[PO]", "[KE]", "[BL]", "[OC]", "ᵉʳ", "ª", "º")):
        return False
    # Strip control tags and normalize é/É before checking words
    clean = re.sub(r"\[[^\]]+\]", " ", text).replace("é", "e").replace("É", "E")
    words = re.findall(r"[a-zA-Z]{2,}", clean.lower())
    if len(words) < 2:
        return False
    known = sum(1 for w in words if w in COMMON_DIALOGUE_WORDS)
    if len(words) == 2:
        return known >= 1 and any(ch in clean for ch in (".", "!", "?", "…", "▲", "▼", "◀", "▶"))
    return (known / len(words)) >= 0.40


def is_valid_name(s: str) -> bool:
    """Validates if a decoded string is a plausible Pokemon/move/item/ability name."""
    if not s or s == "-":
        return True
    s = s.strip()
    if not s or len(s) < 2:
        return False
    if any(c in s for c in [":", ";", "\\x", "[WAIT]", "[PLAYER]", "[RIVAL]", "[CLEAR]", "\n"]):
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.'’`éÉ♀♂!?/()+,:")
    valid_count = sum(1 for c in s if c in allowed)
    return (valid_count / len(s)) >= 0.8


def is_valid_description(s: str) -> bool:
    """Validates if a decoded string is a plausible item/move description."""
    if not s or len(s) < 12:
        return False
    words = s.split()
    if len(words) < 3:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.'’`éÉ♀♂!?/()+,:\n")
    return (sum(1 for c in s if c in allowed) / len(s)) >= 0.8


class TextEntry:
    """Represents a translatable string entry in the ROM."""

    def __init__(
        self,
        entry_id: str,
        category: str,
        offset: int,
        length: int,
        original_text: str,
        translated_text: str = "",
        max_length: Optional[int] = None,
        pointer_offsets: Optional[List[int]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.entry_id = entry_id
        self.category = category
        self.offset = offset
        self.length = length
        self.original_text = original_text
        self.translated_text = translated_text
        self.max_length = max_length
        self.pointer_offsets = pointer_offsets or []
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.entry_id,
            "category": self.category,
            "offset": f"0x{self.offset:X}",
            "length": self.length,
            "original": self.original_text,
            "translated": self.translated_text,
            "max_length": self.max_length,
            "pointer_count": len(self.pointer_offsets),
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TextEntry":
        offset = int(d["offset"], 16) if isinstance(d["offset"], str) else d["offset"]
        return cls(
            entry_id=d["id"],
            category=d["category"],
            offset=offset,
            length=d["length"],
            original_text=d["original"],
            translated_text=d.get("translated", ""),
            max_length=d.get("max_length"),
            pointer_offsets=d.get("pointer_offsets", []),
            meta=d.get("meta", {}),
        )


class TableScanner:
    """Scans and extracts all tables, menus, descriptions, and dialogue text from a GBA ROM."""

    def __init__(self, rom: GbaRom):
        self.rom = rom

    def scan_all(self, include_dialogues: bool = True) -> List[TextEntry]:
        """Runs full scan across all game data categories."""
        entries: List[TextEntry] = []
        entries.extend(self.scan_pokemon_species())
        entries.extend(self.scan_moves())
        entries.extend(self.scan_items())
        entries.extend(self.scan_abilities())
        entries.extend(self.scan_types())
        entries.extend(self.scan_move_descriptions())
        entries.extend(self.scan_menus())

        if include_dialogues:
            existing_offsets = {e.offset for e in entries}
            entries.extend(self.scan_dialogues(limit=10000, exclude_offsets=existing_offsets))

        return entries

    # -----------------------------------------------------------------------
    # Multi-Casing String Sequence Scanner
    # Searches Title Case, ALL CAPS, and Lowercase to support ROM hacks like Gaia!
    # -----------------------------------------------------------------------
    def _find_string_sequence(self, variants: List[List[str]], expected_stride: int) -> Optional[int]:
        """Finds table offset by testing multiple casing variants of a sequence."""
        for strings in variants:
            found = self._find_single_sequence(strings, expected_stride)
            if found is not None:
                return found
        return None

    def _find_single_sequence(self, strings: List[str], expected_stride: int) -> Optional[int]:
        if not strings:
            return None

        first_encoded = encode_gba_string(strings[0], use_kana=False)
        start = 0
        while True:
            idx = self.rom.data.find(first_encoded, start)
            if idx == -1:
                break

            matched = True
            for i in range(1, len(strings)):
                next_offset = idx + (i * expected_stride)
                if next_offset >= len(self.rom.data):
                    matched = False
                    break
                next_encoded = encode_gba_string(strings[i], use_kana=False)
                if not self.rom.data.startswith(next_encoded, next_offset):
                    matched = False
                    break

            if matched:
                return idx
            start = idx + 1

        return None

    # -----------------------------------------------------------------------
    # Pokemon Species
    # -----------------------------------------------------------------------
    def scan_pokemon_species(self) -> List[TextEntry]:
        entries = []
        stride = 11

        # Check Title Case (Pokemon Gaia, Unbound) and ALL-CAPS (Vanilla)
        variants = [
            ["Bulbasaur", "Ivysaur", "Venusaur"],
            ["BULBASAUR", "IVYSAUR", "VENUSAUR"],
        ]
        found = self._find_string_sequence(variants, stride)
        if found is not None:
            # Bulbasaur is species index 1 (index 0 is ?????????? / none)
            table_offset = found - stride
        elif self.rom.is_firered():
            table_offset = 0x245EE0
        elif self.rom.is_emerald():
            table_offset = 0x3185C8
        else:
            table_offset = None

        if table_offset is None or table_offset >= len(self.rom.data):
            return entries

        idx = 0
        offset = table_offset
        # In vanilla Emerald (and Blazed Glazed), species table ends at index 411 (Deoxys)
        max_species = 411 if self.rom.is_emerald() else 1025
        while idx <= max_species and offset + stride <= len(self.rom.data):
            raw = self.rom.data[offset:offset + stride]
            if raw == b"\xFF" * stride:
                break
            text, _ = decode_gba_string(raw, use_kana=False)
            text = text.strip()
            if text and not text.startswith("????"):
                entries.append(TextEntry(
                    entry_id=f"species_{idx}",
                    category="species",
                    offset=offset,
                    length=stride,
                    original_text=text,
                    translated_text=auto_translate_text(text, "species") or "",
                    max_length=stride,
                    meta={"dex_number": idx},
                ))
            idx += 1
            offset += stride

        return entries

    # -----------------------------------------------------------------------
    # Move Names
    # -----------------------------------------------------------------------
    def scan_moves(self) -> List[TextEntry]:
        entries = []
        stride = 13

        # Test Title Case (Gaia/Unbound), ALL-CAPS (Vanilla), and hyphen variations
        variants = [
            ["Pound", "Karate Chop", "Double Slap"],
            ["POUND", "KARATE CHOP", "DOUBLE SLAP"],
            ["Pound", "Karate Chop", "DoubleSlap"],
            ["POUND", "KARATE CHOP", "DOUBLESLAP"],
        ]
        found = self._find_string_sequence(variants, stride)
        if found is not None:
            table_offset = found - stride
        elif self.rom.is_firered():
            table_offset = 0x247094
        elif self.rom.is_emerald():
            table_offset = 0x31977C
        else:
            table_offset = None

        if table_offset is None or table_offset >= len(self.rom.data):
            return entries

        idx = 0
        offset = table_offset
        consecutive_invalid = 0
        # CFRU / Unbound expanded move table has at most 922 moves
        while idx <= 922 and offset + stride <= len(self.rom.data):
            raw = self.rom.data[offset:offset + stride]
            if raw == b"\xFF" * stride or raw == b"\x00" * stride:
                break
            text, _ = decode_gba_string(raw, use_kana=False)
            text = text.strip()
            if not is_valid_name(text):
                consecutive_invalid += 1
                if consecutive_invalid >= 2:
                    break
            else:
                consecutive_invalid = 0
                if text and text != "-" and not text.startswith("????"):
                    entries.append(TextEntry(
                        entry_id=f"move_{idx}",
                        category="moves",
                        offset=offset,
                        length=stride,
                        original_text=text,
                        translated_text=auto_translate_text(text, "moves") or "",
                        max_length=stride,
                        meta={"move_id": idx},
                    ))
            idx += 1
            offset += stride

        return entries

    # -----------------------------------------------------------------------
    # Items (44-byte struct)
    # -----------------------------------------------------------------------
    def scan_items(self) -> List[TextEntry]:
        entries = []
        struct_size = 44
        name_len = 14

        variants = [
            ["Master Ball", "Ultra Ball", "Great Ball"],
            ["MASTER BALL", "ULTRA BALL", "GREAT BALL"],
        ]
        found = self._find_string_sequence(variants, struct_size)
        if found is not None:
            table_offset = found - struct_size
        elif self.rom.is_firered():
            table_offset = 0x3DB028
        else:
            table_offset = None

        if table_offset is None or table_offset >= len(self.rom.data):
            return entries

        idx = 0
        offset = table_offset
        consecutive_invalid = 0
        while idx < 800 and offset + struct_size <= len(self.rom.data):
            name_raw = self.rom.data[offset:offset + name_len]
            if name_raw == b"\xFF" * name_len or name_raw == b"\x00" * name_len:
                break
            text, _ = decode_gba_string(name_raw, use_kana=False)
            text = text.strip()
            if not is_valid_name(text):
                consecutive_invalid += 1
                if consecutive_invalid >= 3:
                    break
            else:
                consecutive_invalid = 0
                if text and not text.startswith("????"):
                    desc_ptr_offset = offset + 20
                    desc_gba_ptr, desc_file_offset = self.rom.read_ptr(desc_ptr_offset)

                    entries.append(TextEntry(
                        entry_id=f"item_{idx}",
                        category="items",
                        offset=offset,
                        length=name_len,
                        original_text=text,
                        translated_text=auto_translate_text(text, "items") or "",
                        max_length=name_len,
                        meta={"item_id": idx, "desc_offset": desc_file_offset},
                    ))

                    # Extract description
                    if desc_file_offset and desc_file_offset < len(self.rom.data):
                        desc_text, desc_consumed = decode_gba_string(self.rom.data, desc_file_offset, max_len=160, use_kana=False)
                        desc_text = desc_text.strip()
                        if desc_text and not desc_text.startswith("????"):
                            entries.append(TextEntry(
                                entry_id=f"item_desc_{idx}",
                                category="item_descriptions",
                                offset=desc_file_offset,
                                length=desc_consumed,
                                original_text=desc_text,
                                translated_text=auto_translate_text(desc_text, "item_descriptions", item_name=text) or "",
                                pointer_offsets=[desc_ptr_offset],
                                meta={"item_id": idx, "item_name": text},
                            ))

            idx += 1
            offset += struct_size

        return entries

    # -----------------------------------------------------------------------
    # Move Descriptions Table (Pointers to strings)
    # -----------------------------------------------------------------------
    def scan_move_descriptions(self) -> List[TextEntry]:
        entries = []
        if not self.rom.is_firered():
            return entries

        table_offset = 0x482488
        if table_offset >= len(self.rom.data):
            return entries

        # Quick validation: check if the first 3 pointers actually point to descriptions
        valid_descs = 0
        for test_id in range(1, 4):
            ptr_offset = table_offset + (test_id * 4)
            if ptr_offset + 4 > len(self.rom.data):
                break
            ptr, file_offset = self.rom.read_ptr(ptr_offset)
            if file_offset and file_offset < len(self.rom.data):
                t, _ = decode_gba_string(self.rom.data, file_offset, max_len=180, use_kana=False)
                if is_valid_description(t):
                    valid_descs += 1
        if valid_descs == 0:
            return entries

        # Reads pointers for moves 1 to 500
        for move_id in range(1, 500):
            ptr_offset = table_offset + (move_id * 4)
            if ptr_offset + 4 > len(self.rom.data):
                break
            ptr, file_offset = self.rom.read_ptr(ptr_offset)
            if file_offset and file_offset < len(self.rom.data):
                desc_text, consumed = decode_gba_string(self.rom.data, file_offset, max_len=180, use_kana=False)
                desc_text = desc_text.strip()
                if is_valid_description(desc_text):
                    entries.append(TextEntry(
                        entry_id=f"move_desc_{move_id}",
                        category="move_descriptions",
                        offset=file_offset,
                        length=consumed,
                        original_text=desc_text,
                        translated_text="",
                        pointer_offsets=[ptr_offset],
                        meta={"move_id": move_id},
                    ))

        return entries

    # -----------------------------------------------------------------------
    # Abilities
    # -----------------------------------------------------------------------
    def scan_abilities(self) -> List[TextEntry]:
        entries = []
        variants = [
            ["Stench", "Drizzle", "Speed Boost"],
            ["STENCH", "DRIZZLE", "SPEED BOOST"],
        ]
        stride = 13
        table_offset = None

        # Check CFRU 17-byte stride first, then standard 13-byte stride
        for test_stride in [17, 13]:
            found = self._find_string_sequence(variants, test_stride)
            if found is not None:
                table_offset = found - test_stride
                stride = test_stride
                break

        if table_offset is None:
            if self.rom.is_firered():
                table_offset = 0x24FC40
                stride = 13
            elif self.rom.is_emerald():
                table_offset = 0x31BC8E
                stride = 13

        if table_offset is None or table_offset >= len(self.rom.data):
            return entries

        idx = 0
        offset = table_offset
        consecutive_invalid = 0
        while idx < 320 and offset + stride <= len(self.rom.data):
            raw = self.rom.data[offset:offset + stride]
            if raw == b"\xFF" * stride or raw == b"\x00" * stride:
                break
            text, _ = decode_gba_string(raw, use_kana=False)
            text = text.strip()
            if not is_valid_name(text):
                consecutive_invalid += 1
                if consecutive_invalid >= 2:
                    break
            else:
                consecutive_invalid = 0
                if text and text != "-------" and not text.startswith("????"):
                    entries.append(TextEntry(
                        entry_id=f"ability_{idx}",
                        category="abilities",
                        offset=offset,
                        length=stride,
                        original_text=text,
                        translated_text=auto_translate_text(text, "abilities") or "",
                        max_length=stride,
                        meta={"ability_id": idx},
                    ))
            idx += 1
            offset += stride

        return entries

    # -----------------------------------------------------------------------
    # Types
    # -----------------------------------------------------------------------
    def scan_types(self) -> List[TextEntry]:
        entries = []
        stride = 7
        variants = [
            ["Normal", "Fight", "Flying"],
            ["NORMAL", "FIGHT", "FLYING"],
        ]
        found = self._find_string_sequence(variants, stride)
        if found is not None:
            table_offset = found
        elif self.rom.is_firered():
            table_offset = 0x24F1A0
        else:
            table_offset = None

        if table_offset is None or table_offset >= len(self.rom.data):
            return entries

        idx = 0
        offset = table_offset
        while idx < 19 and offset + stride <= len(self.rom.data):
            raw = self.rom.data[offset:offset + stride]
            if raw == b"\xFF" * stride or raw == b"\x00" * stride:
                break
            text, _ = decode_gba_string(raw, use_kana=False)
            text = text.strip()
            if not is_valid_name(text):
                break
            if text:
                entries.append(TextEntry(
                    entry_id=f"type_{idx}",
                    category="types",
                    offset=offset,
                    length=stride,
                    original_text=text,
                    translated_text=auto_translate_text(text, "types") or "",
                    max_length=stride,
                    meta={"type_id": idx},
                ))
            idx += 1
            offset += stride

        return entries

    # -----------------------------------------------------------------------
    # Menus & Key UI Words
    # -----------------------------------------------------------------------
    def scan_menus(self) -> List[TextEntry]:
        entries = []
        menu_words = [
            "POKÉDEX", "POKÉMON", "BAG", "SAVE", "OPTION", "EXIT",
            "FIGHT", "RUN", "YES", "NO", "BUY", "SELL",
            "Pokedex", "Pokemon", "Bag", "Save", "Option", "Exit",
            "Fight", "Run", "Yes", "No", "Buy", "Sell",
            "Cancel", "CANCEL", "Items", "ITEMS", "Key Items", "KEY ITEMS",
            "Poké Balls", "POKÉ BALLS", "Use", "USE", "Give", "GIVE",
            "Toss", "TOSS", "Register", "REGISTER", "Take", "TAKE",
            "Summary", "SUMMARY", "Switch", "SWITCH",
            "Text Speed", "TEXT SPEED", "Battle Scene", "BATTLE SCENE",
            "Battle Style", "BATTLE STYLE", "Sound", "SOUND",
            "Button Mode", "BUTTON MODE", "Frame", "FRAME",
            "Slow", "SLOW", "Mid", "MID", "Fast", "FAST",
            "Shift", "SHIFT", "Set", "SET", "Mono", "MONO", "Stereo", "STEREO",
            "Pokémon Info", "POKÉMON INFO", "Pokémon Skills", "POKÉMON SKILLS",
            "Known Moves", "KNOWN MOVES", "CONTROLS",
        ]

        seen_offsets = set()
        for i, word in enumerate(menu_words):
            encoded = encode_gba_string(word, use_kana=False)
            start = 0
            count = 0
            while count < 6:
                idx = self.rom.data.find(encoded, start)
                if idx == -1:
                    break
                if idx not in seen_offsets and (idx == 0 or self.rom.data[idx - 1] in (0xFF, 0x00)):
                    ptrs = self.rom.find_all_pointers_to(idx)
                    if ptrs:
                        seen_offsets.add(idx)
                        entries.append(TextEntry(
                            entry_id=f"menu_{i}_{count}",
                            category="menu",
                            offset=idx,
                            length=len(encoded),
                            original_text=word,
                            translated_text=auto_translate_text(word, "menu") or "",
                            pointer_offsets=ptrs,
                            meta={"menu_word": word},
                        ))
                        count += 1
                start = idx + 1

        return entries

    # -----------------------------------------------------------------------
    # Dialogues and Scripts
    # -----------------------------------------------------------------------
    def scan_dialogues(self, limit: int = 10000, exclude_offsets: Optional[set] = None) -> List[TextEntry]:
        """Scans the ROM for authentic script dialogue strings referenced by 32-bit pointers
        (both 4-byte aligned C pointers and unaligned XSE/overworld event script pointers).
        Prioritizes custom ROM hack strings (>= 0x700000), C intro pointers, and core UI tables.
        """
        data = self.rom.data
        data_len = len(data)
        max_scan = min(data_len, 0x1A00000)
        raw_scan = bytes(data[:max_scan])
        excluded = set(exclude_offsets) if exclude_offsets else set()

        # Group candidate pointers by their string terminator (term_idx) so substring pointers
        # inside the same dialogue never overwrite the earliest valid start offset.
        by_term: Dict[int, Tuple[int, int, str, int]] = {}

        for m in re.finditer(rb"[\x10-\xFF][\x08\x09]", raw_scan):
            p_offset = m.start() - 2
            if p_offset < 0x010000:
                continue
            # Allow 4-byte aligned C pointers anywhere, or unaligned script pointers in >= 0x150000
            if p_offset % 4 != 0 and p_offset < 0x150000:
                continue

            ptr = int.from_bytes(raw_scan[p_offset:p_offset + 4], "little")
            file_offset = ptr - 0x08000000
            if file_offset < 0x100000 or file_offset >= data_len - 10 or file_offset in excluded:
                continue

            first_byte = data[file_offset]
            if not (0xA1 <= first_byte <= 0xEE or first_byte in (0x00, 0x2D, 0x2E, 0xB0, 0xB3, 0xB4, 0xFC, 0xFD)):
                continue
            # Reject mid-word / mid-sentence false pointers (preceded by an ASCII letter/digit/punctuation)
            if 0xA1 <= data[file_offset - 1] <= 0xEE:
                continue

            term_idx = data.find(b"\xFF", file_offset, file_offset + 800)
            if term_idx == -1 or (term_idx - file_offset) < 8 or term_idx in excluded:
                continue

            if term_idx in by_term and file_offset >= by_term[term_idx][0]:
                continue

            raw_str = data[file_offset:term_idx + 1]
            text, consumed = decode_gba_string(raw_str, use_kana=False)
            text = text.strip()
            if is_real_english_dialogue(text):
                by_term[term_idx] = (file_offset, p_offset, text, consumed)

        # Sort so custom ROM hack strings (>= 0x700000), C intro pointers (< 0x160000),
        # and core UI/menu descriptions (0x416000..0x41A600) are always included first.
        def _priority_key(item: Tuple[int, int, str, int]) -> Tuple[int, int]:
            file_offset, p_offset, _, _ = item
            if file_offset >= 0x700000 or p_offset < 0x160000 or (0x416000 <= file_offset <= 0x41A600):
                return (0, file_offset)
            return (1, file_offset)

        sorted_items = sorted(by_term.values(), key=_priority_key)[:limit]
        # Resort selected entries by file_offset for clean sequential order
        sorted_items.sort(key=lambda x: x[0])

        entries: List[TextEntry] = []
        for idx, (file_offset, p_offset, text, consumed) in enumerate(sorted_items):
            trans = auto_translate_text(text, category="dialogue", allow_online=False) or ""
            entries.append(TextEntry(
                entry_id=f"dialogue_{idx}",
                category="dialogue",
                offset=file_offset,
                length=consumed,
                original_text=text,
                translated_text=trans,
                pointer_offsets=[p_offset],
            ))

        return entries


class TableInjector:
    """Injects translated text entries back into the GBA ROM."""

    def __init__(self, rom: GbaRom):
        self.rom = rom

    def inject_entry(self, entry: TextEntry, use_kana: bool = True) -> int:
        """Injects a single translated text entry into the ROM."""
        text_to_write = entry.translated_text if entry.translated_text.strip() else entry.original_text
        if not text_to_write:
            return entry.offset

        # Fixed-length table entries (species, moves, items, etc.)
        if entry.max_length is not None:
            encoded = encode_gba_string(text_to_write, use_kana=use_kana, pad_to_len=entry.max_length)
            self.rom.data[entry.offset:entry.offset + len(encoded)] = encoded
            return entry.offset

        # Auto-wrap dialogue lines so they fit inside the 2-line GBA dialogue window
        if entry.category == "dialogue" and use_kana:
            text_to_write = format_gba_dialogue(text_to_write, original_text=entry.original_text)

        # Pointer-referenced strings (descriptions, dialogues, menus)
        encoded = encode_gba_string(text_to_write, use_kana=use_kana)
        new_offset = self.rom.write_string_with_repoint(entry.offset, entry.length, encoded)
        return new_offset

    def inject_all(self, entries: List[TextEntry], use_kana: bool = True) -> Dict[str, int]:
        """Injects all entries into the ROM and updates header checksum."""
        modified_count = 0
        repointed_count = 0

        for entry in entries:
            if entry.translated_text and entry.translated_text != entry.original_text:
                new_offset = self.inject_entry(entry, use_kana=use_kana)
                modified_count += 1
                if new_offset != entry.offset:
                    repointed_count += 1

        # Sanitize any remaining English 'Poké' (0x1B = 'é' in EN, 'ひ' in JP) or 'POKÉ' (0x06 = 'É' in EN, 'う' in JP)
        # in the ROM data section (>= 0x160000) so 'Pokひmon' never appears even in fallback strings.
        if use_kana and len(self.rom.data) > 0x160000:
            for pattern, repl in ((b"\xCA\xE3\xDF\x1B", b"\xCA\xE3\xDF\xD9"), (b"\xCA\xC9\xC5\x06", b"\xCA\xC9\xC5\xBF")):
                pos = 0x160000
                while True:
                    idx = self.rom.data.find(pattern, pos)
                    if idx == -1:
                        break
                    self.rom.data[idx:idx + 4] = repl
                    pos = idx + 4

        self.rom.fix_header_checksum()
        return {
            "total_entries": len(entries),
            "modified": modified_count,
            "repointed": repointed_count,
        }
