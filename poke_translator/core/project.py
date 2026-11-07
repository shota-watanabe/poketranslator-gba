"""Project management for saving, loading, and exporting translation sessions."""

import json
import csv
import datetime
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from .table_scanner import TextEntry
from .dictionary import auto_translate_text, translate_online_batch
from .dialogue_data import convert_kanji_to_kana
from .charmap import hiragana_to_katakana


class TranslationProject:
    """Represents a translation project session for a GBA Pokemon ROM."""

    def __init__(
        self,
        name: str = "Untitled Project",
        rom_filename: str = "",
        game_title: str = "",
        game_code: str = "",
        engine: str = "",
        entries: Optional[List[TextEntry]] = None,
        patch_font: bool = True,
        char_width: int = 9,
    ):
        self.name = name
        self.rom_filename = rom_filename
        self.game_title = game_title
        self.game_code = game_code
        self.engine = engine
        self.entries: List[TextEntry] = entries or []
        self.patch_font = patch_font
        self.char_width = char_width
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at

    def get_stats(self) -> Dict[str, Any]:
        """Calculates project translation statistics."""
        total = len(self.entries)
        translated = sum(1 for e in self.entries if e.translated_text.strip())
        percentage = round((translated / total * 100), 1) if total > 0 else 0.0

        by_cat: Dict[str, Dict[str, int]] = {}
        for e in self.entries:
            cat = e.category
            if cat not in by_cat:
                by_cat[cat] = {"total": 0, "translated": 0}
            by_cat[cat]["total"] += 1
            if e.translated_text.strip():
                by_cat[cat]["translated"] += 1

        return {
            "total_entries": total,
            "translated_entries": translated,
            "completion_percentage": percentage,
            "by_category": by_cat,
        }

    def auto_translate_all(
        self,
        overwrite: bool = False,
        use_machine_translation: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> int:
        """Applies built-in dictionary, patterns, and natural machine translations to all entries.
        
        Args:
            overwrite: If True, re-translates already translated entries.
            use_machine_translation: If True, uses fallback machine translation for missing terms.
            progress_callback: Optional callback func(current, total, detail_msg) for live UI tracking.

        Returns count of newly translated entries.
        """
        count = 0
        total = len(self.entries)
        if total == 0:
            if progress_callback:
                progress_callback(0, 0, "項目がありません")
            return 0

        # Phase 1: High-speed dictionary & algorithmic pattern translation
        processed = 0
        for i, e in enumerate(self.entries):
            processed += 1
            if progress_callback and (i % 10 == 0 or i == total - 1):
                progress_callback(processed, total, f"辞書照合 [{e.category}]: {e.original_text[:25]}")

            if not overwrite and e.translated_text.strip():
                continue
            item_name = e.meta.get("item_name", "") if e.category == "item_descriptions" else ""
            translated = auto_translate_text(e.original_text, e.category, allow_online=False, item_name=item_name)
            if translated:
                e.translated_text = translated
                count += 1

        # Phase 2: High-speed batch machine translation for remaining entries (dialogues, custom descriptions)
        if use_machine_translation:
            untranslated = [e for e in self.entries if not e.translated_text.strip()]
            if untranslated:
                total_ops = total + len(untranslated)
                batch_size = 20
                batches = [untranslated[b_start : b_start + batch_size] for b_start in range(0, len(untranslated), batch_size)]
                processed = total

                def _run_batch(batch_entries: List[TextEntry]) -> List[Optional[str]]:
                    return translate_online_batch([e.original_text for e in batch_entries])

                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    future_to_batch = {executor.submit(_run_batch, b): b for b in batches}
                    done_items = 0
                    for future in concurrent.futures.as_completed(future_to_batch):
                        batch = future_to_batch[future]
                        batch_results = future.result()
                        done_items += len(batch)
                        processed += len(batch)
                        if progress_callback:
                            progress_callback(
                                processed,
                                total_ops,
                                f"API一括翻訳 ({done_items}/{len(untranslated)}): {batch[0].original_text[:20]}...",
                            )
                        for e, trans in zip(batch, batch_results):
                            if trans:
                                kana_trans = convert_kanji_to_kana(trans)
                                e.translated_text = hiragana_to_katakana(kana_trans) if self.engine == "katakana" else kana_trans
                                count += 1
            else:
                total_ops = total
        else:
            total_ops = total

        if progress_callback:
            progress_callback(total_ops, total_ops, "すべての項目の翻訳が完了しました")

        self.updated_at = datetime.datetime.now().isoformat()
        return count

    def save_to_file(self, path: str) -> None:
        """Saves project to a JSON file."""
        self.updated_at = datetime.datetime.now().isoformat()
        data = {
            "name": self.name,
            "rom_filename": self.rom_filename,
            "game_title": self.game_title,
            "game_code": self.game_code,
            "engine": self.engine,
            "patch_font": self.patch_font,
            "char_width": self.char_width,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "entries": [e.to_dict() for e in self.entries],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, path: str) -> "TranslationProject":
        """Loads project from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = [TextEntry.from_dict(d) for d in data.get("entries", [])]
        proj = cls(
            name=data.get("name", "Untitled Project"),
            rom_filename=data.get("rom_filename", ""),
            game_title=data.get("game_title", ""),
            game_code=data.get("game_code", ""),
            engine=data.get("engine", ""),
            entries=entries,
            patch_font=data.get("patch_font", True),
            char_width=data.get("char_width", 9),
        )
        proj.created_at = data.get("created_at", "")
        proj.updated_at = data.get("updated_at", "")
        return proj

    def export_csv(self, path: str) -> None:
        """Exports entries to CSV for external editing in Excel / Google Sheets."""
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Category", "Offset", "Original Text", "Translated Text", "Max Length"])
            for e in self.entries:
                writer.writerow([
                    e.entry_id,
                    e.category,
                    f"0x{e.offset:X}",
                    e.original_text,
                    e.translated_text,
                    e.max_length or "",
                ])

    def import_csv(self, path: str) -> int:
        """Imports translated text from CSV by matching entry IDs.
        
        Returns number of updated entries.
        """
        entry_map = {e.entry_id: e for e in self.entries}
        updated = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                e_id = row.get("ID")
                trans = row.get("Translated Text", "").strip()
                if e_id and e_id in entry_map and trans:
                    entry_map[e_id].translated_text = trans
                    updated += 1
        self.updated_at = datetime.datetime.now().isoformat()
        return updated
