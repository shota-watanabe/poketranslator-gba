"""Comprehensive Pokemon Gen 1-9 translation dictionary, fuzzy normalization,
Mega Stone handler, and autonomous machine translation engine.
"""

import re
import urllib.request
import urllib.parse
import json
import time
import threading
from typing import Dict, Optional, Tuple, List, Any
from .charmap import hiragana_to_katakana
from .dict_data import (
    SPECIES_GEN4_TO_GEN9,
    EXPANDED_MOVES,
    EXPANDED_ABILITIES,
    EXPANDED_ITEMS,
    OFFICIAL_ITEM_DESCRIPTIONS,
    ITEM_NAME_DEFAULT_DESCRIPTIONS,
)
from .dialogue_data import (
    SPEAKER_NAME_MAP,
    DIALOGUE_PATTERNS,
    convert_kanji_to_kana,
)

# ---------------------------------------------------------------------------
# Key Normalization Helper
# Strips hyphens, underscores, dots, apostrophes, spaces and converts to uppercase
# ---------------------------------------------------------------------------
def normalize_key(text: str) -> str:
    """Normalizes a string for robust dictionary matching.
    e.g. 'Sand-Attack' -> 'SANDATTACK', 'Headbutt' -> 'HEADBUTT'
    """
    if not text:
        return ""
    # Strip leading/trailing and uppercase
    s = text.strip().upper()
    # Replace common variant characters and GBA glyph anomalies
    s = s.replace("É", "E").replace("È", "E").replace("ヒ", "E").replace("’", "'").replace("`", "'")
    # Remove all non-alphanumeric characters
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s


# ---------------------------------------------------------------------------
# Official Menu and System Terms
# ---------------------------------------------------------------------------
MENU_DICTIONARY: Dict[str, str] = {
    "POKÉDEX": "ポケモンずかん", "POKEDEX": "ポケモンずかん",
    "POKÉMON": "ポケモン", "POKEMON": "ポケモン",
    "BAG": "バッグ",
    "POKÉNAV": "ポケナビ", "POKENAV": "ポケナビ",
    "SAVE": "レポート",
    "OPTION": "せってい", "OPTIONS": "せってい",
    "EXIT": "とじる", "RETIRE": "やめる",
    "FIGHT": "たたかう", "RUN": "にげる",
    "YES": "はい", "NO": "いいえ", "OK": "OK",
    "CANCEL": "もどる", "QUIT": "やめる", "ACCEPT": "けってい",
    "BUY": "かう", "SELL": "うる", "SEE YA": "やめる", "SEE YA!": "やめる",
    "ITEMS": "どうぐ", "KEY ITEMS": "たいせつなもの",
    "POKÉ BALLS": "ボール", "POKE BALLS": "ボール", "BALLS": "ボール",
    "TM CASE": "わざマシン", "TMS & HMS": "わざマシン",
    "BERRY POUCH": "きのみ", "BERRIES": "きのみ",
    "MEDICINE": "くすり", "BATTLE ITEMS": "せんとうよう",
    "USE": "つかう", "GIVE": "もたせる", "TAKE": "あずかる",
    "TOSS": "すてる", "REGISTER": "とうろく", "INFO": "せつめい",
    "DESEL": "かいじょ", "CHECK": "みる",
    "SUMMARY": "つよさをみる", "SWITCH": "いれかえる", "ITEM": "もちもの",
    "HP": "HP", "ATTACK": "こうげき", "DEFENSE": "ぼうぎょ",
    "SP. ATK": "とくこう", "SP. DEF": "とくぼう", "SPEED": "すばやさ",
    "EXP": "けいけんち", "EXP POINTS": "けいけんち", "NEXT LV.": "つぎのレベルまで",
    "TYPE": "タイプ", "OT": "おや", "IDNo.": "IDNo.", "STATUS": "じょうたい",
    "NATURE": "せいかく", "ABILITY": "とくせい", "POWER": "いりょく",
    "ACCURACY": "めいちゅう", "PP": "PP",
    "WITHDRAW POKÉMON": "ポケモンを ひきだす",
    "DEPOSIT POKÉMON": "ポケモンを あずける",
    "MOVE POKÉMON": "ポケモンを つれていく",
    "MOVE ITEMS": "もちものを うごかす",
    "CHANGE BOX": "ボックスを かえる",
    "PSN": "どく", "PAR": "まひ", "SLP": "ねむり", "BRN": "やけど",
    "FRZ": "こおり", "FNT": "ひんし",
    "TEXT SPEED": "はなしの はやさ",
    "BATTLE SCENE": "せんとうアニメ",
    "BATTLE STYLE": "しあいの ルール",
    "SOUND": "サウンド",
    "BUTTON MODE": "ボタンモード",
    "FRAME": "ウィンドウ",
    "SLOW": "おそい", "MID": "ふつう", "FAST": "はやい",
    "SHIFT": "いれかえ", "SET": "かちぬき",
    "MONO": "モノラル", "STEREO": "ステレオ",
    "POKÉMON INFO": "ポケモンじょうほう", "POKEMON INFO": "ポケモンじょうほう",
    "POKÉMON SKILLS": "ポケモンののうりょく", "POKEMON SKILLS": "ポケモンののうりょく",
    "KNOWN MOVES": "たたかうわざ",
    "CONTROLS": "そうさほうほう",
}

# ---------------------------------------------------------------------------
# Types & Natures
# ---------------------------------------------------------------------------
TYPE_DICTIONARY: Dict[str, str] = {
    "NORMAL": "ノーマル", "FIGHTING": "かくとう", "FIGHT": "かくとう",
    "FLYING": "ひこう", "POISON": "どく", "GROUND": "じめん", "ROCK": "いわ",
    "BUG": "むし", "GHOST": "ゴースト", "STEEL": "はがね", "FIRE": "ほのお",
    "WATER": "みず", "GRASS": "くさ", "ELECTRIC": "でんき", "ELECTR": "でんき",
    "PSYCHIC": "エスパー", "PSYCHC": "エスパー",
    "ICE": "こおり", "DRAGON": "ドラゴン", "DARK": "あく", "FAIRY": "フェアリー",
    "???": "???",
}

NATURE_DICTIONARY: Dict[str, str] = {
    "HARDY": "がんばりや", "LONELY": "さみしがり", "BRAVE": "ゆうかん",
    "ADAMANT": "いじっぱり", "NAUGHTY": "やんちゃ", "BOLD": "ずぶとい",
    "DOCILE": "すなお", "RELAXED": "のんき", "IMPISH": "わんぱく",
    "LAX": "のうてんき", "TIMID": "おくびょう", "HASTY": "せっかち",
    "SERIOUS": "まじめ", "JOLLY": "ようき", "NAIVE": "むじゃき",
    "MODEST": "ひかえめ", "MILD": "おっとり", "QUIET": "れいせい",
    "BASHFUL": "てれや", "RASH": "うっかりや", "CALM": "おだやか",
    "GENTLE": "おとなしい", "SASSY": "なまいき", "CAREFUL": "しんちょう",
    "QUIRKY": "きまぐれ",
}

# ---------------------------------------------------------------------------
# All 48 Official Mega Stones (メガストーン)
# ---------------------------------------------------------------------------
MEGA_STONES_DICTIONARY: Dict[str, str] = {
    "ABOMASITE": "ユキノオナイト",
    "ABSOLITE": "アブソルナイト",
    "AERODACTYLITE": "プテラナイト",
    "AGGRONITE": "ボスゴドラナイト",
    "ALAKAZITE": "フーディナイト",
    "ALTARIANITE": "チルタリスナイト",
    "AMPHAROSITE": "デンリュウナイト",
    "AUDINITE": "タブンネナイト",
    "BANETTITE": "ジュペッタナイト",
    "BEEDRILLITE": "スピアーナイト",
    "BLASTOISINITE": "カメックスナイト",
    "BLAZIKENITE": "バシャーモナイト",
    "CAMERUPTITE": "バクーダナイト",
    "CHARIZARDITE X": "リザードナイトX",
    "CHARIZARDITE Y": "リザードナイトY",
    "CHARIZARDITE": "リザードナイト",
    "DIANCITE": "ディアンシナイト",
    "GALLADITE": "エルレイドナイト",
    "GARCHOMPITE": "ガブリアスナイト",
    "GARDEVOIRITE": "サーナイトナイト",
    "GENGARITE": "ゲンガーナイト",
    "GLALITITE": "オニゴーリナイト",
    "GYARADOSITE": "ギャラドスナイト",
    "HERACRONITE": "ヘラクロスナイト",
    "HOUNDOOMINITE": "ヘルガーナイト",
    "KANGASKHANITE": "ガルーラナイト",
    "LATIASITE": "ラティアスナイト",
    "LATIOSITE": "ラティオスナイト",
    "LOPUNNITE": "ミミロップナイト",
    "LUCARIONITE": "ルカリオナイト",
    "MANECTITE": "ライボルトナイト",
    "MAWILITE": "クチートナイト",
    "MEDICHAMITE": "チャーレムナイト",
    "METAGROSSITE": "メタグロスナイト",
    "MEWTWONITE X": "ミュウツナイトX",
    "MEWTWONITE Y": "ミュウツナイトY",
    "MEWTWONITE": "ミュウツナイト",
    "PIDGEOTITE": "ピジョットナイト",
    "PINSIRITE": "カイロスナイト",
    "SABLENITE": "ヤミラミナイト",
    "SALAMENCITE": "ボーマンダナイト",
    "SCEPTILITE": "ジュカインナイト",
    "SCIZORITE": "ハッサムナイト",
    "SHARPEDONITE": "サメハダナイト",
    "SLOWBRONITE": "ヤドランナイト",
    "STEELIXITE": "ハガネールナイト",
    "SWAMPERTITE": "ラグラージナイト",
    "TYRANITARITE": "バンギラスナイト",
    "VENUSAURITE": "フシギバナナイト",
    "MEGA BRACELET": "メガブレス",
    "MEGA RING": "メガリング",
    "MEGA CUFF": "メガカフス",
    "MEGA CHARM": "メガチャーム",
}

# ---------------------------------------------------------------------------
# Pokemon Species Names (Gen 1-9 & Major Forms)
# ---------------------------------------------------------------------------
POKEMON_DICTIONARY: Dict[str, str] = {
    # Gen 1
    "BULBASAUR": "フシギダネ", "IVYSAUR": "フシギソウ", "VENUSAUR": "フシギバナ",
    "CHARMANDER": "ヒトカゲ", "CHARMELEON": "リザード", "CHARIZARD": "リザードン",
    "SQUIRTLE": "ゼニガメ", "WARTORTLE": "カメール", "BLASTOISE": "カメックス",
    "CATERPIE": "キャタピー", "METAPOD": "トランセル", "BUTTERFREE": "バタフリー",
    "WEEDLE": "ビードル", "KAKUNA": "コクーン", "BEEDRILL": "スピアー",
    "PIDGEY": "ポッポ", "PIDGEOTTO": "ピジョン", "PIDGEOT": "ピジョット",
    "RATTATA": "コラッタ", "RATICATE": "ラッタ", "SPEAROW": "オニスズメ", "FEAROW": "オニドリル",
    "EKANS": "アーボ", "ARBOK": "アーボック", "PIKACHU": "ピカチュウ", "RAICHU": "ライチュウ",
    "SANDSHREW": "サンド", "SANDSLASH": "サンドパン", "NIDORAN♀": "ニドラン♀", "NIDORAN F": "ニドラン♀",
    "NIDORINA": "ニドリーナ", "NIDOQUEEN": "ニドクイン", "NIDORAN♂": "ニドラン♂", "NIDORAN M": "ニドラン♂",
    "NIDORINO": "ニドリーノ", "NIDOKING": "ニドキング", "CLEFAIRY": "ピッピ", "CLEFABLE": "ピクシー",
    "VULPIX": "ロコン", "NINETALES": "キュウコン", "JIGGLYPUFF": "プリン", "WIGGLYTUFF": "プクリン",
    "ZUBAT": "ズバット", "GOLBAT": "ゴルバット", "ODDISH": "ナゾノクサ", "GLOOM": "クサイハナ",
    "VILEPLUME": "ラフレシア", "PARAS": "パラス", "PARASECT": "パラセクト", "VENONAT": "コンパン",
    "VENOMOTH": "モルフォン", "DIGLETT": "ディグダ", "DUGTRIO": "ダグトリオ", "MEOWTH": "ニャース",
    "PERSIAN": "ペルシアン", "PSYDUCK": "コダック", "GOLDUCK": "ゴルダック", "MANKEY": "マンキー",
    "PRIMEAPE": "オコリザル", "GROWLITHE": "ガーディ", "ARCANINE": "ウインディ", "POLIWAG": "ニョロモ",
    "POLIWHIRL": "ニョロゾ", "POLIWRATH": "ニョロボン", "ABRA": "ケーシィ", "KADABRA": "ユンゲラー",
    "ALAKAZAM": "フーディン", "MACHOP": "ワンリキー", "MACHOKE": "ゴーリキー", "MACHAMP": "カイリキー",
    "BELLSPROUT": "マダツボミ", "WEEPINBELL": "ウツドン", "VICTREEBEL": "ウツボット",
    "TENTACOOL": "メノクラゲ", "TENTACRUEL": "ドククラゲ", "GEODUDE": "イシツブテ",
    "GRAVELER": "ゴローン", "GOLEM": "ゴローニャ", "PONYTA": "ポニータ", "RAPIDASH": "ギャロップ",
    "SLOWPOKE": "ヤドン", "SLOWBRO": "ヤドラン", "MAGNEMITE": "コイル", "MAGNETON": "レアコイル",
    "FARFETCH'D": "カモネギ", "FARFETCHD": "カモネギ", "DODUO": "ドードー", "DODRIO": "ドードリオ",
    "SEEL": "パウワウ", "DEWGONG": "ジュゴン", "GRIMER": "ベトベター", "MUK": "ベトベトン",
    "SHELLDER": "シェルダー", "CLOYSTER": "パルシェン", "GASTLY": "ゴース", "HAUNTER": "ゴースト",
    "GENGAR": "ゲンガー", "ONIX": "イワーク", "DROWZEE": "スリープ", "HYPNO": "スリーパー",
    "KRABBY": "クラブ", "KINGLER": "キングラー", "VOLTORB": "ビリリダマ", "ELECTRODE": "マルマイン",
    "EXEGGCUTE": "タマタマ", "EXEGGUTOR": "ナッシー", "CUBONE": "カラカラ", "MAROWAK": "ガラガラ",
    "HITMONLEE": "サワムラー", "HITMONCHAN": "エビワラー", "LICKITUNG": "ベロリンガ",
    "KOFFING": "ドガース", "WEEZING": "マタドガス", "RHYHORN": "サイホーン", "RHYDON": "サイドン",
    "CHANSEY": "ラッキー", "TANGELA": "モンジャラ", "KANGASKHAN": "ガルーラ", "HORSEA": "タッツー",
    "SEADRA": "シードラ", "GOLDEEN": "トサキント", "SEAKING": "アズマオウ", "STARYU": "ヒトデマン",
    "STARMIE": "スターミー", "MR. MIME": "バリヤード", "MR MIME": "バリヤード", "SCYTHER": "ストライク",
    "JYNX": "ルージュラ", "ELECTABUZZ": "エレブー", "MAGMAR": "ブーバー", "PINSIR": "カイロス",
    "TAUROS": "ケンタロス", "MAGIKARP": "コイキング", "GYARADOS": "ギャラドス", "LAPRAS": "ラプラス",
    "DITTO": "メタモン", "EEVEE": "イーブイ", "VAPOREON": "シャワーズ", "JOLTEON": "サンダース",
    "FLAREON": "ブースター", "PORYGON": "ポリゴン", "OMANYTE": "オムナイト", "OMASTAR": "オムスター",
    "KABUTO": "カブト", "KABUTOPS": "カブトプス", "AERODACTYL": "プテラ", "SNORLAX": "カビゴン",
    "ARTICUNO": "フリーザー", "ZAPDOS": "サンダー", "MOLTRES": "ファイヤー", "DRATINI": "ミニリュウ",
    "DRAGONAIR": "ハクリュー", "DRAGONITE": "カイリュー", "MEWTWO": "ミュウツー", "MEW": "ミュウ",
    # Gen 2
    "CHIKORITA": "チコリータ", "BAYLEEF": "ベイリーフ", "MEGANIUM": "メガニウム",
    "CYNDAQUIL": "ヒノアラシ", "QUILAVA": "マグマラシ", "TYPHLOSION": "バクフーン",
    "TOTODILE": "ワニノコ", "CROCONAW": "アリゲイツ", "FERALIGATR": "オーダイル",
    "SENTRET": "オタチ", "FURRET": "オオタチ", "HOOTHOOT": "ホーホー", "NOCTOWL": "ヨルノズク",
    "LEDYBA": "レディバ", "LEDIAN": "レディアン", "SPINARAK": "イトマル", "ARIADOS": "アリアドス",
    "CROBAT": "クロバット", "CHINCHOU": "チョンチー", "LANTURN": "ランターン",
    "PICHU": "ピチュー", "CLEFFA": "ピィ", "IGGLYBUFF": "ププリン", "TOGEPI": "トゲピー",
    "TOGETIC": "トゲチック", "NATU": "ネイティ", "XATU": "ネイティオ", "MAREEP": "メリープ",
    "FLAAFFY": "モココ", "AMPHAROS": "デンリュウ", "BELLOSSOM": "キレイハナ",
    "MARILL": "マリル", "AZUMARILL": "マリルリ", "SUDOWOODO": "ウソッキー", "POLITOED": "ニョロトノ",
    "HOPPIP": "ハネッコ", "SKIPLOOM": "ポポッコ", "JUMPLUFF": "ワタッコ", "AIPOM": "エイパム",
    "SUNKERN": "ヒマナッツ", "SUNFLORA": "キマワリ", "YANMA": "ヤンヤンマ", "WOOPER": "ウパー",
    "QUAGSIRE": "ヌオー", "ESPEON": "エーフィ", "UMBREON": "ブラッキー", "MURKROW": "ヤミカラス",
    "SLOWKING": "ヤドキング", "MISDREAVUS": "ムウマ", "UNOWN": "アンノーン", "WOBBUFFET": "ソーナンス",
    "GIRAFARIG": "キリンリキ", "PINECO": "クヌギダマ", "FORRETRESS": "フォレトス",
    "DUNSPARCE": "ノコッチ", "GLIGAR": "グライガー", "STEELIX": "ハガネール", "SNUBBULL": "ブルー",
    "GRANBULL": "グランブル", "QWILFISH": "ハリーセン", "SCIZOR": "ハッサム", "SHUCKLE": "ツボツボ",
    "HERACROSS": "ヘラクロス", "SNEASEL": "ニューラ", "TEDDIURSA": "ヒメグマ", "URSARING": "リングマ",
    "SLUGMA": "マグマッグ", "MAGCARGO": "マグカルゴ", "SWINUB": "ウリムー", "PILOSWINE": "イノムー",
    "CORSOLA": "サニーゴ", "REMORAID": "テッポウオ", "OCTILLERY": "オクタン", "DELIBIRD": "デリバード",
    "MANTINE": "マンタイン", "SKARMORY": "エアームド", "HOUNDOUR": "デルビル", "HOUNDOOM": "ヘルガー",
    "KINGDRA": "キングドラ", "PHANPY": "ゴマゾウ", "DONPHAN": "ドンファン", "PORYGON2": "ポリゴン2",
    "STANTLER": "オドシシ", "SMEARGLE": "ドーブル", "TYROGUE": "バルキー", "HITMONTOP": "カポエラー",
    "SMOOCHUM": "ムチュール", "ELEKID": "エレキッド", "MAGBY": "ブビィ", "MILTANK": "ミルタンク",
    "BLISSEY": "ハピナス", "RAIKOU": "ライコウ", "ENTEI": "エンテイ", "SUICUNE": "スイクン",
    "LARVITAR": "ヨーギラス", "PUPITAR": "サナギラス", "TYRANITAR": "バンギラス",
    "LUGIA": "ルギア", "HO-OH": "ホウオウ", "CELEBI": "セレビィ",
    # Gen 3
    "TREECKO": "キモリ", "GROVYLE": "ジュプトル", "SCEPTILE": "ジュカイン",
    "TORCHIC": "アチャモ", "COMBUSKEN": "ワカシャモ", "BLAZIKEN": "バシャーモ",
    "MUDKIP": "ミズゴロウ", "MARSHTOMP": "ヌマクロー", "SWAMPERT": "ラグラージ",
    "POOCHYENA": "ポチエナ", "MIGHTYENA": "グラエナ", "ZIGZAGOON": "ジグザグマ", "LINOONE": "マッスグマ",
    "WURMPLE": "ケムッソ", "SILCOON": "カラサリス", "BEAUTIFLY": "アゲハント",
    "CASCOON": "マユルド", "DUSTOX": "ドクケイル", "LOTAD": "ハスボー", "LOMBRE": "ハスブレロ",
    "LUDICOLO": "ルンパッパ", "SEEDOT": "タネボー", "NUZLEAF": "コノハナ", "SHIFTRY": "ダーテング",
    "TAILLOW": "スバメ", "SWELLOW": "オオスバメ", "WINGULL": "キャモメ", "PELIPPER": "ペリッパー",
    "RALTS": "ラルトス", "KIRLIA": "キルリア", "GARDEVOIR": "サーナイト",
    "SURSKIT": "アメタマ", "MASQUERAIN": "アメモース", "SHROOMISH": "キノココ", "BRELOOM": "キノガッサ",
    "SLAKOTH": "ナマケロ", "VIGOROTH": "ヤルキモノ", "SLAKING": "ケッキング",
    "NINCADA": "ツチニン", "NINJASK": "テッカニン", "SHEDINJA": "ヌケニン",
    "WHISMUR": "ゴニョニョ", "LOUDRED": "ドゴーム", "EXPLOUD": "バクオング",
    "MAKUHITA": "マクノシタ", "HARIYAMA": "ハリテヤマ", "AZURILL": "ルリリ", "NOSEPASS": "ノズパス",
    "SKITTY": "エネコ", "DELCATTY": "エネコロロ", "SABLEYE": "ヤミラミ", "MAWILE": "クチート",
    "ARON": "ココドラ", "LAIRON": "コドラ", "AGGRON": "ボスゴドラ", "MEDITITE": "アサナン",
    "MEDICHAM": "チャーレム", "ELECTRIKE": "ラクライ", "MANECTRIC": "ライボルト",
    "PLUSLE": "プラスル", "MINUN": "マイナン", "VOLBEAT": "バルビート", "ILLUMISE": "イルミーゼ",
    "ROSELIA": "ロゼリア", "GULPIN": "ゴクリン", "SWALOT": "マルノーム", "CARVANHA": "キバニア",
    "SHARPEDO": "サメハダー", "WAILMER": "ホエルコ", "WAILORD": "ホエルオー", "NUMEL": "ドンメル",
    "CAMERUPT": "バクーダ", "TORKOAL": "コータス", "SPOINK": "バネブー", "GRUMPIG": "ブーピッグ",
    "SPINDA": "パッチール", "TRAPINCH": "ナックラー", "VIBRAVA": "ビブラーバ", "FLYGON": "フライゴン",
    "CACNEA": "サボネア", "CACTURNE": "ノクタス", "SWABLU": "チルット", "ALTARIA": "チルタリス",
    "ZANGOOSE": "ザングース", "SEVIPER": "ハブネーク", "LUNATONE": "ルナトーン", "SOLROCK": "ソルロック",
    "BARBOACH": "ドジョッチ", "WHISCASH": "ナマズン", "CORPHISH": "ヘイガニ", "CRAWDAUNT": "シザリガー",
    "BALTOY": "ヤジロン", "CLAYDOL": "ネンドール", "LILEEP": "リリーラ", "CRADILY": "ユレイドル",
    "ANORITH": "アノプス", "ARMALDO": "アーマルド", "FEEBAS": "ヒンバス", "MILOTIC": "ミロカロス",
    "CASTFORM": "ポワルン", "KECLEON": "カクレオン", "SHUPPET": "カゲボウズ", "BANETTE": "ジュペッタ",
    "DUSKULL": "ヨマワル", "DUSCLOPS": "サマヨール", "TROPIUS": "トロピウス", "CHIMECHO": "チリーン",
    "ABSOL": "アブソル", "WYNAUT": "ソーナノ", "SNORUNT": "ユキワラシ", "GLALIE": "オニゴーリ",
    "SPHEAL": "タマザラシ", "SEALEO": "トドグラー", "WALREIN": "トドゼルガ", "CLAMPERL": "パールル",
    "HUNTAIL": "ハンテール", "GOREBYSS": "サクラビス", "RELICANTH": "ジーランス", "LUVDISC": "ラブカス",
    "BAGON": "タツベイ", "SHELGON": "コモルー", "SALAMENCE": "ボーマンダ", "BELDUM": "ダンバル",
    "METANG": "メタング", "METAGROSS": "メタグロス", "REGIROCK": "レジロック", "REGICE": "レジアイス",
    "REGISTEEL": "レジスチル", "LATIAS": "ラティアス", "LATIOS": "ラティオス", "KYOGRE": "カイオーガ",
    "GROUDON": "グラードン", "RAYQUAZA": "レックウザ", "JIRACHI": "ジラーチ", "DEOXYS": "デオキシス",
    # Gen 4-9 & Common ROM Hack Species
    "TURTWIG": "ナエトル", "GROTLE": "ハヤシガメ", "TORTERRA": "ドダイトス",
    "CHIMCHAR": "ヒコザル", "MONFERNO": "モウカザル", "INFERNAPE": "ゴウカザル",
    "PIPLUP": "ポッチャマ", "PRINPLUP": "ポッタイシ", "EMPOLEON": "エンペルト",
    "STARLY": "ムックル", "STARAVIA": "ムクバード", "STARAPTOR": "ムクホーク",
    "BIDOOF": "ビッパ", "BIBAREL": "ビーダル", "SHINX": "コリンク", "LUXIO": "ルクシオ",
    "LUXRAY": "レントラー", "CRANIDOS": "ズガイドス", "RAMPARDOS": "ラムパルド",
    "SHIELDON": "タテトプス", "BASTIODON": "トリデプス", "GIBLE": "フカマル",
    "GABITE": "ガバイト", "GARCHOMP": "ガブリアス", "RIOLU": "リオル", "LUCARIO": "ルカリオ",
    "SNOVER": "ユキカブリ", "ABOMASNOW": "ユキノオー", "WEAVILE": "マニューラ",
    "MAGNEZONE": "ジバコイル", "LICKILICKY": "ベロベルト", "RHYPERIOR": "ドサイドン",
    "TANGROWTH": "モジャンボ", "ELECTIVIRE": "エレキブル", "MAGMORTAR": "ブーバーン",
    "TOGEKISS": "トゲキッス", "YANMEGA": "メガヤンマ", "LEAFEON": "リーフィア", "GLACEON": "グレイシア",
    "GLISCOR": "グライオン", "MAMOSWINE": "マンムー", "PORYGON-Z": "ポリゴンZ",
    "GALLADE": "エルレイド", "PROBOPASS": "ダイノーズ", "DUSKNOIR": "ヨノワール",
    "FROSLASS": "ユキメノコ", "ROTOM": "ロトム", "DIALGA": "ディアルガ", "PALKIA": "パルキア",
    "GIRATINA": "ギラティナ", "CRESSELIA": "クレセリア", "DARKRAI": "ダークライ", "ARCEUS": "アルセウス",
    "SNIVY": "ツタージャ", "SERVINE": "ジャノビー", "SERPERIOR": "ジャローダ",
    "TEPIG": "ポカブ", "PIGNITE": "チャオブー", "EMBOAR": "エンブオー",
    "OSHAWOTT": "ミジュマル", "DEWOTT": "フタチマル", "SAMUROTT": "ダイケンキ",
    "ZORUA": "ゾロア", "ZOROARK": "ゾロアーク", "LITWICK": "ヒトモシ", "LAMPENT": "ランプラー",
    "CHANDELURE": "シャンデラ", "AXEW": "キバゴ", "FRAXURE": "オノンド", "HAXORUS": "オノノクス",
    "DEINO": "モノズ", "ZWEILOUS": "ジヘッド", "HYDREIGON": "サザンドラ", "LARVESTA": "メラルバ",
    "VOLCARONA": "ウルガモス", "RESHIRAM": "レシラム", "ZEKROM": "ゼクロム", "KYUREM": "キュレム",
    "CHESPIN": "ハリマロン", "QUILLADIN": "ハリボーグ", "CHESNAUGHT": "ブリガロン",
    "FENNEKIN": "フォッコ", "BRAIXEN": "テールナー", "DELPHOX": "マフォクシー",
    "FROAKIE": "ケロマツ", "FROGADIER": "ゲコガシラ", "GRENINJA": "ゲッコウガ",
    "FLETCHLING": "ヤヤコマ", "FLETCHINDER": "ヒノヤコマ", "TALONFLAME": "ファイアロー",
    "HONEDGE": "ヒトツキ", "DOUBLADE": "ニダンギル", "AEGISLASH": "ギルガルド",
    "GOOMY": "ヌメラ", "SLIGGOO": "ヌメイル", "GOODRA": "ヌメルゴン",
    "SYLVEON": "ニンフィア", "HAWLUCHA": "ルチャブル", "NOIBAT": "オンバット", "NOIVERN": "オンバーン",
    "XERNEAS": "ゼルネアス", "YVELTAL": "イベルタル", "ZYGARDE": "ジガルデ", "DIANCIE": "ディアンシー",
    "ROWLET": "モクロー", "LITTEN": "ニャビー", "POPPLIO": "アシマリ", "MIMIKYU": "ミミッキュ",
    "TOXAPEX": "ドヒドイデ", "DRAGAPULT": "ドラパルト", "CERULEDGE": "ソウブレイズ",
    "ARMAROUGE": "グレンアルマ", "ANNIHILAPE": "コノヨザル", "KINGAMBIT": "ドドゲザン",
    "KORAIDON": "コライドン", "MIRAIDON": "ミライドン", "PECHARUNT": "モモワロウ",
}

# ---------------------------------------------------------------------------
# Move Names (Gen 1-9) with Hyphenated and Alias Variants
# ---------------------------------------------------------------------------
MOVE_DICTIONARY: Dict[str, str] = {
    "POUND": "はたく", "KARATE CHOP": "からてチョップ", "DOUBLE SLAP": "おうふくビンタ",
    "DOUBLESLAP": "おうふくビンタ", "COMET PUNCH": "れんぞくパンチ", "COMETPUNCH": "れんぞくパンチ",
    "MEGA PUNCH": "メガトンパンチ", "MEGAPUNCH": "メガトンパンチ", "PAY DAY": "ネコにこばん",
    "PAYDAY": "ネコにこばん", "FIRE PUNCH": "ほのおのパンチ", "FIREPUNCH": "ほのおのパンチ",
    "ICE PUNCH": "れいとうパンチ", "ICEPUNCH": "れいとうパンチ", "THUNDER PUNCH": "かみなりのパンチ",
    "THUNDERPUNCH": "かみなりのパンチ", "SCRATCH": "ひっかく", "VICE GRIP": "はさむ",
    "VICEGRIP": "はさむ", "VISE GRIP": "はさむ", "VISEGRIP": "はさむ",
    "GUILLOTINE": "ハサミギロチン", "RAZOR WIND": "かまいたち", "RAZORWIND": "かまいたち",
    "SWORDS DANCE": "つるぎのまい", "SWORDSDANCE": "つるぎのまい", "CUT": "いあいぎり",
    "GUST": "かぜおこし", "WING ATTACK": "つばさでうつ", "WINGATTACK": "つばさでうつ",
    "WHIRLWIND": "ふきとばし", "FLY": "そらをとぶ", "BIND": "しめつける", "SLAM": "たたきつける",
    "VINE WHIP": "つるのムチ", "VINEWHIP": "つるのムチ", "STOMP": "ふみつけ",
    "DOUBLE KICK": "にどげり", "DOUBLEKICK": "にどげり", "MEGA KICK": "メガトンキック",
    "MEGAKICK": "メガトンキック", "JUMP KICK": "とびげり", "JUMPKICK": "とびげり",
    "ROLLING KICK": "まわしげり", "ROLLINGKICK": "まわしげり", "SAND ATTACK": "すなかけ",
    "SAND-ATTACK": "すなかけ", "SANDATTACK": "すなかけ", "HEADBUTT": "ずつき",
    "HORN ATTACK": "つのおの", "HORNATTACK": "つのおの", "FURY ATTACK": "みだれづき",
    "FURYATTACK": "みだれづき", "HORN DRILL": "つのドリル", "HORNDRILL": "つのドリル",
    "TACKLE": "たいあたり", "BODY SLAM": "のしかかり", "BODYSLAM": "のしかかり",
    "TAKE DOWN": "とっしん", "TAKEDOWN": "とっしん", "THRASH": "あばれる",
    "DOUBLE-EDGE": "すてみタックル", "DOUBLE EDGE": "すてみタックル", "DOUBLEEDGE": "すてみタックル",
    "TAIL WHIP": "しっぽをふる", "TAILWHIP": "しっぽをふる", "POISON STING": "どくばり",
    "POISONSTING": "どくばり", "TWINEEDLE": "ダブルニードル", "PIN MISSILE": "ミサイルばり",
    "PINMISSILE": "ミサイルばり", "LEER": "にらみつける", "BITE": "かみつく",
    "GROWL": "なきごえ", "ROAR": "ほえる", "SING": "うたう", "SUPERSONIC": "ちょうおんぱ",
    "SONIC BOOM": "ソニックブーム", "SONICBOOM": "ソニックブーム", "DISABLE": "かなしばり",
    "ACID": "ようかいえき", "EMBER": "ひのこ", "FLAMETHROWER": "かえんほうしゃ",
    "MIST": "しろいきり", "WATER GUN": "みずでっぽう", "WATERGUN": "みずでっぽう",
    "HYDRO PUMP": "ハイドロポンプ", "HYDROPUMP": "ハイドロポンプ", "SURF": "なみのり",
    "ICE BEAM": "れいとうビーム", "ICEBEAM": "れいとうビーム", "BLIZZARD": "ふぶき",
    "PSYBEAM": "サイケこうせん", "BUBBLE BEAM": "バブルこうせん", "BUBBLEBEAM": "バブルこうせん",
    "AURORA BEAM": "オーロラビーム", "AURORABEAM": "オーロラビーム", "HYPER BEAM": "はかいこうせん",
    "HYPERBEAM": "はかいこうせん", "PECK": "つつく", "DRILL PECK": "ドリルくちばし",
    "DRILLPECK": "ドリルくちばし", "SUBMISSION": "じごくぐるま", "LOW KICK": "けたぐり",
    "LOWKICK": "けたぐり", "COUNTER": "カウンター", "SEISMIC TOSS": "ちきゅうなげ",
    "SEISMICTOSS": "ちきゅうなげ", "STRENGTH": "かいりき", "ABSORB": "すいとる",
    "MEGA DRAIN": "メガドレイン", "MEGADRAIN": "メガドレイン", "LEECH SEED": "やどりぎのタネ",
    "LEECHSEED": "やどりぎのタネ", "GROWTH": "せいちょう", "RAZOR LEAF": "はっぱカッター",
    "RAZORLEAF": "はっぱカッター", "SOLAR BEAM": "ソーラービーム", "SOLAR-BEAM": "ソーラービーム",
    "SOLARBEAM": "ソーラービーム", "POISON POWDER": "どくのこな", "POISON-POWDER": "どくのこな",
    "POISONPOWDER": "どくのこな", "STUN SPORE": "しびれごな", "STUNSPORE": "しびれごな",
    "SLEEP POWDER": "ねむりごな", "SLEEPPOWDER": "ねむりごな", "PETAL DANCE": "はなびらのまい",
    "PETALDANCE": "はなびらのまい", "STRING SHOT": "いとをはく", "STRINGSHOT": "いとをはく",
    "DRAGON RAGE": "りゅうのいかり", "DRAGONRAGE": "りゅうのいかり", "FIRE SPIN": "ほのおのうず",
    "FIRESPIN": "ほのおのうず", "THUNDER SHOCK": "でんきショック", "THUNDERSHOCK": "でんきショック",
    "THUNDERBOLT": "10まんボルト", "THUNDER WAVE": "でんじは", "THUNDERWAVE": "でんじは",
    "THUNDER": "かみなり", "ROCK THROW": "いわおとし", "ROCKTHROW": "いわおとし",
    "EARTHQUAKE": "じしん", "FISSURE": "じわれ", "DIG": "あなをほる", "TOXIC": "どくどく",
    "CONFUSION": "ねんりき", "PSYCHIC": "サイコキネシス", "HYPNOSIS": "さいみんじゅつ",
    "MEDITATE": "ヨガのポーズ", "AGILITY": "こうそくいどう", "QUICK ATTACK": "でんこうせっか",
    "QUICKATTACK": "でんこうせっか", "RAGE": "いかり", "TELEPORT": "テレポート",
    "NIGHT SHADE": "ナイトヘッド", "NIGHTSHADE": "ナイトヘッド", "MIMIC": "ものまね",
    "SCREECH": "いやなおと", "DOUBLE TEAM": "かげぶんしん", "DOUBLETEAM": "かげぶんしん",
    "RECOVER": "じこさいせい", "HARDEN": "かたくなる", "MINIMIZE": "ちいさくなる",
    "SMOKESCREEN": "えんまく", "CONFUSE RAY": "あやしいひかり", "CONFUSERAY": "あやしいひかり",
    "WITHDRAW": "からにこもる", "DEFENSE CURL": "まるくなる", "DEFENSECURL": "まるくなる",
    "BARRIER": "バリアー", "LIGHT SCREEN": "ひかりのかべ", "LIGHTSCREEN": "ひかりのかべ",
    "HAZE": "くろいきり", "REFLECT": "リフレクター", "FOCUS ENERGY": "きあいだめ",
    "FOCUSENERGY": "きあいだめ", "BIDE": "がまん", "METRONOME": "ゆびをふる",
    "MIRROR MOVE": "オウムがえし", "MIRRORMOVE": "オウムがえし", "SELF-DESTRUCT": "じばく",
    "SELFDESTRUCT": "じばく", "EGG BOMB": "タマゴばくだん", "EGGBOMB": "タマゴばくだん",
    "LICK": "したでなめる", "SMOG": "スモッグ", "SLUDGE": "ヘドロこうげき",
    "BONE CLUB": "ホネこんぼう", "BONECLUB": "ホネこんぼう", "FIRE BLAST": "だいもんじ",
    "FIREBLAST": "だいもんじ", "WATERFALL": "たきのぼり", "CLAMP": "からではさむ",
    "SWIFT": "スピードスター", "SKULL BASH": "ロケットずつき", "SKULLBASH": "ロケットずつき",
    "SPIKE CANNON": "トゲキャノン", "SPIKECANNON": "トゲキャノン", "CONSTRICT": "からみつく",
    "AMNESIA": "ドわすれ", "KINESIS": "スプーンまげ", "SOFT-BOILED": "タマゴうみ",
    "SOFTBOILED": "タマゴうみ", "HI JUMP KICK": "とびひざげり", "HIJUMPKICK": "とびひざげり",
    "HIGH JUMP KICK": "とびひざげり", "HIGHJUMPKICK": "とびひざげり", "GLARE": "へびにらみ",
    "DREAM EATER": "ゆめくい", "DREAMEATER": "ゆめくい", "POISON GAS": "どくガス",
    "POISONGAS": "どくガス", "BARRAGE": "たまなげ", "LEECH LIFE": "きゅうけつ",
    "LEECHLIFE": "きゅうけつ", "LOVELY KISS": "あくまのキッス", "LOVELYKISS": "あくまのキッス",
    "SKY ATTACK": "ゴッドバード", "SKYATTACK": "ゴッドバード", "TRANSFORM": "へんしん",
    "BUBBLE": "あわ", "DIZZY PUNCH": "ピヨピヨパンチ", "DIZZYPUNCH": "ピヨピヨパンチ",
    "SPORE": "キノコのほうし", "FLASH": "フラッシュ", "PSYWAVE": "サイコウェーブ",
    "SPLASH": "はねる", "ACID ARMOR": "とける", "ACIDARMOR": "とける",
    "CRABHAMMER": "クラブハンマー", "EXPLOSION": "だいばくはつ", "FURY SWIPES": "みだれひっかき",
    "FURYPIPES": "みだれひっかき", "BONEMERANG": "ホネブーメラン", "REST": "ねむる",
    "ROCK SLIDE": "いわなだれ", "ROCKSLIDE": "いわなだれ", "HYPER FANG": "ひっさつまえば",
    "HYPERFANG": "ひっさつまえば", "SHARPEN": "かくばる", "CONVERSION": "テクスチャー",
    "TRI ATTACK": "トライアタック", "TRIATTACK": "トライアタック", "SUPER FANG": "いかりのまえば",
    "SUPERFANG": "いかりのまえば", "SLASH": "きりさく", "SUBSTITUTE": "みがわり",
    "STRUGGLE": "わるあがき",
    # Gen 2-9 Popular
    "SKETCH": "スケッチ", "TRIPLE KICK": "トリプルキック", "THIEF": "どろぼう",
    "SPIDER WEB": "クモのす", "MIND READER": "こころのめ", "NIGHTMARE": "あくむ",
    "FLAME WHEEL": "かえんぐるま", "SNORE": "いびき", "CURSE": "のろい", "FLAIL": "じたばた",
    "CONVERSION 2": "テクスチャー2", "AEROBLAST": "エアロブラスト", "COTTON SPORE": "わたほうし",
    "REVERSAL": "きしかいせい", "SPITE": "うらみ", "POWDER SNOW": "こなゆき", "PROTECT": "まもる",
    "MACH PUNCH": "マッハパンチ", "SCARY FACE": "こわいかお", "FAINT ATTACK": "だましうち",
    "FEINT ATTACK": "だましうち", "SWEET KISS": "てんしのキッス", "BELLY DRUM": "はらだいこ",
    "SLUDGE BOMB": "ヘドロばくだん", "MUD-SLAP": "どろかけ", "MUDSLAP": "どろかけ",
    "OCTAZOOKA": "オクタンほう", "SPIKES": "まきびし", "ZAP CANNON": "でんじほう",
    "FORESIGHT": "みやぶる", "DESTINY BOND": "みちづれ", "PERISH SONG": "ほろびのうた",
    "ICY WIND": "こごえるかぜ", "DETECT": "みきり", "BONE RUSH": "ホネラッシュ",
    "LOCK-ON": "ロックオン", "OUTRAGE": "げきりん", "SANDSTORM": "すなあらし",
    "GIGA DRAIN": "ギガドレイン", "ENDURE": "こらえる", "CHARM": "あまえる", "ROLLOUT": "ころがる",
    "FALSE SWIPE": "みねうち", "SWAGGER": "いばる", "MILK DRINK": "ミルクのみ",
    "SPARK": "スパーク", "FURY CUTTER": "れんぞくぎり", "STEEL WING": "はがねのつばさ",
    "MEAN LOOK": "くろいまなざし", "ATTRACT": "メロメロ", "SLEEP TALK": "ねごと",
    "HEAL BELL": "いやしのすず", "RETURN": "おんがえし", "PRESENT": "プレゼント",
    "FRUSTRATION": "やつあたり", "SAFEGUARD": "しんぴのまもり", "PAIN SPLIT": "いたみわけ",
    "SACRED FIRE": "せいなるほのお", "MAGNITUDE": "マグニチュード", "DYNAMIC PUNCH": "ばくれつパンチ",
    "MEGAPHORN": "メガホーン", "DRAGON BREATH": "りゅうのいぶき", "BATON PASS": "バトンタッチ",
    "ENCORE": "アンコール", "PURSUIT": "おいうち", "RAPID SPIN": "こうそくスピン",
    "SWEET SCENT": "あまいかおり", "IRON TAIL": "アイアンテール", "METAL CLAW": "メタルクロー",
    "VITAL THROW": "あてみなげ", "MORNING SUN": "あさのひざし", "SYNTHESIS": "こうごうせい",
    "MOONLIGHT": "つきのひかり", "HIDDEN POWER": "めざめるパワー", "CROSS CHOP": "クロスチョップ",
    "TWISTER": "たつまき", "RAIN DANCE": "あまごい", "SUNNY DAY": "にほんばれ",
    "CRUNCH": "かみくだく", "MIRROR COAT": "ミラーコート", "PSYCH UP": "じこあんじ",
    "EXTREME SPEED": "しんそく", "ANCIENT POWER": "げんしのちから", "SHADOW BALL": "シャドーボール",
    "FUTURE SIGHT": "みらいよち", "ROCK SMASH": "いわくだき", "WHIRLPOOL": "うずしお",
    "BEAT UP": "ふくろだたき", "FAKE OUT": "ねこだまし", "UPROAR": "さわぐ",
    "STOCKPILE": "たくわえる", "SPIT UP": "はきだす", "SWALLOW": "のみこむ",
    "HEAT WAVE": "ねっぷう", "HAIL": "あられ", "TORMENT": "ちょうはつ", "FLATTER": "おだてる",
    "WILL-O-WISP": "おにび", "MEMENTO": "おきみやげ", "FACADE": "からげんき",
    "FOCUS PUNCH": "きあいパンチ", "SMELLING SALTS": "きつけ", "SMELLINGSALT": "きつけ",
    "FOLLOW ME": "このゆびとまれ", "NATURE POWER": "しぜんのちから", "CHARGE": "じゅうでん",
    "TAUNT": "ちょうはつ", "HELPING HAND": "てだすけ", "TRICK": "トリック",
    "ROLE PLAY": "なりきり", "WISH": "ねがいごと", "ASSIST": "ねこのて",
    "INGRAIN": "ねをはる", "SUPERPOWER": "ばかぢから", "MAGIC COAT": "マジックコート",
    "RECYCLE": "リサイクル", "REVENGE": "リベンジ", "BRICK BREAK": "かわらわり",
    "YAWN": "あくび", "KNOCK OFF": "はたきおとす", "ENDEAVOR": "がむしゃら",
    "ERUPTION": "ふんか", "SKILL SWAP": "スキルスワップ", "IMPRISON": "ふういん",
    "REFRESH": "リフレッシュ", "GRUDGE": "おんねん", "SNATCH": "よこどり",
    "SECRET POWER": "ひみつのちから", "DIVE": "ダイビング", "ARM THRUST": "つっぱり",
    "CAMOUFLAGE": "ほのおのまい", "TAIL GLOW": "ほたるび", "LUSTER PURGE": "ラスターパージ",
    "MIST BALL": "ミストボール", "FEATHER DANCE": "フェザーダンス", "TEETER DANCE": "フラフラダンス",
    "BLAZE KICK": "ブレイズキック", "MUD SPORT": "どろあそび", "ICE BALL": "アイスボール",
    "NEEDLE ARM": "ニードルアーム", "SLACK OFF": "なまける", "HYPER VOICE": "ハイパーボイス",
    "POISON FANG": "どくどくのキバ", "CRUSH CLAW": "ブレイククロー", "BLAST BURN": "ブラストバーン",
    "HYDRO CANNON": "ハイドロカノン", "METEOR MASH": "コメットパンチ", "ASTONISH": "おどろかす",
    "WEATHER BALL": "ウェザーボール", "AROMATHERAPY": "アロマセラピー", "FAKE TEARS": "うそなき",
    "AIR CUTTER": "エアカッター", "OVERHEAT": "オーバーヒート", "ODOR SLEUTH": "かぎわける",
    "ROCK TOMB": "がんせきふうじ", "SILVER WIND": "ぎんいろのかぜ", "METAL SOUND": "きんぞくおん",
    "GRASS WHISTLE": "くさぶえ", "TICKLE": "くすぐる", "COSMIC POWER": "コスモパワー",
    "WATER SPOUT": "しおふき", "SIGNAL BEAM": "シグナルビーム", "SHADOW PUNCH": "シャドーパンチ",
    "EXTRASENSORY": "じんつうりき", "SKY UPPERCUT": "スカイアッパー", "SAND TOMB": "すなじごく",
    "SHEER COLD": "ぜったいれいど", "MUDDY WATER": "だくりゅう", "BULLET SEED": "タネマシンガン",
    "AERIAL ACE": "つばめがえし", "ICICLE SPEAR": "つららばり", "IRON DEFENSE": "てっぺき",
    "BLOCK": "とおせんぼう", "HOWL": "とおぼえ", "DRAGON CLAW": "ドラゴンクロー",
    "FRENZY PLANT": "ハードプラント", "BULK UP": "ビルドアップ", "BOUNCE": "とびはねる",
    "MUD SHOT": "マッドショット", "POISON TAIL": "ポイズンテール", "COVET": "ほしがる",
    "VOLT TACKLE": "ボルテッカー", "MAGICAL LEAF": "マジカルリーフ", "WATER SPORT": "みずあそび",
    "CALM MIND": "めいそう", "LEAF BLADE": "リーフブレード", "DRAGON DANCE": "りゅうのまい",
    "ROCK BLAST": "ロックブラスト", "SHOCK WAVE": "でんげきは", "WATER PULSE": "みずのはどう",
    "DOOM DESIRE": "はめつのねがい", "PSYCHO BOOST": "サイコブースト",
    # Gen 4-9
    "ROOST": "はねやすめ", "GRAVITY": "じゅうりょく", "MIRACLE EYE": "ミラクルアイ",
    "WAKE-UP SLAP": "めざましビンタ", "HAMMER ARM": "アームハンマー", "GYRO BALL": "ジャイロボール",
    "HEALING WISH": "いやしのねがい", "BRINE": "しおみず", "NATURAL GIFT": "しぜんのめぐみ",
    "FEINT": "フェイント", "PLUCK": "ついばむ", "TAILWIND": "おいかぜ", "ACUPRESSURE": "つぼをつく",
    "METAL BURST": "メタルバースト", "U-TURN": "とんぼがえり", "CLOSE COMBAT": "インファイト",
    "PAYBACK": "しっぺがえし", "ASSURANCE": "ダメおし", "EMBARGO": "さしおさえ",
    "FLING": "なげつける", "PSYCHO SHIFT": "サイコシフト", "TRUMP CARD": "きりふだ",
    "HEAL BLOCK": "かいふくふうじ", "WRING OUT": "しぼりとる", "POWER TRICK": "パワートリック",
    "GASTRO ACID": "いえき", "LUCKY CHANT": "おまじない", "ME FIRST": "さきどり",
    "COPYCAT": "まねっこ", "POWER SWAP": "パワースワップ", "GUARD SWAP": "ガードスワップ",
    "PUNISHMENT": "おしおき", "LAST RESORT": "とっておき", "WORRY SEED": "なやみのタネ",
    "SUCKER PUNCH": "ふいうち", "TOXIC SPIKES": "どくびし", "HEART SWAP": "ハートスワップ",
    "AQUA RING": "アクアリング", "MAGNET RISE": "でんじふゆう", "FLARE BLITZ": "フレアドライブ",
    "FORCE PALM": "はっけい", "AURA SPHERE": "はどうだん", "ROCK POLISH": "ロックカット",
    "POISON JAB": "どくづき", "DARK PULSE": "あくのはどう", "NIGHT SLASH": "つじぎり",
    "AQUA TAIL": "アクアテール", "SEED BOMB": "タネばくだん", "AIR SLASH": "エアスラッシュ",
    "X-SCISSOR": "シザークロス", "BUG BUZZ": "むしのさざめき", "DRAGON PULSE": "りゅうのはどう",
    "DRAGON RUSH": "ドラゴンダイブ", "POWER GEM": "パワージェム", "DRAIN PUNCH": "ドレインパンチ",
    "VACUUM WAVE": "しんくうは", "FOCUS BLAST": "きあいだま", "ENERGY BALL": "エナジーボール",
    "BRAVE BIRD": "ブレイブバード", "EARTH POWER": "だいちのちから", "SWITCHEROO": "すりかえ",
    "GIGA IMPACT": "ギガインパクト", "NASTY PLOT": "わるだくみ", "BULLET PUNCH": "バレットパンチ",
    "AVALANCHE": "ゆきなだれ", "ICE SHARD": "こおりのつぶて", "SHADOW CLAW": "シャドークロー",
    "THUNDER FANG": "かみなりのキバ", "ICE FANG": "こおりのキバ", "FIRE FANG": "ほのおのキバ",
    "SHADOW SNEAK": "かげうち", "MUD BOMB": "どろばくだん", "PSYCHO CUT": "サイコカッター",
    "ZEN HEADBUTT": "しねんのずつき", "MIRROR SHOT": "ミラーショット", "FLASH CANNON": "ラスターカノン",
    "ROCK CLIMB": "ロッククライム", "DEFOG": "きりばらい", "TRICK ROOM": "トリックルーム",
    "DRACO METEOR": "りゅうせいぐん", "DISCHARGE": "ほうでん", "LAVA PLUME": "ふんえん",
    "LEAF STORM": "リーフストーム", "POWER WHIP": "パワーウィップ", "ROCK WRECKER": "がんせきほう",
    "CROSS POISON": "クロスポイズン", "GUNK SHOT": "ダストシュート", "IRON HEAD": "アイアンヘッド",
    "MAGNET BOMB": "マグネットボム", "STONE EDGE": "ストーンエッジ", "CAPTIVATE": "ゆうわく",
    "STEALTH ROCK": "ステルスロック", "GRASS KNOT": "くさむすび", "CHATTER": "おしゃべり",
    "JUDGMENT": "さばきのつぶて", "BUG BITE": "むしくい", "CHARGE BEAM": "チャージビーム",
    "WOOD HAMMER": "ウッドハンマー", "AQUA JET": "アクアジェット", "ATTACK ORDER": "こうげきしれい",
    "DEFEND ORDER": "ぼうぎょしれい", "HEAL ORDER": "かいふくしれい", "HEAD SMASH": "モロバレル",
    "DOUBLE HIT": "ダブルアタック", "ROAR OF TIME": "ときのほうこう", "SPACIAL REND": "あくうせつだん",
    "MAGMA STORM": "マグマストーム", "DARK VOID": "ダークホール", "SEED FLARE": "シードフレア",
    "OMINOUS WIND": "あやしいかぜ", "SHADOW FORCE": "シャドーダイブ",
    "HONE CLAWS": "つめとぎ", "WIDE GUARD": "ワイドガード", "GUARD SPLIT": "ガードシェア",
    "POWER SPLIT": "パワーシェア", "WONDER ROOM": "ワンダールーム", "PSYSHOCK": "サイコショック",
    "VENOSHOCK": "ベノムショック", "AUTOTOMIZE": "ボディパージ", "RAGE POWDER": "いかりのこな",
    "TELEKINESIS": "テレキネシス", "MAGIC ROOM": "マジックルーム", "SMACK DOWN": "うちおとす",
    "STORM THROW": "やまあらし", "FLAME BURST": "はじけるほのお", "SLUDGE WAVE": "ヘドロウェーブ",
    "QUIVER DANCE": "ちょうのまい", "HEAVY SLAM": "ヘビーボンバー", "SYNCHRONOISE": "シンクロノイズ",
    "ELECTRO BALL": "エレキボール", "SOAK": "みずびたし", "FLAME CHARGE": "ニトロチャージ",
    "COIL": "とぐろをまく", "LOW SWEEP": "ローキック", "ACID SPRAY": "アシッドボム",
    "FOUL PLAY": "イカサマ", "SIMPLE BEAM": "シンプルビーム", "ENTRAINMENT": "なかまづくり",
    "AFTER YOU": "おさきにどうぞ", "ROUND": "りんしょう", "ECHOED VOICE": "エコーボイス",
    "CHIP AWAY": "ならし", "CLEAR SMOG": "クリアスモッグ", "STORED POWER": "アシストパワー",
    "QUICK GUARD": "ファストガード", "ALLY SWITCH": "サイドチェンジ", "SCALD": "ねっとう",
    "SHELL SMASH": "からをやぶる", "HEAL PULSE": "いやしのはどう", "HEX": "たたりめ",
    "SKY DROP": "フリーフォール", "SHIFT GEAR": "ギアチェンジ", "CIRCLE THROW": "ともえなげ",
    "INCINERATE": "やきつくす", "QUASH": "さきおくり", "ACROBATICS": "アクロバット",
    "REFLECT TYPE": "ミラータイプ", "RETALIATE": "かたきうち", "FINAL GAMBIT": "いのちがけ",
    "BESTOW": "ギフトパス", "INFERNO": "れんごく", "WATER PLEDGE": "みずのちかい",
    "FIRE PLEDGE": "ほのおのちかい", "GRASS PLEDGE": "くさのちかい", "VOLT SWITCH": "ボルトチェンジ",
    "STRUGGLE BUG": "むしのていこう", "BULLDOZE": "じならし", "FROST BREATH": "こおりのいぶき",
    "DRAGON TAIL": "ドラゴンテール", "WORK UP": "ふるいたてる", "ELECTROWEB": "エレキネット",
    "WILD CHARGE": "ワイルドボルト", "DRILL RUN": "ドリルライナー", "DUAL CHOP": "ダブルチョップ",
    "HEART STAMP": "ハートスタンプ", "HORN LEECH": "ウッドホーン", "SACRED SWORD": "せいなるつるぎ",
    "RAZOR SHELL": "シェルブレード", "HEAT CRASH": "ヒートスタンプ", "LEAF TORNADO": "グラスミキサー",
    "STEAMROLLER": "ハードローラー", "COTTON GUARD": "コットンガード", "NIGHT DAZE": "ナイトバースト",
    "TAIL SLAP": "スイープビンタ", "HURRICANE": "ぼうふう", "HEAD CHARGE": "アフロブレイク",
    "GEAR GRIND": "ギアソーサー", "SEARING SHOT": "かえんだん", "TECHNO BUST": "テクノバスター",
    "RELIC SONG": "いにしえのうた", "SECRET SWORD": "しんぴのつるぎ", "GLACIATE": "こごえるせかい",
    "BOLT STRIKE": "らいげき", "BLUE FLARE": "あおいほのお", "FIERY DANCE": "ほのおのまい",
    "FREEZE SHOCK": "フリーズボルト", "ICE BURN": "コールドフレア", "SNARL": "バークアウト",
    "ICICLE CRASH": "つららおとし", "V-CREATE": "Vジェネレート", "FUSION FLARE": "クロスフレイム",
    "FUSION BOLT": "クロスサンダー",
    # Gen 6-9
    "FLYING PRESS": "フライングプレス", "BELCH": "ゲップ", "ROTOTILLER": "たがやす",
    "STICKY WEB": "ねばねばネット", "FELL STINGER": "とどめばり", "PHANTOM FORCE": "ゴーストダイブ",
    "TRICK-OR-TREAT": "ハロウィン", "NOBLE ROAR": "おたけび", "ION DELUGE": "プラズマシャワー",
    "PARABOLIC CHARGE": "パラボラチャージ", "FOREST'S CURSE": "もりののろい", "PETAL BLIZZARD": "はなふぶき",
    "FREEZE-DRY": "フリーズドライ", "DISARMING VOICE": "チャームボイス", "PARTING SHOT": "すてぜりふ",
    "TOPSY-TURVY": "ひっくりかえす", "DRAINING KISS": "ドレインキッス", "CRAFTY SHIELD": "トリックガード",
    "FLOWER SHIELD": "フラワーガード", "GRASSY TERRAIN": "グラスフィールド", "MISTY TERRAIN": "ミストフィールド",
    "ELECTRIFY": "そうでん", "PLAY ROUGH": "じゃれつく", "FAIRY WIND": "ようせいのかぜ",
    "MOONBLAST": "ムーンフォース", "BOOMBURST": "ばくおんぱ", "FAIRY LOCK": "フェアリーロック",
    "KING'S SHIELD": "キングシールド", "PLAY NICE": "なかよくする", "CONFIDE": "ないしょばなし",
    "WATER SHURIKEN": "みずしゅりけん", "MYSTICAL FIRE": "マジカルフレイム", "SPIKY SHIELD": "ニードルガード",
    "AROMATIC MIST": "アロマミスト", "EERIE IMPULSE": "かいでんぱ", "VENOM DRENCH": "ベノムトラップ",
    "POWDER": "ふんじん", "GEOMANCY": "ジオコントロール", "MAGNETIC FLUX": "じばそうさ",
    "HAPPY HOUR": "ハッピータイム", "ELECTRIC TERRAIN": "エレキフィールド", "DAZZLING GLEAM": "マジカルシャイン",
    "CELEBRATE": "おいわい", "HOLD HANDS": "てをつなぐ", "BABY-DOLL EYES": "つぶらなひとみ",
    "NUZZLE": "ほっぺすりすり", "HOLD BACK": "てかげん", "INFESTATION": "まとわりつく",
    "POWER-UP PUNCH": "グロウパンチ", "OBLIVION WING": "デスウイング", "THOUSAND ARROWS": "サウザンアロー",
    "THOUSAND WAVES": "サウザンウェーブ", "LAND'S WRATH": "グランドフォース", "LIGHT OF RUIN": "破滅の光",
    "ORIGIN PULSE": "こんげんのはどう", "PRECIPICE BLADES": "だんがいのつるぎ", "DRAGON ASCENT": "ガリョウテンセイ",
    "HYPERSPACE HOLE": "いじげんホール", "HYPERSPACE FURY": "いじげんラッシュ",
}

# ---------------------------------------------------------------------------
# Items (Gen 1-9 & Rom Hacks)
# ---------------------------------------------------------------------------
ITEM_DICTIONARY: Dict[str, str] = {
    "MASTER BALL": "マスターボール", "ULTRA BALL": "ハイパーボール", "GREAT BALL": "スーパーボール",
    "POKÉ BALL": "モンスターボール", "POKE BALL": "モンスターボール", "SAFARI BALL": "サファリボール",
    "NET BALL": "ネットボール", "DIVE BALL": "ダイブボール", "NEST BALL": "ネストボール",
    "REPEAT BALL": "リピートボール", "TIMER BALL": "タイマーボール", "LUXURY BALL": "ゴージャスボール",
    "PREMIER BALL": "プレミアボール", "DUSK BALL": "ダークボール", "HEAL BALL": "ヒールボール",
    "QUICK BALL": "クイックボール", "CHERISH BALL": "プレシャスボール", "FAST BALL": "スピードボール",
    "LEVEL BALL": "レベルボール", "LURE BALL": "ルアーボール", "HEAVY BALL": "ヘビーボール",
    "LOVE BALL": "ラブラブボール", "FRIEND BALL": "フレンドボール", "MOON BALL": "ムーンボール",
    "SPORT BALL": "コンペボール", "PARK BALL": "パークボール", "BEAST BALL": "ウルトラボール",
    "POTION": "キズぐすり", "ANTIDOTE": "どくけし", "BURN HEAL": "やけどなおし",
    "ICE HEAL": "こおりなおし", "AWAKENING": "ねむけざまし", "PARALYZE HEAL": "まひなおし",
    "FULL RESTORE": "かいふくのくすり", "MAX POTION": "まんたんのくすり", "HYPER POTION": "すごいキズぐすり",
    "SUPER POTION": "いいキズぐすり", "FULL HEAL": "なんでもなおし", "REVIVE": "げんきのかけら",
    "MAX REVIVE": "げんきのかたまり", "FRESH WATER": "おいしいみず", "SODA POP": "サイコソーダ",
    "LEMONADE": "ミックスオレ", "MOOMOO MILK": "モーモーミルク", "ENERGY POWDER": "ちからのこな",
    "ENERGY ROOT": "ちからのねっこ", "HEAL POWDER": "ばんのうごな", "REVIVAL HERB": "ふっかつのそう",
    "ETHER": "ピーピーエイド", "MAX ETHER": "ピーピーリカバー", "ELIXIR": "ピーピーエイダー",
    "MAX ELIXIR": "ピーピーマックス", "PP UP": "ポイントアップ", "PP MAX": "ポイントマックス",
    "RARE CANDY": "ふしぎなアメ", "HP UP": "マックスアップ", "PROTEIN": "タウリン",
    "IRON": "ブロムヘキシン", "CARBOS": "インドメタシン", "CALCIUM": "リゾチウム",
    "ZINC": "キトサン", "GUARD SPEC.": "エフェクトガード", "DIRE HIT": "クリティカッター",
    "X ATTACK": "プラスパワー", "X-ATTACK": "プラスパワー", "X DEFEND": "ディフェンダー",
    "X-DEFEND": "ディフェンダー", "X DEFENSE": "ディフェンダー", "X-DEFENSE": "ディフェンダー",
    "X SPEED": "スピーダー", "X-SPEED": "スピーダー", "X ACCURACY": "ヨクアタール",
    "X-ACCURACY": "ヨクアタール", "X SPECIAL": "スペシャルアップ", "X-SPECIAL": "スペシャルアップ",
    "X SP. ATK": "スペシャルアップ", "X SP. DEF": "スペシャルガード",
    "POKÉ DOLL": "ピッピにんぎょう", "POKE DOLL": "ピッピにんぎょう", "FLUFFY TAIL": "エネコのしっぽ",
    "SUPER REPEL": "シルバースプレー", "MAX REPEL": "ゴールドスプレー", "ESCAPE ROPE": "あなぬけのヒモ",
    "REPEL": "むしよけスプレー", "SUN STONE": "たいようのいし", "MOON STONE": "つきのいし",
    "FIRE STONE": "ほのおのいし", "THUNDER STONE": "かみなりのいし", "WATER STONE": "みずのいし",
    "LEAF STONE": "リーフのいし", "SHINY STONE": "ひかりのいし", "DUSK STONE": "やみのいし",
    "DAWN STONE": "めざめのいし", "ICE STONE": "こおりのいし", "OVAL STONE": "まんまるいし",
    "EXP. SHARE": "がくしゅうそうち", "EXP SHARE": "がくしゅうそうち", "LEFTOVERS": "たべのこし",
    "CHOICE BAND": "こだわりハチマキ", "CHOICE SPECS": "こだわりメガネ", "CHOICE SCARF": "こだわりスカーフ",
    "LIFE ORB": "いのちのたま", "FOCUS SASH": "きあいのタスキ", "FOCUS BAND": "きあいのハチマキ",
    "ASSAULT VEST": "とつげきチョッキ", "LUCKY EGG": "しあわせタマゴ", "AMULET COIN": "おまもりこばん",
    "SOOTHE BELL": "やすらぎのすず", "EVIOLITE": "しんかのきせき", "ROCKY HELMET": "ゴツゴツメット",
    "BLACK SLUDGE": "くろいヘドロ", "AIR BALLOON": "ふうせん", "SAFETY GOGGLES": "ぼうじんゴーグル",
    "WEAKNESS POLICY": "じゃくてんほけん", "EXPERT BELT": "たつじんのおび", "MUSCLE BAND": "ちからのハチマキ",
    "WISE GLASSES": "ものしりメガネ", "WIDE LENS": "こうかくレンズ", "ZOOM LENS": "フォーカスレンズ",
    "SCOPE LENS": "ピントレンズ", "LIGHT CLAY": "ひかりのねんど", "TERRAIN EXTENDER": "グランドコート",
    "OLD ROD": "ボロのつりざお", "GOOD ROD": "いいつりざお", "SUPER ROD": "すごいつりざお",
    "BICYCLE": "じてんしゃ", "BIKE": "じてんしゃ", "TOWN MAP": "タウンマップ",
    "VS SEEKER": "バトルサーチャー", "ITEMFINDER": "ダウジングマシン", "DOWSING MCHN": "ダウジングマシン",
    "COIN CASE": "コインケース", "OLD SEA MAP": "ふるびたかいず", "MYSTIC TICKET": "しんぴのチケット",
    "AURORA TICKET": "オーロラチケット", "SS TICKET": "サントアンヌごうチケット",
}

# Add Mega Stones into Items
ITEM_DICTIONARY.update(MEGA_STONES_DICTIONARY)

# ---------------------------------------------------------------------------
# Abilities
# ---------------------------------------------------------------------------
ABILITY_DICTIONARY: Dict[str, str] = {
    "STENCH": "あくしゅう", "DRIZZLE": "あめふらし", "SPEED BOOST": "かそく",
    "BATTLE ARMOR": "カブトアーマー", "STURDY": "がんじょう", "DAMP": "しめりけ",
    "LIMBER": "じゅうなん", "SAND VEIL": "すながくれ", "STATIC": "せいでんき",
    "VOLT ABSORB": "ちくでん", "WATER ABSORB": "ちょすい", "OBLIVIOUS": "どんかん",
    "CLOUD NINE": "ノーてんき", "COMPOUND EYES": "ふくがん", "COMPOUNDEYES": "ふくがん",
    "INSOMNIA": "ふみん", "COLOR CHANGE": "へんしょく", "IMMUNITY": "めんえき",
    "FLASH FIRE": "もらいび", "SHIELD DUST": "りんぷん", "OWN TEMPO": "マイペース",
    "SUCTION CUPS": "きゅうばん", "INTIMIDATE": "いかく", "SHADOW TAG": "かげふみ",
    "ROUGH SKIN": "さめはだ", "WONDER GUARD": "ふしぎなまもり", "LEVITATE": "ふゆう",
    "EFFECT SPORE": "ほうし", "SYNCHRONIZE": "シンクロ", "CLEAR BODY": "クリアボディ",
    "NATURAL CURE": "しぜんかいふく", "LIGHTNING ROD": "ひらいしん", "LIGHTNINGROD": "ひらいしん",
    "SERENE GRACE": "てんのめぐみ", "SWIFT SWIM": "すいすい", "CHLOROPHYLL": "ようりょくそ",
    "ILLUMINATE": "はっこう", "TRACE": "トレース", "HUGE POWER": "ちからもち",
    "POISON POINT": "どくのトゲ", "INNER FOCUS": "せいしんりょく", "MAGMA ARMOR": "マグマのよろい",
    "WATER VEIL": "みずのベール", "MAGNET PULL": "じりょく", "SOUNDPROOF": "ぼうおん",
    "RAIN DISH": "あめうけざら", "SAND STREAM": "すなおこし", "PRESSURE": "プレッシャー",
    "THICK FAT": "あついしぼう", "EARLY BIRD": "はやおき", "FLAME BODY": "ほのおのからだ",
    "RUN AWAY": "にげあし", "KEEN EYE": "するどいめ", "HYPER CUTTER": "かいりきバサミ",
    "PICKUP": "ものひろい", "TRUANT": "なまけ", "HUSTLE": "はりきり",
    "CUTE CHARM": "メロメロボディ", "PLUS": "プラス", "MINUS": "マイナス",
    "FORECAST": "てんきや", "STICKY HOLD": "ねんちゃく", "SHED SKIN": "だっぴ",
    "GUTS": "こんじょう", "MARVEL SCALE": "ふしぎなうろこ", "LIQUID OOZE": "ヘドロえき",
    "OVERGROW": "しんりょく", "BLAZE": "もうか", "TORRENT": "げきりゅう",
    "SWARM": "むしのしらせ", "ROCK HEAD": "いしあたま", "DROUGHT": "ひでり",
    "ARENA TRAP": "ありじごく", "VITAL SPIRIT": "やるき", "WHITE SMOKE": "しろいけむり",
    "PURE POWER": "ヨガパワー", "SHELL ARMOR": "シェルアーマー", "AIR LOCK": "エアロック",
    # Modern Popular Abilities (CFRU / Radical Red / Unbound)
    "TANGLED FEET": "ちどりあし", "MOTOR DRIVE": "でんきエンジン", "RIVALRY": "とうそうしん",
    "STEADFAST": "ふくつのこころ", "SNOW CLOAK": "ゆきがくれ", "GLUTTONY": "くいしんぼう",
    "ANGER POINT": "いかりのつぼ", "UNBURDEN": "かるわざ", "HEATPROOF": "たいねつ",
    "SIMPLE": "たんじゅん", "DRY SKIN": "かんそうはだ", "DOWNLOAD": "ダウンロード",
    "IRON FIST": "てつのこぶし", "POISON HEAL": "ポイズンヒール", "ADAPTABILITY": "てきおうりょく",
    "SKILL LINK": "スキルリンク", "HYDRATION": "うるおいボディ", "SOLAR POWER": "サンパワー",
    "QUICK FEET": "はやあし", "NORMALIZE": "ノーマルスキン", "SNIPER": "スナイパー",
    "MAGIC GUARD": "マジックガード", "NO GUARD": "ノーガード", "STALL": "あとだし",
    "TECHNICIAN": "テクニシャン", "LEAF GUARD": "リーフガード", "MOLD BREAKER": "かたやぶり",
    "SUPER LUCK": "きょううん", "AFTERMATH": "ゆうばく", "ANTICIPATION": "きけんよち",
    "FOREWARN": "よちむ", "UNAWARE": "てんねん", "TINTED LENS": "いろめがね",
    "FILTER": "フィルター", "SOLID ROCK": "ハードロック", "ICE BODY": "アイスボディ",
    "POWER SPOT": "パワースポット", "PROTEAN": "へんげんじざい", "LIBERO": "リベロ",
    "BEAST BOOST": "ビーストブースト", "INTREPID SWORD": "ふとうのつるぎ", "DAUNTLESS SHIELD": "ふくつのたて",
    "SUPREME OVERLORD": "そうだいしょう", "PROTOSYNTHESIS": "こだいかっせい", "QUARK DRIVE": "クォークチャージ",
}

# Integrate Expanded Gen 4-9 Species, Gen 1-8 Moves, Gen 3-8 Abilities, and Gen 1-8 Items
POKEMON_DICTIONARY.update(SPECIES_GEN4_TO_GEN9)
MOVE_DICTIONARY.update(EXPANDED_MOVES)
ABILITY_DICTIONARY.update(EXPANDED_ABILITIES)
ITEM_DICTIONARY.update(EXPANDED_ITEMS)

# ---------------------------------------------------------------------------
# Pre-computed Normalized Dictionaries for Fast O(1) Fuzzy Lookup
# ---------------------------------------------------------------------------
NORMALIZED_SPECIES = {normalize_key(k): v for k, v in POKEMON_DICTIONARY.items()}
NORMALIZED_MOVES = {normalize_key(k): v for k, v in MOVE_DICTIONARY.items()}
NORMALIZED_ITEMS = {normalize_key(k): v for k, v in ITEM_DICTIONARY.items()}
NORMALIZED_ABILITIES = {normalize_key(k): v for k, v in ABILITY_DICTIONARY.items()}
NORMALIZED_TYPES = {normalize_key(k): v for k, v in TYPE_DICTIONARY.items()}
NORMALIZED_NATURES = {normalize_key(k): v for k, v in NATURE_DICTIONARY.items()}
NORMALIZED_MENUS = {normalize_key(k): v for k, v in MENU_DICTIONARY.items()}
NORMALIZED_ITEM_DESCRIPTIONS = {normalize_key(k): v for k, v in OFFICIAL_ITEM_DESCRIPTIONS.items()}
NORMALIZED_ITEM_NAME_DEFAULT_DESCRIPTIONS = {normalize_key(k): v for k, v in ITEM_NAME_DEFAULT_DESCRIPTIONS.items()}

# Combined dictionary
GLOBAL_NORMALIZED: Dict[str, str] = {}
for d in [NORMALIZED_MENUS, NORMALIZED_SPECIES, NORMALIZED_MOVES, NORMALIZED_ITEMS,
          NORMALIZED_ABILITIES, NORMALIZED_TYPES, NORMALIZED_NATURES]:
    GLOBAL_NORMALIZED.update(d)


# ---------------------------------------------------------------------------
# Algorithmic Item & Move Handlers (Mega Stones, TMs, HMs, Z-Crystals)
# ---------------------------------------------------------------------------
def translate_special_pattern(text: str) -> Optional[str]:
    """Handles programmatic naming conventions like TMs, HMs, Mega Stones, Z-Crystals."""
    norm = normalize_key(text)

    # 1. TMs and HMs (e.g. "TM01", "TM 01 Focus Punch", "HM03 Surf")
    tm_match = re.match(r"^(?:TM|わざマシン)\s*0*([0-9]{1,3})(?:\s+(.*))?$", text, re.IGNORECASE)
    if tm_match:
        num = int(tm_match.group(1))
        sub_move = tm_match.group(2)
        if sub_move:
            sub_trans = auto_translate_text(sub_move, "moves") or sub_move
            return f"わざマシン{num:02d} {sub_trans}"
        return f"わざマシン{num:02d}"

    hm_match = re.match(r"^(?:HM|ひでんマシン)\s*0*([0-9]{1,2})(?:\s+(.*))?$", text, re.IGNORECASE)
    if hm_match:
        num = int(hm_match.group(1))
        sub_move = hm_match.group(2)
        if sub_move:
            sub_trans = auto_translate_text(sub_move, "moves") or sub_move
            return f"ひでんマシン{num:02d} {sub_trans}"
        return f"ひでんマシン{num:02d}"

    # 2. Mega Stones (Any custom or standard Mega Stone ending in 'ite', 'ite X', 'ite Y')
    if norm in NORMALIZED_ITEMS:
        return NORMALIZED_ITEMS[norm]

    mega_x_match = re.match(r"^(.+)ITE\s*X$", norm)
    if mega_x_match:
        stem = mega_x_match.group(1)
        base_poke = find_best_pokemon_stem(stem)
        if base_poke:
            return f"{base_poke}ナイトX"

    mega_y_match = re.match(r"^(.+)ITE\s*Y$", norm)
    if mega_y_match:
        stem = mega_y_match.group(1)
        base_poke = find_best_pokemon_stem(stem)
        if base_poke:
            return f"{base_poke}ナイトY"

    if norm.endswith("ITE"):
        stem = norm[:-3]
        base_poke = find_best_pokemon_stem(stem)
        if base_poke:
            return f"{base_poke}ナイト"

    # 3. Z-Crystals (e.g. Normalium Z, Firium Z)
    z_match = re.match(r"^([A-Z]+)IUM\s*Z$", norm)
    if z_match:
        type_prefix = z_match.group(1)
        if type_prefix in NORMALIZED_TYPES:
            return f"{NORMALIZED_TYPES[type_prefix]}Z"

    # 4. Nature Mints (e.g. Adamant Mint, Jolly Mint)
    mint_match = re.match(r"^([A-Z]+)\s+MINT$", norm)
    if mint_match:
        nat = mint_match.group(1)
        if nat in NORMALIZED_NATURES:
            return f"{NORMALIZED_NATURES[nat]}ミント"

    # 5. Unown forms (e.g. Unown B, UnownB)
    unown_match = re.match(r"^UNOWN\s*([A-Z!\?])$", norm)
    if unown_match:
        return f"アンノーン{unown_match.group(1)}"

    # 6. Z-Moves (e.g. Z-Move 34)
    zmove_match = re.match(r"^ZMOVE\s*([0-9]+)$", norm)
    if zmove_match:
        return f"Zワザ{zmove_match.group(1)}"

    # 7. TRs (Technical Records)
    tr_match = re.match(r"^TR\s*0*([0-9]{1,2})$", norm)
    if tr_match:
        num = int(tr_match.group(1))
        return f"わざレコード{num:02d}"

    # 8. Female / Gender forms (e.g. HippowdonF, Unfezant-F, Meowstic-F)
    fem_match = re.match(r"^([A-Z0-9]+)[-_]?F$", norm)
    if fem_match:
        stem = fem_match.group(1)
        if stem in NORMALIZED_SPECIES:
            return NORMALIZED_SPECIES[stem]

    # 9. Vivillon regional forms (e.g. Vivillon-A, VivilloMod, etc.)
    if norm.startswith("VIVILLO"):
        return "ビビヨン"

    # 10. Algorithmic item descriptions
    hp_match = re.search(r"Restores\s+the\s+HP\s+of\s+one\s+Pok[eéヒ]mon\s+by\s+([0-9]+)\s+points", text, re.IGNORECASE)
    if hp_match:
        pts = hp_match.group(1)
        return f"ポケモン1ぴきの HPを\n{pts}だけ かいふくする。"

    repel_match = re.search(r"Prevents\s+weak\s+wild\s+Pok[eéヒ]mon\s+from\s+appearing\s+for\s+([0-9]+)\s+steps", text, re.IGNORECASE)
    if repel_match:
        steps = repel_match.group(1)
        return f"つかうと {steps}ぽの あいだ\nやせい ポケモンが\nまったく でてこなくなる。"

    pp_match = re.search(r"Restores\s+the\s+PP\s+of\s+a\s+selected\s+move\s+by\s+([0-9]+)\s+points", text, re.IGNORECASE)
    if pp_match:
        pts = pp_match.group(1)
        return f"えらんだ わざの PPを\n{pts}だけ かいふくする。"

    return None


def auto_translate_item_description(desc: str, item_name: str = "") -> Optional[str]:
    """High-precision item description translator using name-context and patterns."""
    if not desc:
        return ""
    norm = normalize_key(desc)
    if norm in NORMALIZED_ITEM_DESCRIPTIONS:
        return NORMALIZED_ITEM_DESCRIPTIONS[norm]

    # Name-based context fallback
    if item_name:
        it_norm = normalize_key(item_name)
        if it_norm in NORMALIZED_ITEM_NAME_DEFAULT_DESCRIPTIONS:
            return NORMALIZED_ITEM_NAME_DEFAULT_DESCRIPTIONS[it_norm]

        if it_norm.endswith("ITE") or "MEGA" in it_norm or it_norm.endswith("ITEX") or it_norm.endswith("ITEY"):
            base_p = find_best_pokemon_stem(it_norm.replace("ITEX", "").replace("ITEY", "").replace("ITE", ""))
            if base_p:
                return f"{base_p}に もたせると\nメガシンカ できる\nふしぎな いし。"
            return "ポケモンに もたせると\nメガシンカ できる\nふしぎな いし。"

        if re.match(r"^(?:TM|HM)\s*0*([0-9]+)$", it_norm):
            return "ポケモンに わざを おしえる\nたいせつな マシン。\nなんどでも つかえる。"

        if "BERRY" in it_norm:
            b_trans = NORMALIZED_ITEMS.get(it_norm, "きのみ")
            return f"ポケモンに もたせると\nピンチのときに やくだつ\n{b_trans}。"

        if "MAIL" in it_norm:
            return "ポケモンに もたせて\nてがみを おくることが\nできる。"

        if "FOSSIL" in it_norm or "AMBER" in it_norm:
            return "たいこの ポケモンの カセキ。\nさいせい させることが できる。"

        if "SHARD" in it_norm:
            return "たいこの どうぐの いちぶと\nいわれている かけら。"

        if "FLUTE" in it_norm:
            return "ふきならすと こうかのある\nガラスせいの ビードロ。"

        if "SCARF" in it_norm or "BAND" in it_norm:
            return "もたせると コンテストで\nアピールしやすくなる バンダナ。"

        if "BALL" in it_norm:
            return "ポケモンを つかまえるための\nカプセルしきの ボール。"

        if "ORB" in it_norm:
            return "ふしぎな ちからを ひめた\nたいせつな たま。"

    # Description text regex patterns
    pat = translate_special_pattern(desc)
    if pat:
        return pat

    return None


def find_best_pokemon_stem(stem: str) -> Optional[str]:
    """Matches stem like CHARIZARD, BLASTOISIN, VENUSAUR back to Pokemon Japanese name."""
    if stem in NORMALIZED_SPECIES:
        return NORMALIZED_SPECIES[stem]

    # Partial prefix match
    for p_norm, j_name in NORMALIZED_SPECIES.items():
        if p_norm.startswith(stem) or stem.startswith(p_norm[:len(stem) - 1]):
            return j_name
    return None


# ---------------------------------------------------------------------------
# Free Google Translate API Engine (Zero dependencies using urllib)
# ---------------------------------------------------------------------------
import os

# ---------------------------------------------------------------------------
# Persistent Translation Cache
# ---------------------------------------------------------------------------
_CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".translation_cache.json"))
_TRANSLATION_CACHE: Dict[str, str] = {}

def _load_translation_cache() -> None:
    global _TRANSLATION_CACHE
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _TRANSLATION_CACHE.update(data)
        except Exception:
            pass

_CACHE_LOCK = threading.Lock()

def _save_translation_cache() -> None:
    try:
        with _CACHE_LOCK:
            snapshot = dict(_TRANSLATION_CACHE)
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Initialize cache on import
_load_translation_cache()


def _preprocess_for_mt(raw_text: str) -> Tuple[str, List[str], str, str, str]:
    """Prepares an English GBA string for natural sentence-level machine translation.
    
    - Extracts optional speaker prefix ("Mom: ", "Prof. Redwood: ") and leading [COLOR:XX].
    - Replaces mid-sentence visual line-wraps (\n and [WAIT]) with spaces so English phrases
      ("should\nhelp", "get\nout") are not split in half!
    - Replaces [CLEAR] page breaks with \n so each page is translated as a complete sentence.
    - Strips mid-sentence highlight color toggles while keeping buffer tags ([PLAYER], [BUFFER_1], etc.).
    """
    text = raw_text.strip()
    trailing_suffix = ""
    if text.endswith("[EXT:09]"):
        trailing_suffix = "[EXT:09]"
        text = text[: -len("[EXT:09]")].rstrip()
    if text.endswith("[CLEAR]"):
        trailing_suffix = "[CLEAR]" + trailing_suffix
        text = text[: -len("[CLEAR]")].rstrip()

    speaker_prefix = ""
    leading_color = ""

    # Check speaker prefix: e.g. "Mom: [COLOR:04]Those Running Shoes..."
    sp_match = re.match(
        r"^((?:\[COLOR:[0-9A-Fa-f]{2}\])?\s*([A-Za-z][A-Za-z0-9\.\'\s]{0,18}?)\s*:\s*(\[COLOR:[0-9A-Fa-f]{2}\])?\s*)(.*)$",
        text,
        re.DOTALL,
    )
    if sp_match:
        raw_speaker = sp_match.group(2).strip()
        c_tag = sp_match.group(3) or ""
        norm_sp = raw_speaker.upper()
        jp_sp = SPEAKER_NAME_MAP.get(norm_sp, raw_speaker)
        speaker_prefix = f"{jp_sp}: "
        leading_color = c_tag
        text = sp_match.group(4).strip()
    else:
        c_match = re.match(r"^((?:\[(?:COLOR|EXT):[0-9A-Fa-f:]+\])+)\s*(.*)$", text, re.DOTALL)
        if c_match:
            leading_color = c_match.group(1)
            text = c_match.group(2).strip()

    # Strip remaining inline [COLOR:XX], [HL:XX], [EXT:...] tags inside body so they don't break sentences
    text = re.sub(r"\[(?:COLOR|HL|EXT|PAUSE|BTN|SYM):[^\]]+\]", "", text)

    # Split into pages by [CLEAR], and within each page join visual line wraps (\n, [WAIT]) with a single space
    pages = [p.strip() for p in text.split("[CLEAR]") if p.strip()]
    clean_pages = []
    for p in pages:
        p_flat = p.replace("[WAIT]", " ").replace("\r", " ").replace("\n", " ")
        p_flat = re.sub(r"\s{2,}", " ", p_flat).strip()
        if p_flat:
            clean_pages.append(p_flat)

    joined_sentences = "\n".join(clean_pages)

    # Protect only variable buffer tags ([PLAYER], [RIVAL], [BUFFER_1], [BUFFER_2], [BUF:XX])
    buf_pattern = re.compile(r"(\[(?:PLAYER|RIVAL|BUFFER_1|BUFFER_2|BUF:[0-9A-Fa-f]{2})\])", re.IGNORECASE)
    tags: List[str] = []

    def replacer(match):
        idx = len(tags)
        tags.append(match.group(0))
        return f" XTAG{idx}X "

    protected = buf_pattern.sub(replacer, joined_sentences)
    return protected, tags, speaker_prefix, leading_color, trailing_suffix


def _postprocess_from_mt(
    translated_raw: str,
    tags: List[str],
    speaker_prefix: str,
    leading_color: str,
    trailing_suffix: str,
) -> str:
    """Restores buffer tags, [CLEAR] page breaks, speaker prefix, and color tags."""
    restored = translated_raw
    for idx, tag in enumerate(tags):
        tag_regex = re.compile(rf"\s*XTAG\s*{idx}\s*X\s*", re.IGNORECASE)
        restored = tag_regex.sub(tag, restored)

    restored = restored.replace(" !", "!").replace(" ?", "?").replace(" 、", "、").replace(" 。", "。").strip()
    # Convert \n (which separated [CLEAR] pages during MT) back to [CLEAR]
    pages = [p.strip() for p in restored.split("\n") if p.strip()]
    body = "[CLEAR]".join(pages)
    return f"{speaker_prefix}{leading_color}{body}{trailing_suffix}"


def _sanitize_cached_translation(cached: str) -> str:
    """Cleans legacy cached translations that had mid-sentence \\n artifacts."""
    if "\n" not in cached:
        return cached
    s = re.sub(r"の\n(から|に|で|を|へ)", r"\1", cached)
    s = re.sub(r"を\nに", "を", s)
    s = re.sub(r"\n([のをにがでとへもは])", r"\1", s)
    s = s.replace("\r\n", "").replace("\n", "")
    return s


def translate_online(text: str, timeout: float = 3.5) -> Optional[str]:
    """Translates arbitrary English text into Japanese using Google Translate public endpoint.
    Safeguards all GBA control tags ([PLAYER], [RIVAL], [CLEAR]) during translation.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""

    if clean_text in _TRANSLATION_CACHE:
        cached = _TRANSLATION_CACHE[clean_text]
        if "\nを" not in cached and "\nの" not in cached and "\nに" not in cached:
            return _sanitize_cached_translation(cached)

    protected_text, tags, speaker_prefix, leading_color, trailing_suffix = _preprocess_for_mt(clean_text)

    # Encode query
    query = urllib.parse.quote(protected_text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ja&dt=t&q={query}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Recombine translation pieces
        translated_segments = []
        if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if part and len(part) > 0 and part[0]:
                    translated_segments.append(part[0])

        raw_translated = "".join(translated_segments)
        restored = _postprocess_from_mt(raw_translated, tags, speaker_prefix, leading_color, trailing_suffix)

        _TRANSLATION_CACHE[clean_text] = restored
        _save_translation_cache()
        return restored
    except Exception:
        # Network failed or timed out, fallback to sanitized cache if present
        if clean_text in _TRANSLATION_CACHE:
            return _sanitize_cached_translation(_TRANSLATION_CACHE[clean_text])
        return None


def translate_online_batch(texts: List[str], timeout: float = 8.0) -> List[Optional[str]]:
    """Translates a batch of English texts into Japanese in a single API request.
    Reduces thousands of separate HTTP requests to a few dozen, preventing rate limits.
    """
    if not texts:
        return []

    results: List[Optional[str]] = [None] * len(texts)
    to_translate_indices: List[int] = []
    to_translate_texts: List[str] = []

    for i, t in enumerate(texts):
        clean = t.strip()
        if not clean:
            results[i] = ""
            continue
        if clean in _TRANSLATION_CACHE:
            cached = _TRANSLATION_CACHE[clean]
            if "\nを" not in cached and "\nの" not in cached and "\nに" not in cached:
                results[i] = _sanitize_cached_translation(cached)
                continue
        to_translate_indices.append(i)
        to_translate_texts.append(clean)

    if not to_translate_texts:
        return results

    if len(to_translate_texts) == 1:
        res = translate_online(to_translate_texts[0], timeout=timeout)
        results[to_translate_indices[0]] = res
        return results

    # Batching via unique delimiter
    DELIMITER = "\n<<<SEG>>>\n"

    batch_meta = []
    batch_protected = []
    for item in to_translate_texts:
        prot, tags, sp_pref, l_col, tr_suf = _preprocess_for_mt(item)
        batch_meta.append((tags, sp_pref, l_col, tr_suf))
        batch_protected.append(prot)

    combined = DELIMITER.join(batch_protected)
    query = urllib.parse.quote(combined)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ja&dt=t&q={query}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        translated_segments = []
        if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if part and len(part) > 0 and part[0]:
                    translated_segments.append(part[0])

        raw_all = "".join(translated_segments)
        parts = re.split(r"\s*<<<[\s_]*SEG[\s_]*>>>\s*", raw_all)

        if len(parts) == len(to_translate_texts):
            for orig_clean, meta, trans_part, orig_idx in zip(to_translate_texts, batch_meta, parts, to_translate_indices):
                tags, sp_pref, l_col, tr_suf = meta
                restored = _postprocess_from_mt(trans_part, tags, sp_pref, l_col, tr_suf)
                _TRANSLATION_CACHE[orig_clean] = restored
                results[orig_idx] = restored
            _save_translation_cache()
            return results
    except Exception:
        pass

    # Fallback to single item translation if batch delimiter was lost
    for orig_idx, orig_clean in zip(to_translate_indices, to_translate_texts):
        results[orig_idx] = translate_online(orig_clean, timeout=timeout)

    return results


# ---------------------------------------------------------------------------
# Dialogue Translation Helper
# ---------------------------------------------------------------------------
def auto_translate_dialogue(text: str) -> Optional[str]:
    """Translates dialogue text using template patterns and speaker mapping."""
    if not text or not text.strip():
        return None

    raw_text = text.strip()

    # Handle multi-column Move Tutor / Game Corner strings: e.g. 'Water Pulse[EXT:13:5A][EXT:06:00]4 Green Shards'
    col_match = re.match(r"^([^[]+)(\[EXT:13:[0-9A-Fa-f]{2}\](?:\[EXT:[^\]]+\])*)\s*(.+)$", raw_text)
    if col_match and "\n" not in raw_text:
        left_part = col_match.group(1).strip()
        mid_tags = col_match.group(2)
        right_part = col_match.group(3).strip()
        left_norm = normalize_key(left_part)
        left_jp = NORMALIZED_MOVES.get(left_norm) or NORMALIZED_SPECIES.get(left_norm) or NORMALIZED_ITEMS.get(left_norm) or left_part
        shard_m = re.match(r"^(\d+)\s+(Red|Blue|Yellow|Green)\s+Shards?$", right_part, re.I)
        coin_m = re.match(r"^([\d,]+)\s+Coins?$", right_part, re.I)
        if shard_m:
            s_num = shard_m.group(1)
            s_col = {"red": "あか", "blue": "あお", "yellow": "きいろ", "green": "みどり"}[shard_m.group(2).lower()]
            return f"{left_jp}{mid_tags}{s_col}のかけら{s_num}こ"
        elif coin_m:
            c_num = coin_m.group(1).replace(",", "")
            return f"{left_jp}{mid_tags}{c_num}まい"

    speaker_prefix = ""
    dialogue_body = raw_text

    # Extract optional speaker prefix: e.g. "Prof. Redwood: ", "Nurse: "
    speaker_match = re.match(
        r"^((?:\[[^\]]+\])*\s*([A-Za-z0-9\.\'\s]+?)\s*:\s*(?:\[[^\]]+\])*\s*)(.*)$",
        raw_text,
        re.DOTALL,
    )
    if speaker_match:
        raw_speaker = speaker_match.group(2).strip()
        body_part = speaker_match.group(3).strip()
        norm_speaker = raw_speaker.upper()
        if norm_speaker in SPEAKER_NAME_MAP:
            jp_speaker = SPEAKER_NAME_MAP[norm_speaker]
            speaker_prefix = f"{jp_speaker}「"
            dialogue_body = body_part
        elif len(raw_speaker) <= 20 and not re.search(r"[\r\n]", raw_speaker):
            speaker_prefix = f"{raw_speaker}「"
            dialogue_body = body_part

    # Normalize whitespace for multi-line pattern matching
    normalized_body = " ".join(dialogue_body.split())

    for pattern, template in DIALOGUE_PATTERNS:
        m = pattern.search(normalized_body)
        if m:
            if r"\1" in template or r"\2" in template:
                matched_trans = m.expand(template)
            else:
                matched_trans = template

            if speaker_prefix:
                res = f"{speaker_prefix}{matched_trans}」"
            else:
                res = matched_trans

            return convert_kanji_to_kana(res)

    return None


# ---------------------------------------------------------------------------
# Master Translation Lookup Function
# ---------------------------------------------------------------------------
def auto_translate_text(
    text: str,
    category: Optional[str] = None,
    allow_online: bool = False,
    convert_to_kana: bool = False,
    item_name: str = "",
) -> Optional[str]:
    """High-precision auto-translation function.
    
    1. Tries Category-specific normalized lookup
    2. Tries Global normalized lookup (Moves, Items, Species, Abilities, Types, Menus)
    3. Tries Algorithmic pattern lookup (Mega Stones, TMs, Z-Crystals, Mints)
    4. If still unmatched and allow_online=True: queries Machine Translation API
    5. Guarantees GBA font compatibility (converting Kanji to Kana when necessary).
    """
    if not text or not text.strip():
        return ""

    raw_text = text.strip()
    norm = normalize_key(raw_text)

    # 1. Category-specific lookup
    if category == "dialogue":
        dial_res = auto_translate_dialogue(raw_text)
        if dial_res:
            return hiragana_to_katakana(dial_res) if convert_to_kana else dial_res

    if category == "item_descriptions":
        desc_res = auto_translate_item_description(raw_text, item_name)
        if desc_res:
            kana_res = convert_kanji_to_kana(desc_res)
            return hiragana_to_katakana(kana_res) if convert_to_kana else kana_res

    if category == "species" and norm in NORMALIZED_SPECIES:
        res = NORMALIZED_SPECIES[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "moves" and norm in NORMALIZED_MOVES:
        res = NORMALIZED_MOVES[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "items" and norm in NORMALIZED_ITEMS:
        res = NORMALIZED_ITEMS[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "item_descriptions" and norm in NORMALIZED_ITEM_DESCRIPTIONS:
        res = convert_kanji_to_kana(NORMALIZED_ITEM_DESCRIPTIONS[norm])
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "abilities" and norm in NORMALIZED_ABILITIES:
        res = NORMALIZED_ABILITIES[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "types" and norm in NORMALIZED_TYPES:
        res = NORMALIZED_TYPES[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "natures" and norm in NORMALIZED_NATURES:
        res = NORMALIZED_NATURES[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res
    elif category == "menu" and norm in NORMALIZED_MENUS:
        res = NORMALIZED_MENUS[norm]
        return hiragana_to_katakana(res) if convert_to_kana else res

    # 2. Global Normalized Lookup
    if norm in GLOBAL_NORMALIZED:
        res = convert_kanji_to_kana(GLOBAL_NORMALIZED[norm])
        return hiragana_to_katakana(res) if convert_to_kana else res
    if norm in NORMALIZED_ITEM_DESCRIPTIONS:
        res = convert_kanji_to_kana(NORMALIZED_ITEM_DESCRIPTIONS[norm])
        return hiragana_to_katakana(res) if convert_to_kana else res

    # 3. Special Pattern Lookup (Mega Stones, TMs, Z-Crystals)
    pattern_trans = translate_special_pattern(raw_text)
    if pattern_trans:
        res = convert_kanji_to_kana(pattern_trans)
        return hiragana_to_katakana(res) if convert_to_kana else res

    # 4. Dialogue Pattern Fallback for unknown categories
    dial_fallback = auto_translate_dialogue(raw_text)
    if dial_fallback:
        return hiragana_to_katakana(dial_fallback) if convert_to_kana else dial_fallback

    # 5. Persistent Local MT Cache & Online Machine Translation
    if raw_text in _TRANSLATION_CACHE:
        cached = _TRANSLATION_CACHE[raw_text]
        if "\nを" not in cached and "\nの" not in cached and "\nに" not in cached:
            kana_res = convert_kanji_to_kana(_sanitize_cached_translation(cached))
            return hiragana_to_katakana(kana_res) if convert_to_kana else kana_res

    if allow_online:
        online_res = translate_online(raw_text)
        if online_res:
            kana_res = convert_kanji_to_kana(online_res)
            return hiragana_to_katakana(kana_res) if convert_to_kana else kana_res

    return None
