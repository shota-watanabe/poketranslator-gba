"""Unit tests for PokeTranslator GBA core modules."""

import unittest
from poke_translator.core.charmap import (
    encode_gba_string,
    decode_gba_string,
    hiragana_to_katakana,
    KANA_CHAR_TO_BYTE,
)
from poke_translator.core.rom import GbaRom
from poke_translator.core.dictionary import auto_translate_text, normalize_key
from poke_translator.core.font_patcher import (
    KANA_DOT_PATTERNS,
    pattern_to_2bpp_glyph,
    patch_kana_font,
)
from poke_translator.core.project import TranslationProject
from poke_translator.core.table_scanner import TextEntry


class TestPokeTranslatorCore(unittest.TestCase):

    def test_charmap_english_roundtrip(self):
        original = "POUND"
        encoded = encode_gba_string(original, use_kana=False)
        self.assertTrue(encoded.endswith(b"\xFF"))
        decoded, _ = decode_gba_string(encoded, use_kana=False)
        self.assertEqual(decoded, original)

    def test_charmap_control_codes(self):
        text = "Hello[WAIT]\nWorld[PLAYER]!"
        encoded = encode_gba_string(text, use_kana=False)
        decoded, _ = decode_gba_string(encoded, use_kana=False)
        self.assertEqual(decoded, text)

    def test_charmap_kana_encoding(self):
        # "ピカチュウ" should encode using KANA_CHAR_TO_BYTE
        kana_text = "ピカチュウ"
        encoded = encode_gba_string(kana_text, use_kana=True)
        self.assertTrue(len(encoded) > 0)
        self.assertEqual(encoded[-1], 0xFF)
        decoded, _ = decode_gba_string(encoded, use_kana=True)
        self.assertEqual(decoded, kana_text)

    def test_hiragana_transliteration(self):
        hira = "たいあたり"
        kata = hiragana_to_katakana(hira)
        self.assertEqual(kata, "タイアタリ")

    def test_dictionary_lookups(self):
        self.assertEqual(auto_translate_text("BULBASAUR", "species"), "フシギダネ")
        self.assertEqual(auto_translate_text("POUND", "moves"), "はたく")
        self.assertEqual(auto_translate_text("MASTER BALL", "items"), "マスターボール")
        self.assertEqual(auto_translate_text("OVERGROW", "abilities"), "しんりょく")
        self.assertEqual(auto_translate_text("FIRE", "types"), "ほのお")
        self.assertEqual(auto_translate_text("FIGHT", "menu"), "たたかう")
        self.assertEqual(auto_translate_text("POKÉMON", "menu"), "ポケモン")

    def test_fuzzy_normalization_and_mega_stones(self):
        # TitleCase and hyphens
        self.assertEqual(auto_translate_text("Headbutt", "moves"), "ずつき")
        self.assertEqual(auto_translate_text("Sand-Attack", "moves"), "すなかけ")
        self.assertEqual(auto_translate_text("Wrap", "moves"), "まきつく")
        self.assertEqual(auto_translate_text("Megahorn", "moves"), "メガホーン")

        # Mega Stones
        self.assertEqual(auto_translate_text("Mawilite", "items"), "クチートナイト")
        self.assertEqual(auto_translate_text("Charizite X", "items"), "リザードナイトX")
        self.assertEqual(auto_translate_text("Blastoisite", "items"), "カメックスナイト")

        # Gen 4-9 Species
        self.assertEqual(auto_translate_text("Turtwig", "species"), "ナエトル")
        self.assertEqual(auto_translate_text("Rowlet", "species"), "モクロー")
        self.assertEqual(auto_translate_text("Sprigatito", "species"), "ニャオハ")
        self.assertEqual(auto_translate_text("Bad Egg", "species"), "ダメタマゴ")
        self.assertEqual(auto_translate_text("Unown B", "species"), "アンノーンB")

        # Item Descriptions by context
        desc = "A spray-type medicine.\nIt heals one Pokémon from a\npoisoning."
        self.assertEqual(auto_translate_text(desc, "item_descriptions", item_name="Antidote"), "ポケモン1ぴきの どくを\nなおす くすり。")

    def test_rom_header_and_checksum(self):
        # Create a mock 16MB GBA ROM
        mock_data = bytearray(b"\x00" * (16 * 1024 * 1024))
        # Game title at 0xA0
        mock_data[0xA0:0xAC] = b"POKEMON FIRE"
        # Game code at 0xAC
        mock_data[0xAC:0xB0] = b"BPRE"
        mock_data[0xB0:0xB2] = b"01"
        mock_data[0xB2] = 0x96

        rom = GbaRom(bytes(mock_data), filename="test.gba")
        self.assertEqual(rom.game_title, "POKEMON FIRE")
        self.assertEqual(rom.game_code, "BPRE")
        self.assertTrue(rom.is_firered())

        # Checksum repair
        rom.fix_header_checksum()
        self.assertEqual(rom.header_checksum, rom.calculate_header_checksum())

    def test_rom_expansion_and_repoint(self):
        mock_data = bytearray(b"\x00" * (16 * 1024 * 1024))
        mock_data[0xAC:0xB0] = b"BPRE"
        rom = GbaRom(bytes(mock_data), filename="test.gba")

        # Test pointer write and read
        rom.write_ptr(0x1000, 0x5000)
        gba_ptr, file_offset = rom.read_ptr(0x1000)
        self.assertEqual(gba_ptr, 0x08005000)
        self.assertEqual(file_offset, 0x5000)

        # Repoint
        ptrs = rom.find_all_pointers_to(0x5000)
        self.assertIn(0x1000, ptrs)

        rom.repoint(0x5000, 0x9000)
        _, new_target = rom.read_ptr(0x1000)
        self.assertEqual(new_target, 0x9000)

        # Expand to 32MB
        rom.expand_to_32mb()
        self.assertEqual(len(rom.data), 32 * 1024 * 1024)

    def test_font_patcher_glyph_generator(self):
        self.assertIn('ア', KANA_DOT_PATTERNS)
        pattern = KANA_DOT_PATTERNS['ア']
        glyph64 = pattern_to_2bpp_glyph(pattern, glyph_size=64)
        self.assertEqual(len(glyph64), 64)
        glyph32 = pattern_to_2bpp_glyph(pattern, glyph_size=32)
        self.assertEqual(len(glyph32), 32)

    def test_dialogue_translation_and_kanji_conversion(self):
        from poke_translator.core.dialogue_data import convert_kanji_to_kana

        # Kanji to Kana conversion
        kanji_text = "不思議な世界へようこそ！冒険に出発しよう！"
        kana_result = convert_kanji_to_kana(kanji_text)
        self.assertEqual(kana_result, "ふしぎなせかいへようこそ！ぼうけんにしゅっぱつしよう！")

        # Intro dialogues
        intro1 = "In the world which you are about to enter, you will embark on a grand adventure with you as the hero."
        trans1 = auto_translate_text(intro1, "dialogue")
        self.assertIsNotNone(trans1)
        self.assertIn("ぼうけん", trans1)

        intro2 = "Welcome to the wonderful world of Pokémon!\nThe name's Redwood!"
        trans2 = auto_translate_text(intro2, "dialogue")
        self.assertIsNotNone(trans2)
        self.assertIn("レッドウッド", trans2)

        # Bag & Mart dialogues
        bag1 = "Where should the [BUFFER_2] be placed?"
        self.assertEqual(auto_translate_text(bag1, "dialogue"), "[BUFFER_2]を どこに おきますか？")

        bag2 = "Toss out how many [BUFFER_2]?"
        self.assertEqual(auto_translate_text(bag2, "dialogue"), "[BUFFER_2]を いくつ すてますか？")

        # Speaker mapping
        nurse_line = "Nurse: Welcome to our Pokémon Center! Would you like me to heal your Pokémon?"
        nurse_trans = auto_translate_text(nurse_line, "dialogue")
        self.assertIsNotNone(nurse_trans)
        self.assertTrue(nurse_trans.startswith("ジョーイ「"))

    def test_project_stats_and_auto_translate(self):
        entries = [
            TextEntry("sp_1", "species", 0x100, 11, "BULBASAUR"),
            TextEntry("mv_1", "moves", 0x200, 13, "POUND"),
            TextEntry("custom_1", "dialogue", 0x300, 20, "Hello random world"),
        ]
        proj = TranslationProject(entries=entries)
        stats = proj.get_stats()
        self.assertEqual(stats["total_entries"], 3)
        self.assertEqual(stats["translated_entries"], 0)

        new_count = proj.auto_translate_all()
        self.assertEqual(new_count, 2)
        self.assertEqual(entries[0].translated_text, "フシギダネ")
        self.assertEqual(entries[1].translated_text, "はたく")


if __name__ == "__main__":
    unittest.main()
