"""Lightweight HTTP Server providing Web Studio for PokeTranslator GBA.
Uses standard library http.server for zero external dependencies on macOS.
"""

import http.server
import json
import os
import urllib.parse
import webbrowser
import mimetypes
import time
import threading
from typing import Optional, Dict, Any

from ..core.rom import GbaRom
from ..core.table_scanner import TableScanner, TableInjector
from ..core.font_patcher import patch_kana_font, KANA_DOT_PATTERNS
from ..core.project import TranslationProject
from ..core.dictionary import auto_translate_text

# Global active session
CURRENT_ROM: Optional[GbaRom] = None
CURRENT_PROJECT: Optional[TranslationProject] = None

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Thread-safe progress tracking for long operations
PROGRESS_LOCK = threading.Lock()
PROGRESS_STATE: Dict[str, Any] = {
    "active": False,
    "task": "",
    "title": "",
    "detail": "",
    "current": 0,
    "total": 0,
    "percentage": 0.0,
    "start_time": 0.0,
    "elapsed_seconds": 0.0,
    "speed": 0.0,
    "eta_seconds": 0.0,
    "finished": False,
    "error": None,
}


def set_progress(
    task: str,
    title: str,
    current: int,
    total: int,
    detail: str = "",
    start_time: Optional[float] = None,
    finished: bool = False,
    error: Optional[str] = None,
) -> None:
    """Updates global progress state safely across threads."""
    with PROGRESS_LOCK:
        now = time.time()
        st = start_time if start_time is not None else PROGRESS_STATE.get("start_time", now)
        if not st or st <= 0:
            st = now
        elapsed = max(0.001, now - st)
        pct = round((current / total * 100), 1) if total > 0 else (100.0 if finished else 0.0)
        speed = round(current / elapsed, 1) if current > 0 else 0.0
        eta = max(0.0, (total - current) / speed) if speed > 0 and current < total else 0.0

        PROGRESS_STATE.update({
            "active": not finished and error is None,
            "task": task,
            "title": title,
            "detail": detail,
            "current": current,
            "total": total,
            "percentage": min(100.0, max(0.0, pct)),
            "start_time": st,
            "elapsed_seconds": round(elapsed, 1),
            "speed": speed,
            "eta_seconds": round(eta, 1),
            "finished": finished,
            "error": error,
        })


def get_progress() -> Dict[str, Any]:
    """Retrieves a thread-safe copy of current progress with dynamic elapsed/ETA updates."""
    with PROGRESS_LOCK:
        state = dict(PROGRESS_STATE)
        if state["active"] and state.get("start_time", 0) > 0:
            now = time.time()
            elapsed = max(0.001, now - state["start_time"])
            state["elapsed_seconds"] = round(elapsed, 1)
            current = state["current"]
            total = state["total"]
            speed = round(current / elapsed, 1) if current > 0 else 0.0
            eta = max(0.0, (total - current) / speed) if speed > 0 and current < total else 0.0
            state["speed"] = speed
            state["eta_seconds"] = round(eta, 1)
        return state


class StudioHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for PokeTranslator Web Studio."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard request logging to keep console clean."""
        pass

    def send_json(self, data: Any, status: int = 200) -> None:
        """Sends a JSON response."""
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def send_binary(self, data: bytes, filename: str, content_type: str = "application/octet-stream") -> None:
        """Sends binary data download."""
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        """CORS preflight handler."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Static assets
        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
            return
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                self.serve_file(file_path, mime or "application/octet-stream")
                return
            else:
                self.send_error(404, "File Not Found")
                return

        # API Endpoints
        if path == "/api/status":
            global CURRENT_ROM, CURRENT_PROJECT
            loaded = CURRENT_ROM is not None and CURRENT_PROJECT is not None
            resp = {
                "loaded": loaded,
                "project": CURRENT_PROJECT.get_stats() if loaded and CURRENT_PROJECT else None,
                "rom_info": {
                    "filename": CURRENT_ROM.filename if CURRENT_ROM else "",
                    "title": CURRENT_ROM.game_title if CURRENT_ROM else "",
                    "code": CURRENT_ROM.game_code if CURRENT_ROM else "",
                    "engine": CURRENT_ROM.detect_engine() if CURRENT_ROM else "",
                    "size_mb": round(len(CURRENT_ROM.data) / (1024 * 1024), 2) if CURRENT_ROM else 0,
                } if CURRENT_ROM else None,
            }
            self.send_json(resp)
            return

        elif path == "/api/entries":
            if not CURRENT_PROJECT:
                self.send_json({"error": "No ROM loaded"}, status=400)
                return

            category = query.get("category", ["all"])[0]
            search = query.get("search", [""])[0].lower()
            page = int(query.get("page", [1])[0])
            page_size = int(query.get("page_size", [50])[0])

            filtered = CURRENT_PROJECT.entries
            if category != "all":
                filtered = [e for e in filtered if e.category == category]

            if search:
                filtered = [
                    e for e in filtered
                    if search in e.original_text.lower() or search in e.translated_text.lower()
                ]

            total_matches = len(filtered)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_items = filtered[start_idx:end_idx]

            self.send_json({
                "total": total_matches,
                "page": page,
                "page_size": page_size,
                "entries": [e.to_dict() for e in page_items],
            })
            return

        elif path == "/api/font_preview":
            # Return list of Kana dot matrix patterns
            preview = {}
            for char, pattern in KANA_DOT_PATTERNS.items():
                preview[char] = pattern
            self.send_json({"kana": preview})
            return

        elif path == "/api/sample_roms":
            sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data"))
            samples = []
            if os.path.exists(sample_dir):
                for f in sorted(os.listdir(sample_dir)):
                    if f.endswith(".gba"):
                        full_path = os.path.join(sample_dir, f)
                        samples.append({
                            "filename": f,
                            "path": full_path,
                            "size_mb": round(os.path.getsize(full_path) / (1024 * 1024), 1)
                        })
            self.send_json({"samples": samples})
            return

        elif path == "/api/progress":
            self.send_json(get_progress())
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        global CURRENT_ROM, CURRENT_PROJECT

        if path == "/api/upload_rom":
            st = time.time()
            set_progress("upload_rom", "ROM解析 & テキスト抽出中", 1, 3, "ROMデータヘッダー検証中...", start_time=st)
            try:
                # Can be raw binary or multipart or json with path
                if self.headers.get("Content-Type", "").startswith("application/json"):
                    req = json.loads(body.decode("utf-8"))
                    rom_path = req.get("path")
                    if not rom_path or not os.path.exists(rom_path):
                        set_progress("upload_rom", "エラー", 0, 1, "ファイルが存在しません", finished=True, error="File does not exist")
                        self.send_json({"error": "File does not exist"}, status=400)
                        return
                    CURRENT_ROM = GbaRom.load(rom_path)
                else:
                    # Raw file upload
                    CURRENT_ROM = GbaRom(body, filename="uploaded.gba")

                set_progress("upload_rom", "ROM解析 & テキスト抽出中", 2, 3, "ゲーム内テキストテーブル走査中...", start_time=st)
                scanner = TableScanner(CURRENT_ROM)
                entries = scanner.scan_all(include_dialogues=True)

                CURRENT_PROJECT = TranslationProject(
                    name=os.path.splitext(CURRENT_ROM.filename)[0],
                    rom_filename=CURRENT_ROM.filename,
                    game_title=CURRENT_ROM.game_title,
                    game_code=CURRENT_ROM.game_code,
                    engine=CURRENT_ROM.detect_engine(),
                    entries=entries,
                )
                set_progress("upload_rom", "ROM解析完了", 3, 3, f"{len(entries)} 項目のテキストを抽出しました", start_time=st, finished=True)

                self.send_json({
                    "status": "success",
                    "rom_info": {
                        "filename": CURRENT_ROM.filename,
                        "title": CURRENT_ROM.game_title,
                        "code": CURRENT_ROM.game_code,
                        "engine": CURRENT_ROM.detect_engine(),
                        "size_mb": round(len(CURRENT_ROM.data) / (1024 * 1024), 2),
                    },
                    "stats": CURRENT_PROJECT.get_stats(),
                })
            except Exception as e:
                set_progress("upload_rom", "エラー", 0, 1, str(e), finished=True, error=str(e))
                self.send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/update_entry":
            if not CURRENT_PROJECT:
                self.send_json({"error": "No project active"}, status=400)
                return
            req = json.loads(body.decode("utf-8"))
            e_id = req.get("id")
            trans = req.get("translated", "")

            found = False
            for e in CURRENT_PROJECT.entries:
                if e.entry_id == e_id:
                    e.translated_text = trans
                    found = True
                    break

            if found:
                self.send_json({"status": "updated", "id": e_id, "translated": trans})
            else:
                self.send_json({"error": "Entry not found"}, status=404)
            return

        elif path == "/api/load_sample":
            st = time.time()
            try:
                req = json.loads(body.decode("utf-8")) if body else {}
                sample_name = req.get("filename", "")
                sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data"))
                target_path = os.path.join(sample_dir, sample_name)
                if not os.path.exists(target_path):
                    set_progress("load_sample", "エラー", 0, 1, f"サンプルROMが見つかりません: {sample_name}", finished=True, error="Not found")
                    self.send_json({"error": f"Sample ROM not found: {sample_name}"}, status=404)
                    return
                set_progress("load_sample", f"サンプルROM読み込み: {sample_name}", 1, 4, "ROMバイナリ読み込み中...", start_time=st)
                CURRENT_ROM = GbaRom.load(target_path)
                set_progress("load_sample", f"サンプルROM読み込み: {sample_name}", 2, 4, f"エンジン判定中: {CURRENT_ROM.detect_engine()}", start_time=st)
                scanner = TableScanner(CURRENT_ROM)
                entries = scanner.scan_all(include_dialogues=True)
                set_progress("load_sample", f"サンプルROM読み込み: {sample_name}", 3, 4, f"テーブル走査完了 ({len(entries)} 項目)", start_time=st)
                CURRENT_PROJECT = TranslationProject(
                    name=os.path.splitext(sample_name)[0],
                    rom_filename=sample_name,
                    game_title=CURRENT_ROM.game_title,
                    game_code=CURRENT_ROM.game_code,
                    engine=CURRENT_ROM.detect_engine(),
                    entries=entries,
                )
                set_progress("load_sample", f"サンプルROM読み込み完了: {sample_name}", 4, 4, f"{len(entries)} 項目の解析が完了しました", start_time=st, finished=True)
                self.send_json({
                    "status": "success",
                    "rom_info": {
                        "filename": CURRENT_ROM.filename,
                        "title": CURRENT_ROM.game_title,
                        "code": CURRENT_ROM.game_code,
                        "engine": CURRENT_ROM.detect_engine(),
                        "size_mb": round(len(CURRENT_ROM.data) / (1024 * 1024), 2),
                    },
                    "stats": CURRENT_PROJECT.get_stats(),
                })
            except Exception as e:
                set_progress("load_sample", "エラー", 0, 1, str(e), finished=True, error=str(e))
                self.send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/auto_translate":
            if not CURRENT_PROJECT:
                self.send_json({"error": "No project active"}, status=400)
                return
            req = json.loads(body.decode("utf-8")) if body else {}
            overwrite = req.get("overwrite", False)
            use_mt = req.get("use_machine_translation", True)

            st = time.time()
            total_items = len(CURRENT_PROJECT.entries)
            set_progress("auto_translate", "100%全自動翻訳を実行中", 0, total_items, "辞書および翻訳エンジンを初期化中...", start_time=st)

            def on_progress(cur: int, tot: int, msg: str) -> None:
                set_progress("auto_translate", "100%全自動翻訳を実行中", cur, tot, msg, start_time=st)

            count = CURRENT_PROJECT.auto_translate_all(
                overwrite=overwrite,
                use_machine_translation=use_mt,
                progress_callback=on_progress,
            )
            set_progress("auto_translate", "100%全自動翻訳完了", total_items, total_items, f"{count} 項目を新たに翻訳しました", start_time=st, finished=True)

            self.send_json({
                "status": "success",
                "translated_count": count,
                "stats": CURRENT_PROJECT.get_stats(),
            })
            return

        elif path == "/api/build_rom":
            if not CURRENT_ROM or not CURRENT_PROJECT:
                self.send_json({"error": "No active ROM/project"}, status=400)
                return

            req = json.loads(body.decode("utf-8")) if body else {}
            patch_font = req.get("patch_font", CURRENT_PROJECT.patch_font)

            st = time.time()
            set_progress("build_rom", "日本語版GBA ROM出力中", 1, 4, "ROMクローンデータ作成中...", start_time=st)

            # Build in a fresh copy of ROM data
            export_rom = GbaRom(CURRENT_ROM.original_data, filename=CURRENT_ROM.filename)

            # Patch font if requested
            if patch_font:
                set_progress("build_rom", "日本語版GBA ROM出力中", 2, 4, "8x12 日本語カナフォント注入中...", start_time=st)
                patch_kana_font(export_rom, char_width=CURRENT_PROJECT.char_width)

            # Inject translated text entries
            set_progress("build_rom", "日本語版GBA ROM出力中", 3, 4, f"翻訳テキストバイナリ注入中 ({len(CURRENT_PROJECT.entries)} 項目)...", start_time=st)
            injector = TableInjector(export_rom)
            inj_res = injector.inject_all(CURRENT_PROJECT.entries, use_kana=True)
            export_rom.fix_header_checksum()

            set_progress("build_rom", "日本語版GBA ROM出力完了", 4, 4, "ROMバイナリ生成完了。ダウンロードを開始します", start_time=st, finished=True)

            # Output filename
            base_name = os.path.splitext(CURRENT_ROM.filename)[0]
            out_name = f"{base_name}_JP.gba"

            self.send_binary(bytes(export_rom.data), filename=out_name)
            return

        elif path == "/api/build_ips":
            if not CURRENT_ROM or not CURRENT_PROJECT:
                self.send_json({"error": "No active ROM/project"}, status=400)
                return

            st = time.time()
            set_progress("build_ips", "IPSパッチ生成中", 1, 4, "テキスト＆フォント注入中...", start_time=st)

            export_rom = GbaRom(CURRENT_ROM.original_data, filename=CURRENT_ROM.filename)
            if CURRENT_PROJECT.patch_font:
                patch_kana_font(export_rom, char_width=CURRENT_PROJECT.char_width)
            injector = TableInjector(export_rom)
            injector.inject_all(CURRENT_PROJECT.entries, use_kana=True)
            export_rom.fix_header_checksum()

            set_progress("build_ips", "IPSパッチ生成中", 2, 4, "差分ブロック計算中...", start_time=st)
            ips_patch = export_rom.create_ips_patch()

            set_progress("build_ips", "IPSパッチ生成完了", 4, 4, "IPSパッチ完成。ダウンロードを開始します", start_time=st, finished=True)
            base_name = os.path.splitext(CURRENT_ROM.filename)[0]
            self.send_binary(ips_patch, filename=f"{base_name}_JP.ips")
            return

        self.send_error(404, "Not Found")

    def serve_file(self, path: str, content_type: str) -> None:
        """Serves a static file from disk."""
        try:
            with open(path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_error(500, "Error reading file")


def start_web_studio(port: int = 8080, open_browser: bool = True) -> None:
    """Starts the Web Studio server and optionally launches browser."""
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    server_address = ("127.0.0.1", port)

    with http.server.ThreadingHTTPServer(server_address, StudioHandler) as httpd:
        url = f"http://127.0.0.1:{port}"
        print("\n" + "=" * 65)
        print("  PokeTranslator GBA - Web Studio (M1 Mac / Apple Silicon)")
        print(f"  Server running at: {url}")
        print("  Press Ctrl+C to stop.")
        print("=" * 65 + "\n")

        if open_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down PokeTranslator GBA Studio.")
            httpd.shutdown()
