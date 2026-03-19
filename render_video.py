"""
FOR SALE — Documentary Video Renderer
Renders the full documentary as an MP4 video from narration MP3s + text cards.
Uses moviepy + Pillow for text rendering.

Output: ForSale_Documentary.mp4 (1920x1080, 30fps)
Style: Ken Burns text-card documentary (white/accent text on dark background)

Requirements:
  pip install moviepy Pillow
  ffmpeg must be in PATH

Usage:
  python render_video.py
"""

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip

# ============================================================
# CONFIG
# ============================================================
W, H = 1920, 1080
FPS = 30
BG_COLOR = (10, 10, 15)         # --bg: #0a0a0f
ACCENT = (0, 212, 255)          # --accent: #00d4ff
RED = (255, 51, 102)            # --accent2: #ff3366
GOLD = (255, 170, 0)            # --accent3: #ffaa00
GREEN = (0, 255, 136)           # --green: #00ff88
PURPLE = (170, 102, 255)        # --purple: #aa66ff
WHITE = (232, 232, 240)         # --text
DIM = (136, 136, 160)           # --dim
BRIGHT = (255, 255, 255)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ForSale_Documentary.mp4")

# Try to find a good font
def find_font(name, size):
    """Try common font paths on Windows."""
    paths = [
        f"C:/Windows/Fonts/{name}.ttf",
        f"C:/Windows/Fonts/{name}.otf",
        f"C:/Users/dan/AppData/Local/Microsoft/Windows/Fonts/{name}.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    # Fallback
    try:
        return ImageFont.truetype(name, size)
    except:
        return ImageFont.load_default()

# ============================================================
# TEXT CARD RENDERER
# ============================================================
def render_text_card(lines, duration=5.0, bg=BG_COLOR, title_color=BRIGHT,
                     body_color=DIM, accent_color=ACCENT, subtitle=None,
                     card_type="body"):
    """
    Render a text card as a PIL image, return as moviepy ImageClip.

    card_type: "title" (big centered), "act" (act header), "body" (paragraph),
               "quote" (quote block), "stat" (stat display)
    """
    img = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(img)

    if card_type == "title":
        # Big centered title
        font_big = find_font("georgia", 96)
        font_sub = find_font("arial", 28)

        # Title
        title_text = lines[0] if lines else ""
        bbox = draw.textbbox((0, 0), title_text, font=font_big)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x, H // 2 - 80), title_text, fill=title_color, font=font_big)

        # Subtitle
        if subtitle:
            bbox2 = draw.textbbox((0, 0), subtitle, font=font_sub)
            tw2 = bbox2[2] - bbox2[0]
            draw.text(((W - tw2) // 2, H // 2 + 40), subtitle, fill=DIM, font=font_sub)

        # Accent line
        draw.rectangle([(W//2 - 60, H//2 + 100), (W//2 + 60, H//2 + 103)], fill=accent_color)

    elif card_type == "act":
        # Act header with number
        font_num = find_font("consolas", 18)
        font_title = find_font("georgia", 72)
        font_sub = find_font("arial", 24)

        # Act number
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=font_num)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, H // 2 - 120), subtitle, fill=accent_color, font=font_num)

        # Title
        title_text = lines[0] if lines else ""
        bbox = draw.textbbox((0, 0), title_text, font=font_title)
        tw = bbox[2] - bbox[0]
        x = max((W - tw) // 2, 40)
        draw.text((x, H // 2 - 60), title_text, fill=title_color, font=font_title)

        # Tagline
        if len(lines) > 1:
            bbox2 = draw.textbbox((0, 0), lines[1], font=font_sub)
            tw2 = bbox2[2] - bbox2[0]
            draw.text(((W - tw2) // 2, H // 2 + 40), lines[1], fill=DIM, font=font_sub)

        # Accent lines
        draw.rectangle([(W//2 - 100, H//2 - 130), (W//2 + 100, H//2 - 128)], fill=accent_color)

    elif card_type == "quote":
        font_quote = find_font("georgia", 32)
        font_attr = find_font("arial", 20)

        # Big quotation mark
        font_big_q = find_font("georgia", 200)
        draw.text((100, H // 2 - 200), "\u201C", fill=(*accent_color, 40), font=font_big_q)

        # Quote text (wrapped)
        quote_text = lines[0] if lines else ""
        wrapped = textwrap.fill(quote_text, width=60)
        draw.text((180, H // 2 - 80), wrapped, fill=WHITE, font=font_quote, spacing=12)

        # Attribution
        if len(lines) > 1:
            attr_y = H // 2 + 120
            for extra_line in lines[1:]:
                draw.text((180, attr_y), extra_line, fill=DIM, font=font_attr)
                attr_y += 30

    elif card_type == "stat":
        font_num = find_font("consolas", 120)
        font_label = find_font("arial", 24)

        # Multiple stats in a row
        stat_count = len(lines) // 2  # pairs of (number, label)
        if stat_count == 0:
            stat_count = 1

        spacing = W // (stat_count + 1)
        colors = [ACCENT, RED, GOLD, GREEN, PURPLE]

        for i in range(0, len(lines), 2):
            idx = i // 2
            x_center = spacing * (idx + 1)

            num_text = lines[i]
            bbox = draw.textbbox((0, 0), num_text, font=font_num)
            tw = bbox[2] - bbox[0]
            color = colors[idx % len(colors)]
            draw.text((x_center - tw // 2, H // 2 - 80), num_text, fill=color, font=font_num)

            if i + 1 < len(lines):
                label_text = lines[i + 1]
                bbox2 = draw.textbbox((0, 0), label_text, font=font_label)
                tw2 = bbox2[2] - bbox2[0]
                draw.text((x_center - tw2 // 2, H // 2 + 60), label_text, fill=DIM, font=font_label)

    else:  # body
        font_body = find_font("arial", 28)
        font_heading = find_font("georgia", 42)

        y = 120
        margin = 200

        for line in lines:
            if line.startswith("# "):
                # Heading
                draw.text((margin, y), line[2:], fill=title_color, font=font_heading)
                y += 60
                draw.rectangle([(margin, y), (margin + 80, y + 3)], fill=accent_color)
                y += 30
            elif line.startswith("> "):
                # Highlighted line
                draw.text((margin + 20, y), line[2:], fill=accent_color, font=font_body)
                y += 45
            else:
                # Normal body text (wrap)
                wrapped = textwrap.fill(line, width=70)
                draw.text((margin, y), wrapped, fill=body_color, font=font_body, spacing=8)
                line_count = wrapped.count('\n') + 1
                y += 40 * line_count + 10

            if y > H - 100:
                break

    # Convert to numpy array for moviepy
    import numpy as np
    arr = np.array(img)
    clip = ImageClip(arr, duration=duration)
    return clip


# ============================================================
# DOCUMENTARY STRUCTURE
# ============================================================
# Each segment: (mp3_file, card_type, lines, subtitle, accent_color, extra_duration)
# The MP3 determines the primary duration; extra_duration adds padding

DOCUMENTARY = [
    # ===== TITLE =====
    ("00_intro.mp3", "title", ["FOR SALE"], "How Money Bought Power, From the Pyramids to the Blockchain", ACCENT, 3),

    # ===== ACT I =====
    ("01a_bigbang.mp3", "act", ["In the Beginning", "Before corruption, before money, before life — there was only energy looking for structure."], "ACT I", ACCENT, 2),
    ("01b_life.mp3", "body", [
        "# The Origin",
        "13.8 billion years ago, all matter and energy existed in a point smaller than an atom.",
        "It exploded. Stars ignited. Stars died.",
        "Their deaths created the elements that formed planets.",
        "> On one planet, chemistry became biology.",
        "The moment two organisms wanted the same resource, the game began.",
    ], None, None, 0),
    ("01e_asteroid.mp3", "body", [
        "# The Asteroid",
        "66 million years ago. A 7.5-mile rock hit the Yucatán at 45,000 mph.",
        "165 million years of dinosaur dominance ended in a single day.",
        "> No amount of power protects you from a force you didn't see coming.",
        "Small mammals survived in the margins. They inherited everything.",
    ], None, None, 0),
    ("01f_sapiens.mp3", "body", [
        "# Homo Sapiens",
        "Not the strongest, fastest, or largest.",
        "But the species that could tell stories.",
        "Language let humans coordinate at scale.",
        "> Myths, religions, laws, currencies — all stories that let strangers cooperate.",
    ], None, None, 0),

    # ===== ACT II =====
    ("02a_rome.mp3", "act", ["Dominance", "Every dominant species believes its reign is permanent. None of them are right."], "ACT II · 252 MYA – 1945 CE", RED, 2),
    ("02b_crusades.mp3", "body", [
        "# The Crusades: Banking Was Born",
        "The Knights Templar invented international banking to fund holy wars.",
        "Deposit gold in Paris, withdraw in Jerusalem.",
        "> On Friday, October 13, 1307, King Philip IV arrested every Templar simultaneously.",
        "He owed them too much money. The first bank bailout was a bank execution.",
        "The Medici family took over. They produced four popes and two queens of France.",
    ], None, None, 0),
    ("02e_wwi.mp3", "body", [
        "# World War I: The Bankers' War",
        "J.P. Morgan lent $2.3 billion to the Allies ($50 billion today).",
        "Du Pont supplied 40% of all Allied explosives. Profits: $6M → $82M in four years.",
        "Arms manufacturers lobbied against arms embargoes.",
        "> Congress called them 'Merchants of Death.'",
        "The Treaty of Versailles planted the seeds of the next war.",
    ], None, None, 0),
    ("02g_wwii.mp3", "body", [
        "# World War II: Both Sides",
        "IBM supplied punch card systems to Nazi Germany.",
        "Ford built trucks for the Wehrmacht. Standard Oil sold fuel additives.",
        "Coca-Cola invented Fanta for the German market.",
        "> Not a single American corporation was prosecuted for trading with the enemy.",
        "Operation Paperclip recruited 1,600 Nazi scientists for America.",
    ], None, None, 0),
    ("02g_wwii.mp3", "stat", ["75M", "DEAD", "$2B", "MANHATTAN PROJECT", "1,600", "NAZI SCIENTISTS HIRED"], None, None, 3),

    # ===== ACT III =====
    ("03a_computer.mp3", "act", ["The Machine Age", "Every technological breakthrough was first funded by military money."], "ACT III · 1945 – 2008", ACCENT, 2),
    ("03b_microchip.mp3", "body", [
        "# The Microchip (1958)",
        "Jack Kilby at Texas Instruments. Robert Noyce at Fairchild Semiconductor.",
        "A single chip replaced thousands of components.",
        "Noyce co-founded Intel. Moore's Law began.",
        "> Transistor density doubles every two years. The exponential curve that reshapes civilization.",
    ], None, None, 0),
    ("03e_internet.mp3", "body", [
        "# The Internet",
        "The internet was supposed to democratize information.",
        "For a brief moment, it did. GeoCities, MySpace, early forums.",
        "Then the platforms realized the real product was attention,",
        "> and the real business was selling it.",
    ], None, None, 0),
    ("04a_2008crisis.mp3", "body", [
        "# The 2008 Financial Crisis",
        "Banks sold garbage mortgages as gold-plated securities.",
        "$10 trillion in household wealth evaporated.",
        "10 million Americans lost their homes.",
        "The banks got $700 billion in bailouts.",
        "> Zero executives went to prison.",
        "One person published a whitepaper in response.",
    ], None, None, 0),
    ("04a_2008crisis.mp3", "stat", ["$10T", "WEALTH DESTROYED", "$700B", "BAILOUT", "0", "EXECUTIVES JAILED"], None, None, 3),

    # ===== ACT IV =====
    ("04b_satoshi.mp3", "act", ["The Promise", "A purely peer-to-peer version of electronic cash."], "ACT III · 2008 – 2019", GREEN, 2),
    ("04b_satoshi.mp3", "body", [
        "# Satoshi Nakamoto",
        "October 31, 2008 — six weeks after Lehman Brothers collapsed.",
        "A pseudonymous figure published the Bitcoin whitepaper.",
        "Money without banks. Transactions without trust.",
        "> The tool built to fight corruption became the most efficient corruption machine ever created.",
    ], None, None, 0),

    # ===== ACT V: FTX =====
    ("05a_sbf_rise.mp3", "act", ["The $8 Billion Lie", "134 companies. 27 countries. One line of code."], "ACT IV", RED, 2),
    ("05a_sbf_rise.mp3", "stat", ["$8B", "CUSTOMER FUNDS STOLEN", "134", "SHELL ENTITIES", "25 yrs", "PRISON SENTENCE"], None, None, 3),
    ("05b_machine.mp3", "body", [
        "# The Machine",
        "Customer deposits were routed to Alameda's bank accounts.",
        "One line of code exempted Alameda from auto-liquidation.",
        "Every other user got liquidated at $0.",
        "> Alameda could carry a negative balance up to $65 billion.",
        "$1.13B on celebrity endorsements. $256M on Bahamas real estate.",
        "$100M on political donations — from stolen customer funds.",
    ], None, None, 0),
    ("05d_six_days.mp3", "body", [
        "# Six Days in November",
        "Nov 2: CoinDesk leaks Alameda's balance sheet. $3.66B in FTT — a token FTX made itself.",
        "Nov 6: Binance CEO dumps $529M in FTT. $1B withdrawn in one day.",
        "Nov 7: 'FTX is fine. Assets are fine.' — SBF tweets the lie.",
        "Nov 8: Withdrawals halted. Hundreds of thousands locked out.",
        "> Nov 11: Bankruptcy. Hackers drain $477 million that night.",
    ], None, None, 0),
    ("05e_trial.mp3", "quote", [
        "Never in my career have I seen such a complete failure of corporate controls and such a complete absence of trustworthy financial information as occurred here.",
        "— John Ray III",
        "The man who cleaned up Enron, saying FTX was worse",
    ], None, None, 0),

    # ===== ACT VI: REVOLVING DOOR =====
    ("06a_cftc.mp3", "act", ["The Revolving Door", "FTX hired 13 former CFTC officials. 1 in 3 members of Congress took FTX money."], "ACT V", GOLD, 2),
    ("06b_donations.mp3", "body", [
        "# Buying Both Sides",
        "SBF personally: $40M+ to Democrats — 2nd largest donor after Soros",
        "Ryan Salame: $24.5M to Republicans — 11th largest individual donor",
        "Nishad Singh: $9.7M to Democratic causes (straw donor)",
        "Barbara Fried (SBF's mother): ran Mind the Gap PAC",
        "> $50M+ through dark money 501(c)(4)s. 196 members of Congress took FTX money.",
        "73% never gave it back.",
    ], None, None, 0),

    # ===== ACT VII: THE TAKEOVER =====
    ("07a_fairshake.mp3", "act", ["The Takeover", "SBF went to prison. The industry took notes — and did it better."], "ACT VI · 2024 – 2026", PURPLE, 2),
    ("07a_fairshake.mp3", "stat", ["$260M", "FAIRSHAKE PAC", "33/35", "RACES WON", "$116M", "WAR CHEST FOR 2026"], None, None, 3),
    ("07b_scalps.mp3", "body", [
        "# The Scalps",
        "Sen. Sherrod Brown (D-OH): Chair of Senate Banking. $40M spent to unseat him. He lost.",
        "Rep. Jamaal Bowman (D-NY): $12M opposing him. Lost his primary.",
        "Rep. Katie Porter (D-CA): $10M opposing her Senate bid. She lost.",
        "> Fairshake win rate: 33 out of 35 races entered.",
    ], None, None, 0),
    ("07c_pardons.mp3", "body", [
        "# Three Crypto Pardons",
        "Ross Ulbricht — Silk Road. Life sentence. Pardoned Day 1, pledged to libertarians.",
        "BitMEX Founders — Bank Secrecy Act violations. First time a president pardoned a corporation.",
        "CZ (Changpeng Zhao) — Binance. Pardoned Oct 2025.",
        "> Binance paid lobbyist Charles McDowell (friend of Trump Jr.) $450K/month for 'executive relief from the White House.'",
    ], None, None, 0),

    # ===== THE WEB =====
    ("08a_facebook_rise.mp3", "act", ["The Web", "These aren't separate stories. They're the same people."], "CONNECTIONS", ACCENT, 2),
    ("08a_facebook_rise.mp3", "body", [
        "# The PayPal Mafia",
        "Peter Thiel → JD Vance (VP), David Sacks (AI/Crypto Czar), Palantir ($970M federal contracts)",
        "Elon Musk → $288M in election support → runs DOGE → $38B in government contracts",
        "Reid Hoffman → LinkedIn → OpenAI board → major Democratic donor",
        "> One company. Six billionaires. The entire power structure.",
    ], None, None, 0),
    ("08e_inauguration.mp3", "body", [
        "# The Billionaire Dinner Table",
        "Elon Musk: $288M → runs DOGE, $38B in contracts untouched",
        "Mark Zuckerberg: $1M → FTC case dismissed, dropped fact-checking",
        "Jeff Bezos: $1M → AWS government cloud contracts",
        "Sam Altman: $1M → $500B Stargate deal announced Day 2",
        "Larry Ellison: $30M+ → Oracle is Stargate partner",
        "Brian Armstrong: $75M+ → SEC case dropped",
        "> $239 million total — the most expensive inauguration in history.",
    ], None, None, 0),

    # ===== GOLDMAN / KOCH =====
    ("08d_meta.mp3", "body", [
        "# Goldman Sachs → Government",
        "Robert Rubin: Co-Chairman → Treasury Secretary → repealed Glass-Steagall → joined Citigroup → Citi needed $45B bailout",
        "Hank Paulson: CEO → Treasury Secretary → designed $700B TARP bailout → Goldman got $12.9B",
        "Steven Mnuchin: Partner → Treasury Secretary → $2T tax cuts → top 1% got 83% of benefit",
        "> More Goldman alumni serve in government than from any other institution in history.",
    ], None, None, 0),
    ("08f_doge_thiel.mp3", "body", [
        "# Leonard Leo: The Man Who Built the Supreme Court",
        "Personally recommended 6 Supreme Court Justices: Roberts, Alito, Gorsuch, Kavanaugh, Barrett, Thomas",
        "Received $1.6 billion from Barre Seid — largest known political donation in history",
        "Citizens United (2010): dark money went from $5M to $1B+",
        "> Clarence Thomas: $4.4M in undisclosed gifts from Harlan Crow. Luxury vacations, private jets, $267K tuition.",
    ], None, None, 0),

    # ===== VICTIMS =====
    ("05f_victims.mp3", "body", [
        "# The Human Cost",
        "Sunil Kavuri — $2.1M lost on FTX. 'If the government can't protect us, who can?'",
        "Garrison Grein, 25 — $400K. 'I watched the Super Bowl ad. I thought it was safe.'",
        "Ontario Teachers' Pension Plan — $95M in retirement savings. Nobody asked the teachers.",
        "Enron employees — $2B collective. 401(k)s locked in stock that went from $90 to $0.26.",
        "> 2008 homeowners — $10 trillion in wealth destroyed. 10 million homes foreclosed.",
        "The executives cash out. The celebrities keep their fees. The regular people lose everything.",
    ], None, None, 0),

    # ===== WARS =====
    ("10a_pattern.mp3", "act", ["Follow the Money Through Every War", "Every war was funded by someone. Every one made someone rich."], "ALL OF HUMAN HISTORY", RED, 2),
    ("10a_pattern.mp3", "body", [
        "# The Ancient Ledger",
        "Sumerian temples: lent grain to fund wars that seized more farmland for the temples.",
        "Athens: built 200 warships with silver mined by 20,000 slaves. Democracy's footnote.",
        "Rome: the publicani — private military contractors — became the wealthiest class.",
        "Knights Templar: invented banking to fund Crusades. King Philip seized their assets.",
        "> The Rothschilds: funded both sides of the Napoleonic Wars. Used carrier pigeons for insider trading.",
    ], None, None, 0),
    ("10b_ai_future.mp3", "body", [
        "# The Industrial Wars",
        "WWI: J.P. Morgan lent $50B (today's dollars). Du Pont's profits: $6M → $82M.",
        "WWII: IBM served Nazi Germany. Ford built Wehrmacht trucks. Coca-Cola made Fanta.",
        "Cold War: $10 trillion on weapons. Lockheed, Boeing, Raytheon became permanent.",
        "Vietnam: Pentagon Papers proved the government lied. Defense profits doubled.",
        "Iraq: WMDs didn't exist. Halliburton got $39.5B. Cheney's deferred comp paid out.",
        "> Afghanistan: 20 years. Taliban won. Defense stocks rose 1,000%.",
    ], None, None, 0),
    ("10b_ai_future.mp3", "stat", ["$8T", "WAR ON TERROR", "900K+", "KILLED", "+1,236%", "LOCKHEED STOCK"], None, None, 3),

    # ===== CLOSING =====
    ("10c_question.mp3", "act", ["The Pattern", "Same playbook, every era. Just faster."], "", GOLD, 2),
    ("10d_closing.mp3", "body", [
        "# The Timeline of Speed",
        "The universe: 13.8 billion years to create life.",
        "Dinosaurs: 165 million years of dominance.",
        "The pyramids: generations.",
        "Wall Street: decades to capture. Got bailed out in days.",
        "Enron: a decade to build, a week to collapse.",
        "FTX: three years. Collapsed in six days.",
        "> The crypto takeover of the U.S. government: ten months.",
        "The only thing that changes is the speed. The game never changes.",
    ], None, None, 0),
    ("10d_closing.mp3", "quote", [
        "We are watching, in real time, the merger of corporate power and government power. When the richest people in the world can buy elections, hire regulators, pardon criminals, and write the laws that govern their own industries — that's not democracy. That's oligarchy.",
        "— Rep. Alexandria Ocasio-Cortez (D-NY)",
        "House Oversight Committee, 2025",
    ], None, None, 0),

    # ===== END CARD =====
    (None, "title", ["FOR SALE"], "An interactive documentary · forsale.documentary@protonmail.com · 2026", DIM, 8),
]


# ============================================================
# RENDER
# ============================================================
def render_documentary():
    clips = []
    total = len(DOCUMENTARY)

    for i, entry in enumerate(DOCUMENTARY):
        mp3_file, card_type, lines, subtitle, accent_color, extra_dur = entry

        # Get audio duration
        audio_clip = None
        duration = extra_dur or 5.0

        if mp3_file:
            mp3_path = os.path.join(OUTPUT_DIR, mp3_file)
            if os.path.exists(mp3_path):
                audio_clip = AudioFileClip(mp3_path)
                duration = audio_clip.duration + (extra_dur or 1.0)
            else:
                print(f"  WARNING: {mp3_file} not found, using {duration}s silence")

        print(f"[{i+1}/{total}] {card_type}: {lines[0][:50]}... ({duration:.1f}s)")

        # Render the text card
        video_clip = render_text_card(
            lines, duration=duration,
            accent_color=accent_color or ACCENT,
            card_type=card_type, subtitle=subtitle
        )

        # Attach audio
        if audio_clip:
            # Pad audio if needed
            if audio_clip.duration < duration:
                video_clip = video_clip.with_duration(duration)
                video_clip = video_clip.with_audio(audio_clip)
            else:
                video_clip = video_clip.with_duration(audio_clip.duration + 1)
                video_clip = video_clip.with_audio(audio_clip)

        clips.append(video_clip)

    print(f"\nConcatenating {len(clips)} clips...")
    final = concatenate_videoclips(clips, method="compose")

    total_mins = final.duration / 60
    print(f"Total duration: {total_mins:.1f} minutes")
    print(f"Rendering to {OUTPUT_FILE}...")

    final.write_videofile(
        OUTPUT_FILE,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        bitrate='4000k',
        preset='medium',
        threads=4,
        logger='bar'
    )

    print(f"\nDone! Output: {OUTPUT_FILE}")
    print(f"Duration: {total_mins:.1f} minutes")
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    render_documentary()
