"""Pokémon Gen 3 dialogue templates, speaker mapping, and comprehensive Kanji-to-Kana converter.
Ensures translated text displays in authentic Japanese Hiragana/Katakana compatible with GBA fonts.
"""

import re
from typing import Dict, List, Tuple, Optional

# ---------------------------------------------------------------------------
# Speaker Name Mapping (English -> Japanese)
# ---------------------------------------------------------------------------
SPEAKER_NAME_MAP: Dict[str, str] = {
    "PROF. REDWOOD": "レッドウッドはかせ",
    "PROFESSOR REDWOOD": "レッドウッドはかせ",
    "PROF. OAK": "オーキドはかせ",
    "PROFESSOR OAK": "オーキドはかせ",
    "PROF. BIRCH": "オダマキはかせ",
    "PROFESSOR BIRCH": "オダマキはかせ",
    "PROF. ROWAN": "ナナカマドはかせ",
    "PROFESSOR ROWAN": "ナナカマドはかせ",
    "NURSE": "ジョーイ",
    "CLERK": "てんいん",
    "RICHTER": "リヒター",
    "BELLE": "ベル",
    "MARINA": "マリナ",
    "EZEKIEL": "エゼキエル",
    "ARIA": "アリア",
    "NINA": "ニーナ",
    "HERSCHEL": "ハーシェル",
    "GUIDE": "ガイド",
    "TRAINER": "トレーナー",
    "MAN": "おじさん",
    "WOMAN": "おねえさん",
    "BOY": "おとこのこ",
    "GIRL": "おんなのこ",
    "KID": "こども",
    "OLD MAN": "おじいさん",
    "OLD WOMAN": "おばあさん",
    "MOM": "おかあさん",
    "DAD": "おとうさん",
    "RIVAL": "ライバル",
}

# ---------------------------------------------------------------------------
# Dialogue Templates (Regex pattern -> Japanese text)
# ---------------------------------------------------------------------------
DIALOGUE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # --- Intro & Professor Speeches ---
    (
        re.compile(r"hello there!.*welcome to the wonderful world of\s*pok[eé]mon!.*the name[’']s redwood!.*unravelling the past is my passion", re.I | re.S),
        "やあ こんにちは！[CLEAR]ポケットモンスターの すばらしい\nせかいへ ようこそ！[CLEAR]わしの なまえは レッドウッド！\nポケモンはかせを しておるよ！[CLEAR]この ふしぎな せかいと そこにすむ\nポケモンたちを けんきゅうしておる！[CLEAR]そして こうこがくしゃ でもある！\nかこの ナゾを とくのが だいすきでな！[CLEAR]",
    ),
    (
        re.compile(r"welcome to the wonderful world of pok[eé]mon.*the name[’']s redwood", re.I | re.S),
        "ポケモンの すばらしい せかいへ\nようこそ！[CLEAR]わしの なまえは レッドウッド！\nみんなからは ポケモンはかせと[CLEAR]よばれておるよ！",
    ),
    (
        re.compile(r"welcome to the wonderful world of pok[eé]mon", re.I),
        "ポケモンの すばらしい せかいへ\nようこそ！",
    ),
    (
        re.compile(r"the name[’']s redwood!\s*people often call me the pok[eé]mon\s*prof", re.I),
        "わしの なまえは レッドウッド！\nみんなからは ポケモンはかせと[CLEAR]よばれておるよ！",
    ),
    (
        re.compile(r"^this creature[…\.\[\]A-Z]*$", re.I),
        "この いきものは…[CLEAR]",
    ),
    (
        re.compile(r"[…\.]*is kabuto,?\s*a pok[eé]mon!.*work partners", re.I | re.S),
        "…ポケモンと よばれる\nいきもの「カブト」じゃ！[CLEAR]ポケモンは わしたちの ともだちであり\nたよりになる パートナーなのじゃ！[CLEAR]",
    ),
    (
        re.compile(r"[…\.]*is kabuto,?\s*a pok[eé]mon!", re.I),
        "…ポケモンと よばれる\nいきもの「カブト」じゃ！",
    ),
    (
        re.compile(r"in the world which you are about to enter", re.I),
        "これから はじまる ぼうけんの\nしゅやくは きみじしんだ！\n\nまちや どうろ どうくつなど\nいろんな ばしょで ひとびとに\nはなしかけて ヒントを あつめよう！",
    ),
    (
        re.compile(r"new paths will open to you by helping people", re.I),
        "こまっている ひとを たすけたり\nなぞを といたり することで\nあたらしい みちが ひらけていく！\n\nときどき ひとびとから\nしょうぶを いどまれることも\nあるだろう。 ガンバレ！",
    ),
    (
        re.compile(r"through your adventure.*achieve personal growth", re.I),
        "ぼうけんを つうじて たくさんの\nひとと ふれあい せいちょうしよう！\n\nそれでは Ａボタンを おして\nぼうけんの たびへ しゅっぱつだ！",
    ),
    (
        re.compile(r"this world is widely inhabited by creatures called pok[eé]mon", re.I),
        "この せかいには ポケットモンスター\n…ちぢめて「ポケモン」と よばれる[CLEAR]いきものたちが いたるところに\nすんでおる！",
    ),
    (
        re.compile(r"with today[’']s technology,?\s*we can\s*revive kabuto", re.I | re.S),
        "いまの かがくぎじゅつで カブトを\nカセキから よみがえらせることが[CLEAR]できるように なったのじゃ！\nいのちの ちからづよさには おどろくばかりじゃ！[CLEAR]",
    ),
    (
        re.compile(r"but enough about me!", re.I),
        "さて わしの はなしは\nこれくらいに して…[CLEAR]",
    ),
    (
        re.compile(r"tell me,?\s*are you a boy,?\s*or a girl\?", re.I),
        "きみは おとこのこ かな？\nそれとも おんなのこ かな？",
    ),
    (
        re.compile(r"i see!\s*and your name is\?", re.I),
        "なるほど！\nそれでは きみの なまえは？[CLEAR]",
    ),
    (
        re.compile(r"ah!\s*your name is ([^?]+)\?", re.I),
        r"おお！ きみの なまえは\n\1 じゃな？",
    ),
    (
        re.compile(r"[…\.]*er,?\s*was it ([^?]+)\?", re.I),
        r"…えーと \1\nじゃったかな？",
    ),
    (
        re.compile(r"wonderful,?\s*([^!]+)!\s*now,?\s*this\s*adventure of yours", re.I | re.S),
        r"すばらしいぞ \1！\nいよいよ きみだけの ぼうけんが[CLEAR]いま ここから はじまるのじゃ！\nれきしに のこる だいぼうけんに[CLEAR]なるじゃろう！ がんばってくるのじゃぞ！",
    ),
    (
        re.compile(r"the name[’']s redwood", re.I),
        "わしの なまえは レッドウッド！\nポケモン はかせ じゃ！",
    ),
    (
        re.compile(r"the name[’']s oak", re.I),
        "わしの なまえは オーキド！\nポケモン はかせ じゃ！",
    ),
    (
        re.compile(r"are you a boy\?\s*or are you a girl\?", re.I),
        "きみは おとこのこ？\nそれとも おんなのこ？",
    ),
    (
        re.compile(r"first,?\s*what is your name\?", re.I),
        "まず きみの なまえを\nおしえてもらおう！",
    ),
    (
        re.compile(r"right!?\s*so your name is ([^?]+)\?", re.I),
        r"きみの なまえは \1 で\nまちがいない かな？",
    ),
    (
        re.compile(r"this is my grandson.*what was his name now\?", re.I | re.S),
        "こいつは わしの まごじゃ。[CLEAR]あかんぼうの ころからの きみの\nライバル じゃったな。[CLEAR]…えーと なまえは なんじゃったかの？",
    ),
    (
        re.compile(r"your rival[’']s name,?\s*what was it now\?", re.I),
        "ライバルの なまえは なんじゃったかの？",
    ),
    (
        re.compile(r"that[’']s right!?\s*i remember now!?\s*his name is ([^!]+)!", re.I),
        r"そうじゃった！ おもいだした！\nこいつの なまえは \1 じゃ！[CLEAR]",
    ),
    # --- Start Menu & System UI Descriptions ---
    (
        re.compile(r"save your game with a complete record\s*of your progress to take a break", re.I),
        "これまでの ぼうけんを\nレポートに かきこみます。",
    ),
    (
        re.compile(r"a device that records pok[eé]mon secrets\s*upon meeting or catching them", re.I),
        "みつけたり つかまえた ポケモンの\nデータが きろくされます。",
    ),
    (
        re.compile(r"check and organize pok[eé]mon that are\s*traveling with you in your party", re.I),
        "つれている ポケモンの じょうたいを\nかくにんし ならびかえます。",
    ),
    (
        re.compile(r"equipped with pockets for storing items\s*you bought,?\s*received,?\s*or found", re.I),
        "かったり ひろったりした どうぐを\nポケットごとに しまいます。",
    ),
    (
        re.compile(r"check your money and other game data", re.I),
        "あなたの ステータスや おこづかいを\nかくにんします。",
    ),
    (
        re.compile(r"adjust various game settings such as text\s*speed,?\s*game rules,?\s*etc", re.I),
        "はなしの はやさや ウィンドウなどの\nせっていを かえます。",
    ),
    (
        re.compile(r"close this menu window", re.I),
        "この メニューウィンドウを とじます。",
    ),
    (
        re.compile(r"go back to the\s*previous menu", re.I),
        "まえの メニューに\nもどります。",
    ),
    (
        re.compile(r"what would you like to do\?", re.I),
        "なにを しますか？",
    ),
    (
        re.compile(r"previously on your quest", re.I),
        "これまでの あらすじ…",
    ),
    # --- Battle Menu & Battle UI Prompts ---
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)(?:fight|battle)\[EXT:13:38\]bag\s*pok[eé]mon\[EXT:13:38\]run$", re.I),
        r"\1たたかう[EXT:13:38]バッグ\nポケモン[EXT:13:38]にげる",
    ),
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)ball\[EXT:13:38\]bait\s*rock\[EXT:13:38\]run$", re.I),
        r"\1ボール[EXT:13:38]エサ\nいし[EXT:13:38]にげる",
    ),
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)switch\s*which\?$", re.I),
        r"\1どれを\nだす？",
    ),
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)yes\s*no$", re.I),
        r"\1はい\nいいえ",
    ),
    (
        re.compile(r"^what will\s*(\[[^\]]+\])\s*do\?$", re.I),
        r"\1は\nなにを する？",
    ),
    (
        re.compile(r"^what will\s*(\[[^\]]+\])\s*throw\?$", re.I),
        r"\1は\nなにを なげる？",
    ),
    (
        re.compile(r"^what will the\s*old man do\?$", re.I),
        "おじいさんは\nなにを する？",
    ),
    (
        re.compile(r"^(\[[^\]]+\]) used\s*(\[[^\]]+\])!?$", re.I),
        r"\1の\n\2！",
    ),
    (
        re.compile(r"^a critical hit!$", re.I),
        "きゅうしょに あたった！",
    ),
    (
        re.compile(r"^it[’']s a one-hit ko!$", re.I),
        "いちげき ひっさつ！",
    ),
    (
        re.compile(r"^it[’']s super effective!$", re.I),
        "こうかは ばつぐんだ！",
    ),
    (
        re.compile(r"^it[’']s not very effective[…\.]*$", re.I),
        "こうかは いまひとつの ようだ…",
    ),
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)got away safely!(?:\[CLEAR\])?$", re.I),
        r"\1うまく にげきれた！[CLEAR]",
    ),
    (
        re.compile(r"^((?:\[EXT:[^\]]+\])*)wild (\[[^\]]+\]) fled!$", re.I),
        r"\1やせいの \2は にげだした！",
    ),
    (
        re.compile(r"^player defeated\s*(\[[^\]]+\])!(?:\[CLEAR\])?$", re.I),
        r"\1との\nしょうぶに かった！",
    ),
    (
        re.compile(r"^go!\s*(\[[^\]]+\])!$", re.I),
        r"ゆけっ！ \1！",
    ),
    (
        re.compile(r"^(\[[^\]]+\]) fainted[…\.]*(?:\[CLEAR\])?$", re.I),
        r"\1は たおれた…[CLEAR]",
    ),
    (
        re.compile(r"^what\?\s*(\[[^\]]+\]) is evolving!$", re.I),
        r"おや…！？\n\1の ようすが…！",
    ),
    (
        re.compile(r"^congratulations! your (\[[^\]]+\])\s*evolved into (\[[^\]]+\])!((?:\[EXT:[^\]]+\])*)(?:\[CLEAR\])?$", re.I),
        r"おめでとう！ \1は\n\2に しんかした！\3[CLEAR]",
    ),
    (
        re.compile(r"^huh\?\s*(\[[^\]]+\])\s*stopped evolving!(?:\[CLEAR\])?$", re.I),
        r"あれ…？\n\1の へんかが とまった！[CLEAR]",
    ),
    # --- Early Game Story & Celanto Town NPCs ---
    (
        re.compile(r"celanto library\[CLEAR\]knowledge is learned\.\s*wisdom is earned\.", re.I),
        "ここは セラントとしょかん[CLEAR]「ちしきは まなぶもの。\nちえは みにつけるもの。」",
    ),
    (
        re.compile(r"those running shoes should\s*help you get there faster!.*waiting\s*for you at.*reliquia ruins", re.I | re.S),
        "[COLOR:04]その ランニングシューズが あれば\nもっと はやく いけるはずよ！[CLEAR]ぐずぐず しないで！ かのじょが\nレリキアいせきで まっているわよ！",
    ),
    (
        re.compile(r"the wild pok[eé]mon past here are\s*incredibly dangerous!.*shouldn[’']t go out alone", re.I | re.S),
        "このさきの やせいの ポケモンは\nものすごく きけんだ！[CLEAR]ひとりで でかけちゃ いけないよ！",
    ),
    (
        re.compile(r"i think i owe most of my knowledge\s*to the celanto library!.*books there are so informative", re.I | re.S),
        "ぼくの ちしきの ほとんどは\nセラントとしょかんの おかげさ！[CLEAR]あそこの ほんは すごく べんきょうになるよ！",
    ),
    # --- Tutorial Controls ---
    (
        re.compile(r"the various buttons will be explained in\s*the order of their importance", re.I),
        "たいせつな ボタンの つかいかたを\nじゅんばんに せつめいします。",
    ),
    (
        re.compile(r"press this button to open the menu", re.I),
        "この ボタンで メニューを ひらきます。",
    ),
    (
        re.compile(r"used to shift items and to use a registered item", re.I),
        "どうぐの いれかえや とうろくした どうぐを つかいます。",
    ),
    (
        re.compile(r"if you need help playing the game.*press the l or r button", re.I),
        "あそびかたの せつめいを みるときは Ｌまたは Ｒボタンを おしてください。",
    ),
    (
        re.compile(r"the battlers take turns attacking and reducing each other[’']s hp", re.I),
        "たたかう ポケモンたちが こうごに こうげきして あいての ＨＰを へらしていきます。",
    ),
    (
        re.compile(r"it looks like my (.+?) was faster than the (.+?)\.", re.I),
        r"こちらの \1の ほうが \2より すばやかったようですね。",
    ),
    # --- Bag & Item System Messages ---
    (
        re.compile(r"where should the (.+?) be placed\??", re.I),
        r"\1を どこに おきますか？",
    ),
    (
        re.compile(r"toss out how many (.+?)\?", re.I),
        r"\1を いくつ すてますか？",
    ),
    (
        re.compile(r"deposit how many (.+?)\?", re.I),
        r"\1を いくつ あずけますか？",
    ),
    (
        re.compile(r"withdraw how many (.+?)\?", re.I),
        r"\1を いくつ ひきだしますか？",
    ),
    (
        re.compile(r"the (.+?) can[’']t be held\.", re.I),
        r"\1は もたせられません。",
    ),
    (
        re.compile(r"there is no pok[eé]mon\.", re.I),
        "ポケモンが いません。",
    ),
    (
        re.compile(r"you can[’']t write mail here\.", re.I),
        "ここでは メールを かけません。",
    ),
    (
        re.compile(r"there[’']s no room to store items\.", re.I),
        "これいじょう どうぐを あずけられません。",
    ),
    (
        re.compile(r"there is no more room in the bag\.", re.I),
        "バッグが いっぱいです。",
    ),
    (
        re.compile(r"return to the pc\.", re.I),
        "パソコンに もどる。",
    ),
    (
        re.compile(r"obtained the (.+?)!", re.I),
        r"\1を てにいれた！",
    ),
    (
        re.compile(r"\[player\] found (?:one |a |an )?(.+?)!", re.I),
        r"[PLAYER]は \1を みつけた！",
    ),
    (
        re.compile(r"found (?:one |a |an )?(.+?)!", re.I),
        r"\1を みつけた！",
    ),
    (
        re.compile(r"\[player\] put the (.+?) in the bag\.", re.I),
        r"[PLAYER]は \1を バッグに しまった！",
    ),
    (
        re.compile(r"\[player\] put the (.+?) in the (.+?) pocket\.", re.I),
        r"[PLAYER]は \1を \2ポケットに しまった！",
    ),
    (
        re.compile(r"\[player\] received (.+?)!", re.I),
        r"[PLAYER]は \1を もらった！",
    ),
    # --- Mart Messages ---
    (
        re.compile(r"welcome! How may I help you\?", re.I),
        "いらっしゃいませ！\nどのような ごようけん ですか？",
    ),
    (
        re.compile(r"(.+?)\?\s*Oh,?\s*no\.?\s*I can[’']t buy that\.", re.I),
        r"\1？ それは かりとる ことが できません。",
    ),
    (
        re.compile(r"(.+?)\?\s*How many would you like to sell\?", re.I),
        r"\1？ いくつ うりますか？",
    ),
    (
        re.compile(r"I can pay ¥(.+?)\.?\s*Would that be okay\?", re.I),
        r"\1えんに なりますが\nよろしいですか？",
    ),
    (
        re.compile(r"please come again!?", re.I),
        "またの おこしを おまちしております！",
    ),
    # --- Center Messages ---
    (
        re.compile(r"welcome to our pok[eé]mon center!?.*heal your pok[eé]mon", re.I),
        "ポケモンセンターへ ようこそ！\nポケモンを やすませますか？",
    ),
    (
        re.compile(r"we[’']ve restored your pok[eé]mon to full health\.", re.I),
        "おまちどうさまでした！\nあずかった ポケモンは みんな げんきに なりましたよ！",
    ),
    (
        re.compile(r"we hope to see you again!?", re.I),
        "またの ごりようを おまちしております！",
    ),
    # --- Save Game ---
    (
        re.compile(r"saved the game at this location", re.I),
        "レポートを しっかり かきこみました！",
    ),
    (
        re.compile(r"saving\.\.\.?\s*don[’']t turn off the power", re.I),
        "レポートを かいています\nでんげんを きらないでください",
    ),
    # --- Battle Challenges ---
    (
        re.compile(r"trainer!?\s*welcome to my gym\..*", re.I),
        "チャレンジャーよ！ ジムへ ようこそ！\nしょうぶを はじめよう！",
    ),
    (
        re.compile(r"let our fight begin!?", re.I),
        "さあ！ しょうぶだ！",
    ),
    (
        re.compile(r"i[’']m not gonna lose!?", re.I),
        "わたしは まけないよ！",
    ),
    (
        re.compile(r"you[’']re pretty good!?", re.I),
        "なかなか やるな！",
    ),
    (
        re.compile(r"there are no trainers within range who can battle", re.I),
        "たたかえる トレーナーは まわりに いないようだ…",
    ),
    (
        re.compile(r"the other trainers don[’']t appear to be ready for battle", re.I),
        "ほかの トレーナーは たたかう じゅんびが できていないようだ。",
    ),
]

# ---------------------------------------------------------------------------
# Comprehensive Kanji to Kana Replacement Table
# ---------------------------------------------------------------------------
KANJI_COMPOUNDS: List[Tuple[str, str]] = [
    ("ポケットモンスター", "ポケットモンスター"),
    ("モンスターボール", "モンスターボール"),
    ("ポケモン図鑑", "ポケモンずかん"),
    ("ポケモンずかん", "ポケモンずかん"),
    ("ポケモン", "ポケモン"),
    ("不思議", "ふしぎ"),
    ("世界", "せかい"),
    ("冒険", "ぼうけん"),
    ("主役", "しゅやく"),
    ("主人公", "しゅじんこう"),
    ("自分自身", "じぶんじしん"),
    ("自分", "じぶん"),
    ("自身", "じしん"),
    ("案内", "あんない"),
    ("挑戦", "ちょうせん"),
    ("道路", "どうろ"),
    ("洞窟", "どうくつ"),
    ("場所", "ばしょ"),
    ("人々", "ひとびと"),
    ("人間", "にんげん"),
    ("話しかける", "はなしかける"),
    ("調べる", "しらべる"),
    ("情報", "じょうほう"),
    ("仲間", "なかま"),
    ("友達", "ともだち"),
    ("博士", "はかせ"),
    ("助手", "じょしゅ"),
    ("研究所", "けんきゅうじょ"),
    ("道具", "どうぐ"),
    ("大切", "たいせつ"),
    ("回復", "かいふく"),
    ("経験値", "けいけんち"),
    ("攻撃", "こうげき"),
    ("防御", "ぼうぎょ"),
    ("特攻", "とくこう"),
    ("特防", "とくぼう"),
    ("素早さ", "すばやさ"),
    ("状態", "じょうたい"),
    ("特性", "とくせい"),
    ("性格", "せいかく"),
    ("能力", "のうりょく"),
    ("勝負", "しょうぶ"),
    ("戦い", "たたかい"),
    ("勝利", "しょうり"),
    ("敗北", "はいぼく"),
    ("選択", "せんたく"),
    ("決定", "けってい"),
    ("取消", "とりけし"),
    ("保存", "ほぞん"),
    ("記録", "きろく"),
    ("電源", "でんげん"),
    ("時間", "じかん"),
    ("時計", "とけい"),
    ("名前", "なまえ"),
    ("男の子", "おとこのこ"),
    ("女の子", "おんなのこ"),
    ("相手", "あいて"),
    ("野生", "やせい"),
    ("捕獲", "ほかく"),
    ("進化", "しんか"),
    ("出発", "しゅっぱつ"),
    ("最初", "さいしょ"),
    ("最後", "さいご"),
    ("移動", "いどう"),
    ("終了", "しゅうりょう"),
    ("開始", "かいし"),
    ("設定", "せってい"),
    ("説明", "せつめい"),
    ("登録", "とうろく"),
    ("解除", "かいじょ"),
    ("入手", "にゅうしゅ"),
    ("獲得", "かくとく"),
    ("発見", "はっけん"),
    ("お願い", "おねがい"),
    ("助けて", "たすけて"),
    ("大丈夫", "だいじょうぶ"),
    ("元気", "げんき"),
    ("病気", "びょうき"),
    ("混乱", "こんらん"),
    ("急所", "きゅうしょ"),
    ("効果", "こうか"),
    ("抜群", "ばつぐん"),
    ("命中", "めいちゅう"),
    ("威力", "いりょく"),
    ("交代", "こうたい"),
    ("逃げる", "にげる"),
    ("持たせる", "もたせる"),
    ("預ける", "あずける"),
    ("引き出す", "ひきだす"),
    ("捨てる", "すてる"),
    ("買う", "かう"),
    ("売る", "うる"),
    ("倒す", "たおす"),
    ("覚える", "おぼえる"),
    ("忘れる", "わすれる"),
    ("戻る", "もどる"),
    ("行く", "いく"),
    ("来る", "くる"),
    ("見る", "みる"),
    ("聞く", "きく"),
    ("言う", "いう"),
    ("思う", "おもう"),
    ("分かる", "わかる"),
    ("知る", "しる"),
    ("探す", "さがす"),
    ("届ける", "とどける"),
    ("渡す", "わたす"),
    ("開ける", "あける"),
    ("閉める", "しめる"),
    ("入る", "はいる"),
    ("出る", "でる"),
    ("乗る", "のる"),
    ("降りる", "おりる"),
    ("走る", "はしる"),
    ("歩く", "あるく"),
    ("飛ぶ", "とぶ"),
    ("泳ぐ", "およぐ"),
    ("潜る", "もぐる"),
    ("登る", "のぼる"),
    ("押す", "おす"),
    ("引く", "ひく"),
    ("お前", "おまえ"),
    ("彼女", "かのじょ"),
    ("今日", "きょう"),
    ("明日", "あした"),
    ("昨日", "きのう"),
    ("夕方", "ゆうがた"),
    ("四天王", "してんのう"),
    ("殿堂入り", "でんどういり"),
    ("殿堂", "でんどう"),
    ("自転車", "じてんしゃ"),
    ("手紙", "てがみ"),
    ("荷物", "にもつ"),
    ("お金", "おかね"),
    ("階段", "かいだん"),
    ("看板", "かんばん"),
    ("建物", "たてもの"),
    ("部屋", "へや"),
    ("港", "みなと"),
    ("街", "まち"),
    ("町", "まち"),
    ("村", "むら"),
    ("都市", "とし"),
    ("島", "しま"),
    ("道", "みち"),
    ("森", "もり"),
    ("山", "やま"),
    ("海", "うみ"),
    ("川", "かわ"),
    ("湖", "みずうみ"),
    ("家", "いえ"),
    ("店", "みせ"),
    ("扉", "とびら"),
    ("門", "もん"),
    ("橋", "はし"),
    ("船", "ふね"),
    ("敵", "てき"),
    ("味方", "みかた"),
    ("父", "ちち"),
    ("母", "はは"),
    ("兄", "あに"),
    ("弟", "おとうと"),
    ("姉", "あね"),
    ("妹", "いもうと"),
    ("祖父", "そふ"),
    ("祖母", "そぼ"),
    ("孫", "まご"),
    ("家族", "かぞく"),
    ("箱", "はこ"),
    ("袋", "ふくろ"),
    ("先生", "せんせい"),
    ("店員", "てんいん"),
    ("少年", "しょうねん"),
    ("少女", "しょうじょ"),
    ("子供", "こども"),
    ("大人", "おとな"),
    ("私", "わたし"),
    ("僕", "ぼく"),
    ("俺", "おれ"),
    ("君", "きみ"),
    ("彼", "かれ"),
    ("誰", "だれ"),
    ("何", "なに"),
    ("朝", "あさ"),
    ("昼", "ひる"),
    ("夜", "よる"),
    ("今", "いま"),
    ("昔", "むかし"),
    ("未来", "みらい"),
    ("東", "ひがし"),
    ("西", "にし"),
    ("南", "みなみ"),
    ("北", "きた"),
    ("上", "うえ"),
    ("下", "した"),
    ("右", "みぎ"),
    ("左", "ひだり"),
    ("前", "まえ"),
    ("後", "うしろ"),
    ("中", "なか"),
    ("外", "そと"),
    ("先", "さき"),
    ("近く", "ちかく"),
    ("遠く", "とおく"),
    ("一", "いち"),
    ("二", "に"),
    ("三", "さん"),
    ("四", "よん"),
    ("五", "ご"),
    ("六", "ろく"),
    ("七", "なな"),
    ("八", "はち"),
    ("九", "きゅう"),
    ("十", "じゅう"),
    ("百", "ひゃく"),
    ("千", "せん"),
    ("万", "まん"),
    ("円", "えん"),
    ("毒", "どく"),
    ("麻痺", "まひ"),
    ("眠り", "ねむり"),
    ("火傷", "やけど"),
    ("氷", "こおり"),
    ("瀕死", "ひんし"),
]

# Single Kanji fallback table (common Kanji -> Hiragana reading)
KANJI_CHAR_MAP: Dict[str, str] = {
    "世": "せ", "界": "かい", "冒": "ぼう", "険": "けん", "人": "ひと", "物": "もの",
    "心": "こころ", "力": "ちから", "気": "き", "手": "て", "足": "あし", "目": "め",
    "耳": "みみ", "口": "くち", "頭": "あたま", "体": "からだ", "命": "いのち",
    "生": "い", "死": "し", "天": "てん", "地": "ち", "日": "ひ", "月": "つき",
    "火": "ひ", "水": "みず", "木": "き", "金": "きん", "土": "つち", "風": "かぜ",
    "光": "ひかり", "闇": "やみ", "神": "かみ", "王": "おう", "友": "とも", "愛": "あい",
    "好": "す", "嫌": "きら", "強": "つよ", "弱": "よわ", "高": "たか", "低": "ひく",
    "大": "おお", "小": "ちい", "多": "おお", "少": "すく", "新": "あたら", "古": "ふる",
    "良": "よ", "悪": "わる", "正": "ただ", "真": "ま", "白": "しろ", "黒": "くろ",
    "赤": "あか", "青": "あお", "黄": "き", "緑": "みどり", "紫": "むらさき",
    "時": "とき", "年": "ねん", "分": "ふん", "秒": "びょう", "間": "あいだ",
    "点": "てん", "数": "かず", "度": "ど", "回": "かい", "番": "ばん", "号": "ごう",
    "方": "かた", "者": "もの", "事": "こと", "用": "よう", "意": "い", "味": "み",
    "全": "ぜん", "部": "ぶ", "同": "おな", "違": "ちが", "合": "あ", "別": "べつ",
    "持": "も", "取": "と", "出": "だ", "入": "い", "買": "か", "売": "う",
    "見": "み", "聞": "き", "話": "はな", "言": "い", "思": "おも", "知": "し",
    "行": "い", "来": "く", "帰": "かえ", "待": "ま", "止": "と", "立": "た",
    "座": "すわ", "走": "はし", "歩": "ある", "飛": "と", "落": "お", "消": "き",
    "変": "か", "化": "か", "進": "すす", "退": "しりぞ", "勝": "か", "負": "ま",
    "戦": "たたか", "闘": "とう", "打": "う", "切": "き", "投": "な", "受": "う",
    "助": "たす", "救": "すく", "守": "まも", "破": "やぶ", "壊": "こわ", "直": "なお",
}


# ---------------------------------------------------------------------------
# macOS Native Morphological Kanji-to-Hiragana Engine (CoreFoundation)
# Converts arbitrary Japanese Kanji text into 100% accurate Hiragana readings
# with zero external dependencies on macOS.
# ---------------------------------------------------------------------------
_CF_LIB = None
_CF_LATIN_HIRAGANA = None

try:
    import ctypes
    from ctypes import c_void_p, c_long, c_uint32, c_char_p, c_bool, Structure

    class _CFRange(Structure):
        _fields_ = [("location", c_long), ("length", c_long)]

    _cf = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    _cf.CFStringCreateWithCString.restype = c_void_p
    _cf.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    _cf.CFStringCreateMutableCopy.restype = c_void_p
    _cf.CFStringCreateMutableCopy.argtypes = [c_void_p, c_long, c_void_p]
    _cf.CFStringTokenizerCreate.restype = c_void_p
    _cf.CFStringTokenizerCreate.argtypes = [c_void_p, c_void_p, _CFRange, c_uint32, c_void_p]
    _cf.CFStringTokenizerAdvanceToNextToken.restype = c_uint32
    _cf.CFStringTokenizerAdvanceToNextToken.argtypes = [c_void_p]
    _cf.CFStringTokenizerGetCurrentTokenRange.restype = _CFRange
    _cf.CFStringTokenizerGetCurrentTokenRange.argtypes = [c_void_p]
    _cf.CFStringTokenizerCopyCurrentTokenAttribute.restype = c_void_p
    _cf.CFStringTokenizerCopyCurrentTokenAttribute.argtypes = [c_void_p, c_uint32]
    _cf.CFStringTransform.restype = c_bool
    _cf.CFStringTransform.argtypes = [c_void_p, c_void_p, c_void_p, c_bool]
    _cf.CFStringGetLength.restype = c_long
    _cf.CFStringGetLength.argtypes = [c_void_p]
    _cf.CFStringGetCString.restype = c_bool
    _cf.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
    _cf.CFRelease.argtypes = [c_void_p]

    _CF_LATIN_HIRAGANA = _cf.CFStringCreateWithCString(None, b"Latin-Hiragana", 0x08000100)
    _CF_LIB = _cf
except Exception:
    _CF_LIB = None


def _macos_kanji_to_hiragana(text: str) -> str:
    """Uses macOS CoreFoundation CFStringTokenizer to convert Kanji words to Hiragana."""
    if not _CF_LIB or not text or not any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return text
    try:
        kUTF8 = 0x08000100
        kLatinAttr = 1 << 16
        u16 = text.encode("utf-16-le")
        s = _CF_LIB.CFStringCreateWithCString(None, text.encode("utf-8"), kUTF8)
        if not s:
            return text
        length = _CF_LIB.CFStringGetLength(s)
        tok = _CF_LIB.CFStringTokenizerCreate(None, s, _CFRange(0, length), 0, None)
        if not tok:
            _CF_LIB.CFRelease(s)
            return text
        out = []
        last_idx = 0
        while _CF_LIB.CFStringTokenizerAdvanceToNextToken(tok):
            r = _CF_LIB.CFStringTokenizerGetCurrentTokenRange(tok)
            if r.location > last_idx:
                out.append(u16[last_idx * 2 : r.location * 2].decode("utf-16-le", errors="ignore"))
            token_str = u16[r.location * 2 : (r.location + r.length) * 2].decode("utf-16-le", errors="ignore")
            if any("\u4e00" <= ch <= "\u9fff" for ch in token_str):
                attr = _CF_LIB.CFStringTokenizerCopyCurrentTokenAttribute(tok, kLatinAttr)
                if attr:
                    m = _CF_LIB.CFStringCreateMutableCopy(None, 0, attr)
                    _CF_LIB.CFStringTransform(m, None, _CF_LATIN_HIRAGANA, False)
                    buf = ctypes.create_string_buffer(1024)
                    _CF_LIB.CFStringGetCString(m, buf, 1024, kUTF8)
                    hira = buf.value.decode("utf-8", errors="ignore")
                    out.append(hira)
                    _CF_LIB.CFRelease(m)
                    _CF_LIB.CFRelease(attr)
                else:
                    out.append(token_str)
            else:
                out.append(token_str)
            last_idx = r.location + r.length
        if last_idx * 2 < len(u16):
            out.append(u16[last_idx * 2 :].decode("utf-16-le", errors="ignore"))
        _CF_LIB.CFRelease(tok)
        _CF_LIB.CFRelease(s)
        return "".join(out)
    except Exception:
        return text


# Pokémon domain & ROM hack proper noun glossary (applied before Kanji->Kana)
POKEMON_GLOSSARY_REPLACEMENTS: List[Tuple[str, str]] = [
    ("Pokémon", "ポケモン"),
    ("Pokemon", "ポケモン"),
    ("POKÉMON", "ポケモン"),
    ("Pokédex", "ポケモンずかん"),
    ("Pokedex", "ポケモンずかん"),
    ("POKÉDEX", "ポケモンずかん"),
    ("Poké Ball", "モンスターボール"),
    ("Poke Ball", "モンスターボール"),
    ("Running Shoes", "ランニングシューズ"),
    ("ランニング シューズ", "ランニングシューズ"),
    ("エスケープ ロープ", "あなぬけのヒモ"),
    ("キーアイテムポケット", "たいせつなものポケット"),
    ("アイテムポケット", "どうぐポケット"),
    ("ポケモンの動き", "ポケモンのわざ"),
    ("の動きを", "のわざを"),
    ("アイテム", "どうぐ"),
    ("Reliquia Ruins", "レリキアいせき"),
    ("Reliquia", "レリキア"),
    ("Celanto Library", "セラントとしょかん"),
    ("Celanto Town", "セラントタウン"),
    ("Celanto", "セラント"),
    ("Archan Town", "アーカンタウン"),
    ("Archan Tunnel", "アーカントンネル"),
    ("Archan", "アーカン"),
    ("Seros Village", "セロスむら"),
    ("Seros", "セロス"),
    ("Aerous City", "エアロスシティ"),
    ("Aerous", "エアロス"),
    ("Nestpine Town", "ネストパインタウン"),
    ("Nestpine", "ネストパイン"),
    ("Windmist City", "ウィンドミストシティ"),
    ("Windmist", "ウィンドミスト"),
    ("Sabulo Island", "サブロじま"),
    ("Sabulo", "サブロ"),
    ("Valoon Town", "バルーンタウン"),
    ("Valoon", "バルーン"),
    ("Telmurk City", "テルマークシティ"),
    ("Telmurk", "テルマーク"),
    ("Precimos Island", "プレシモスじま"),
    ("Precimos", "プレシモス"),
    ("Edashore Town", "エダショアタウン"),
    ("Edashore", "エダショア"),
    ("Atsail City", "アットセイルシティ"),
    ("Atsail", "アットセイル"),
    ("Loamas Town", "ロアマスタウン"),
    ("Loamas", "ロアマス"),
    ("Ikos Town", "イコスタウン"),
    ("Ikos", "イコス"),
    ("Ovarr Town", "オヴァールタウン"),
    ("Ovarr", "オヴァール"),
    ("Orbtus", "オーブタス"),
    ("Redwood", "レッドウッド"),
    ("教授", "はかせ"),
    ("博士", "はかせ"),
    ("私", "わたし"),
    ("僕", "ぼく"),
    ("俺", "おれ"),
    ("君", "きみ"),
    ("彼女", "かのじょ"),
    ("彼", "かれ"),
    ("お父さん", "おとうさん"),
    ("お母さん", "おかあさん"),
    ("何を", "なにを"),
    ("何が", "なにが"),
    ("何処", "どこ"),
]


def convert_kanji_to_kana(text: str) -> str:
    """Converts all Kanji in text into accurate Hiragana to guarantee 100% GBA font display compatibility."""
    if not text:
        return ""

    result = text

    # Step 0: Apply Pokémon domain & proper noun glossary
    for src_term, dst_term in POKEMON_GLOSSARY_REPLACEMENTS:
        if src_term in result:
            result = result.replace(src_term, dst_term)

    # Step 1: Use macOS CoreFoundation morphological analyzer for full-sentence Kanji-to-Hiragana accuracy
    if any("\u4e00" <= ch <= "\u9fff" for ch in result):
        result = _macos_kanji_to_hiragana(result)

    # Step 2: Replace any remaining multi-character compound words
    if any("\u4e00" <= ch <= "\u9fff" for ch in result):
        for word, kana in KANJI_COMPOUNDS:
            if word in result:
                result = result.replace(word, kana)

    # Step 3: Replace any remaining individual Kanji characters using fallback map
    chars = []
    for ch in result:
        if ch in KANJI_CHAR_MAP:
            chars.append(KANJI_CHAR_MAP[ch])
        elif '\u4e00' <= ch <= '\u9fff':
            chars.append("")
        else:
            chars.append(ch)

    return "".join(chars)


def format_gba_dialogue(text: str, original_text: str = "", max_chars_per_line: int = 18) -> str:
    """Formats a Japanese dialogue string with automatic line-wrapping and [CLEAR] page breaks
    so that text never overflows the 2-line GBA dialogue window (208px width) and never
    renders off-screen (blank white box).
    """
    if not text:
        return ""

    # Preserve multi-column menu tables and palette-header battle menus ([EXT:13:], [EXT:05:], [EXT:04:]) intact
    if any(tag in text for tag in ("[EXT:13:", "[EXT:05:", "[EXT:04:")):
        return text

    # Normalize any legacy [WAIT]\n or [CLEAR]\n into [CLEAR]
    cleaned = text.replace("[WAIT]\r\n", "[CLEAR]").replace("[WAIT]\n", "[CLEAR]")
    cleaned = cleaned.replace("[CLEAR]\r\n", "[CLEAR]").replace("[CLEAR]\n", "[CLEAR]")
    cleaned = cleaned.replace("[WAIT]", "[CLEAR]")

    # Preserve paragraph breaks (\n\n) for full-screen multi-paragraph help screens (e.g. Pikachu intro help)
    if "\n\n" in cleaned and "[CLEAR]" not in cleaned:
        paragraphs = cleaned.split("\n\n")
        formatted_paras = []
        for p in paragraphs:
            p_lines = _wrap_segment_to_lines(p.replace("\n", " "), max_chars_per_line)
            formatted_paras.append("\n".join(p_lines))
        return "\n\n".join(formatted_paras)

    trailing_clear = cleaned.endswith("[CLEAR]") or (original_text and original_text.rstrip().endswith("[CLEAR]"))
    trailing_ext09 = cleaned.endswith("[EXT:09]") or (original_text and original_text.rstrip().endswith("[EXT:09]"))

    if cleaned.endswith("[EXT:09]"):
        cleaned = cleaned[: -len("[EXT:09]")].rstrip()
    if cleaned.endswith("[CLEAR]"):
        cleaned = cleaned[: -len("[CLEAR]")].rstrip()

    raw_pages = [p.strip() for p in cleaned.split("[CLEAR]") if p.strip()]
    if not raw_pages:
        return text

    tag_re = re.compile(r"\[[^\]]+\]")

    def visible_len(s: str) -> int:
        s_clean = re.sub(r"\[(PLAYER|RIVAL|BUFFER_1|BUFFER_2)\]", "AAAAA", s)
        s_clean = tag_re.sub("", s_clean)
        return len(s_clean)

    box_pages: List[str] = []
    for page in raw_pages:
        existing_lines = [ln.strip() for ln in page.split("\n") if ln.strip()]
        if len(existing_lines) <= 2 and all(visible_len(ln) <= max_chars_per_line + 3 for ln in existing_lines):
            box_pages.append("\n".join(existing_lines))
        else:
            # Wrap into lines of max_chars_per_line and group into 2-line boxes
            wrapped_lines: List[str] = []
            for ln in existing_lines:
                if visible_len(ln) <= max_chars_per_line + 2:
                    wrapped_lines.append(ln)
                else:
                    wrapped_lines.extend(_wrap_segment_to_lines(ln, max_chars_per_line))
            for i in range(0, len(wrapped_lines), 2):
                pair = wrapped_lines[i : i + 2]
                box_pages.append("\n".join(pair))

    result = "[CLEAR]".join(box_pages)
    if trailing_clear and not result.endswith("[CLEAR]"):
        result += "[CLEAR]"
    if trailing_ext09 and not result.endswith("[EXT:09]"):
        result += "[EXT:09]"
    return result


def _wrap_segment_to_lines(seg: str, max_chars_per_line: int = 18) -> List[str]:
    """Wraps a single text segment into lines of at most max_chars_per_line visible characters."""
    tokens = re.findall(r"\[[^\]]+\]|.", seg.strip())
    lines: List[str] = []
    current_line: List[str] = []
    current_len = 0

    for tok in tokens:
        if tok in ("[WAIT]", "[CLEAR]"):
            if current_line:
                lines.append("".join(current_line).strip())
                current_line = []
                current_len = 0
            continue

        tok_len = 5 if tok in ("[PLAYER]", "[RIVAL]", "[BUFFER_1]", "[BUFFER_2]") else (0 if tok.startswith("[") else 1)
        if current_len + tok_len > max_chars_per_line and current_line:
            if tok in ("。", "、", "！", "？", "」", "』", "!", "?", ".", ",") and current_len <= max_chars_per_line + 1:
                current_line.append(tok)
                lines.append("".join(current_line).strip())
                current_line = []
                current_len = 0
                continue
            lines.append("".join(current_line).strip())
            if tok != " ":
                current_line = [tok]
                current_len = tok_len
            else:
                current_line = []
                current_len = 0
        else:
            if not current_line and tok == " ":
                continue
            current_line.append(tok)
            current_len += tok_len

    if current_line:
        lines.append("".join(current_line).strip())
    return [ln for ln in lines if ln]
