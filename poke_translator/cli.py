"""Command Line Interface for PokeTranslator GBA."""

import argparse
import sys
import os
from .core.rom import GbaRom
from .core.table_scanner import TableScanner, TableInjector
from .core.font_patcher import patch_kana_font
from .core.project import TranslationProject


def cmd_info(args: argparse.Namespace) -> None:
    """Displays information and analysis of a GBA ROM."""
    print(f"\n[PokeTranslator GBA] Analyzing ROM: {args.rom_path}")
    rom = GbaRom.load(args.rom_path)
    current_cs = rom.header_checksum
    calc_cs = rom.calculate_header_checksum()
    cs_status = "VALID (OK)" if current_cs == calc_cs else f"INVALID (Header: 0x{current_cs:02X}, Expected: 0x{calc_cs:02X})"

    print("=" * 60)
    print(f"  File Name:        {os.path.basename(args.rom_path)}")
    print(f"  File Size:        {len(rom.data) / (1024*1024):.2f} MB ({len(rom.data)} bytes)")
    print(f"  Game Title:       {rom.game_title}")
    print(f"  Game Code:        {rom.game_code}")
    print(f"  Maker Code:       {rom.maker_code}")
    print(f"  Software Version: 1.{rom.software_version}")
    print(f"  Header Checksum:  0x{current_cs:02X} -> {cs_status}")
    print(f"  Detected Engine:  {rom.detect_engine()}")
    print("=" * 60)

    # Quick preview of table entries
    scanner = TableScanner(rom)
    species = scanner.scan_pokemon_species()
    moves = scanner.scan_moves()
    items = scanner.scan_items()
    print(f"  Detected Pokémon Species: {len(species)}")
    print(f"  Detected Moves:           {len(moves)}")
    print(f"  Detected Items:           {len(items)}")
    print("=" * 60 + "\n")


def cmd_extract(args: argparse.Namespace) -> None:
    """Extracts translatable text from ROM into a project file or CSV."""
    print(f"\n[PokeTranslator GBA] Scanning ROM: {args.rom_path} ...")
    rom = GbaRom.load(args.rom_path)
    scanner = TableScanner(rom)
    entries = scanner.scan_all(include_dialogues=not args.no_dialogues)

    project = TranslationProject(
        name=os.path.splitext(os.path.basename(args.rom_path))[0],
        rom_filename=os.path.basename(args.rom_path),
        game_title=rom.game_title,
        game_code=rom.game_code,
        engine=rom.detect_engine(),
        entries=entries,
    )

    stats = project.get_stats()
    print(f"Scanned {stats['total_entries']} entries across categories.")
    for cat, info in stats["by_category"].items():
        print(f"  - {cat:20s}: {info['total']} entries ({info['translated']} auto-translated)")

    output_path = args.output or f"{project.name}_project.json"
    if args.csv:
        csv_path = os.path.splitext(output_path)[0] + ".csv"
        project.export_csv(csv_path)
        print(f"\nExported to CSV: {csv_path}")
    else:
        project.save_to_file(output_path)
        print(f"\nSaved project file: {output_path}")


def cmd_translate(args: argparse.Namespace) -> None:
    """Applies auto-translation to an existing project file."""
    print(f"\n[PokeTranslator GBA] Loading project: {args.project_path} ...")
    project = TranslationProject.load_from_file(args.project_path)
    use_mt = not getattr(args, "offline", False)
    new_count = project.auto_translate_all(overwrite=args.overwrite, use_machine_translation=use_mt)
    print(f"Auto-translated {new_count} entries (use_machine_translation: {use_mt}).")

    output_path = args.output or args.project_path
    project.save_to_file(output_path)
    print(f"Saved updated project: {output_path}\n")


def cmd_build(args: argparse.Namespace) -> None:
    """Injects translation and font patches into the ROM and exports translated .gba file."""
    print(f"\n[PokeTranslator GBA] Building translated ROM...")
    print(f"  Base ROM:    {args.rom_path}")
    print(f"  Project:     {args.project_path}")
    print(f"  Output ROM:  {args.output}")

    rom = GbaRom.load(args.rom_path)
    project = TranslationProject.load_from_file(args.project_path)

    # Patch Kana Font if requested
    if args.patch_font or project.patch_font:
        print("  Injecting Japanese Kana font tiles into ROM...")
        res = patch_kana_font(rom, char_width=project.char_width)
        print(f"  -> Patched {res['patched_glyphs']} font glyph slots.")

    # Inject translations
    print("  Injecting translated text entries...")
    injector = TableInjector(rom)
    inj_res = injector.inject_all(project.entries, use_kana=True)
    print(f"  -> {inj_res['modified']} entries injected ({inj_res['repointed']} repointed).")

    # Export ROM
    rom.export_rom(args.output)
    print(f"\nSUCCESS! Translated GBA ROM exported to: {args.output}")

    # Optional IPS Patch
    if args.ips:
        ips_data = rom.create_ips_patch()
        with open(args.ips, "wb") as f:
            f.write(ips_data)
        print(f"IPS Patch generated: {args.ips}")
    print()


def cmd_gui(args: argparse.Namespace) -> None:
    """Launches local Web Studio."""
    from .web.server import start_web_studio
    start_web_studio(port=args.port, open_browser=not args.no_browser)


def cmd_test_samples(args: argparse.Namespace) -> None:
    """Batch processes and verifies all sample ROMs in sample_data directory."""
    sample_dir = os.path.abspath(args.sample_dir or "sample_data")
    out_dir = os.path.join(sample_dir, "translated_output")
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n[PokeTranslator GBA] Processing sample ROMs in: {sample_dir}")
    if not os.path.exists(sample_dir):
        print(f"Error: {sample_dir} not found.")
        return

    rom_files = [f for f in sorted(os.listdir(sample_dir)) if f.endswith(".gba")]
    if not rom_files:
        print("No .gba ROM files found in sample_data.")
        return

    for f in rom_files:
        src = os.path.join(sample_dir, f)
        print("=" * 65)
        print(f"  Target ROM: {f}")
        rom = GbaRom.load(src)
        scanner = TableScanner(rom)
        entries = scanner.scan_all(include_dialogues=True)
        proj = TranslationProject(f, entries=entries)
        use_mt = not getattr(args, "offline", False)
        proj.auto_translate_all(use_machine_translation=use_mt)
        stats = proj.get_stats()
        print(f"  Completion: {stats['completion_percentage']}% ({stats['translated_entries']}/{stats['total_entries']})")
        for cat, info in stats["by_category"].items():
            pct = round(info['translated']/info['total']*100, 1) if info['total'] else 0
            print(f"    - {cat:18s}: {info['translated']}/{info['total']} ({pct}%)")

        # Build translated GBA ROM
        export_rom = GbaRom(rom.original_data, filename=f)
        patch_kana_font(export_rom, char_width=6)
        injector = TableInjector(export_rom)
        inj_stats = injector.inject_all(proj.entries, use_kana=True)
        export_rom.fix_header_checksum()

        base_name = os.path.splitext(f)[0]
        out_path = os.path.join(out_dir, f"{base_name}_JP.gba")
        export_rom.save(out_path)
        print(f"  Output GBA: {out_path} ({os.path.getsize(out_path)/(1024*1024):.1f}MB, Checksum={export_rom.verify_header_checksum()})")
    print("=" * 65)
    print("Sample ROM processing complete!\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="poke_translator",
        description="PokeTranslator GBA - GBA Pokemon ROM Hack Translation Tool for M1 Mac",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # info
    p_info = subparsers.add_parser("info", help="Display ROM details and header analysis")
    p_info.add_argument("rom_path", help="Path to .gba ROM file")

    # extract
    p_ext = subparsers.add_parser("extract", help="Scan and extract translatable text from ROM")
    p_ext.add_argument("rom_path", help="Path to .gba ROM file")
    p_ext.add_argument("-o", "--output", help="Output JSON project path")
    p_ext.add_argument("--csv", action="store_true", help="Also export as CSV spreadsheet")
    p_ext.add_argument("--no-dialogues", action="store_true", help="Skip scanning script dialogues")

    # translate
    p_trans = subparsers.add_parser("translate", help="Auto-translate project with official dictionary + MT")
    p_trans.add_argument("project_path", help="Path to project JSON file")
    p_trans.add_argument("-o", "--output", help="Output path (defaults to overwrite project)")
    p_trans.add_argument("--overwrite", action="store_true", help="Overwrite existing translations")
    p_trans.add_argument("--online", "--use-mt", action="store_true", default=True, help="セリフや看板を含む全テキストを翻訳APIで全自動翻訳 (デフォルト有効)")
    p_trans.add_argument("--offline", action="store_true", help="オンライン翻訳APIを使用せずオフライン辞書のみで翻訳")

    # build
    p_build = subparsers.add_parser("build", help="Build translated GBA ROM")
    p_build.add_argument("rom_path", help="Base .gba ROM file")
    p_build.add_argument("-p", "--project-path", required=True, help="Project JSON file with translations")
    p_build.add_argument("-o", "--output", required=True, help="Path for output translated .gba file")
    p_build.add_argument("--patch-font", action="store_true", help="Force inject Japanese Kana font tiles")
    p_build.add_argument("--ips", help="Optional path to output IPS patch file")

    # gui
    p_gui = subparsers.add_parser("gui", help="Launch interactive Web Studio in browser")
    p_gui.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")
    p_gui.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")

    # test-samples
    p_test = subparsers.add_parser("test-samples", help="Process and verify all sample ROMs in sample_data")
    p_test.add_argument("--sample-dir", default="sample_data", help="Path to sample_data directory")
    p_test.add_argument("--online", "--use-mt", action="store_true", default=True, help="セリフや看板も翻訳APIで全自動翻訳 (デフォルト有効)")
    p_test.add_argument("--offline", action="store_true", help="オンライン翻訳APIを使用せずオフライン辞書のみで翻訳")

    args = parser.parse_args()
    if not args.command:
        # Default action when run without arguments: launch GUI
        from .web.server import start_web_studio
        start_web_studio(port=8080, open_browser=True)
        return

    if args.command == "info":
        cmd_info(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "translate":
        cmd_translate(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "gui":
        cmd_gui(args)
    elif args.command == "test-samples":
        cmd_test_samples(args)


if __name__ == "__main__":
    main()
