#!/usr/bin/env python3
"""
Peoples of Tarim-Shaiel — Ancestry HTML Generator
==================================================
Reads world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md and builds
docs/peoples-of-tarim-shaiel.html using the shared parchment design system.

Each ancestry entry mirrors the canonical Daggerheart format:
  - World name (Daggerheart system name in small type)
  - 3-paragraph lore description
  - Two named feature boxes with in-world flavor text

Usage:
    python utilities/ancestries/generate_ancestry_html.py
    python utilities/ancestries/generate_ancestry_html.py --out docs/custom.html
"""

import re
import sys
import argparse
from pathlib import Path
from html import escape

SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"
SOURCE_PATH = VAULT_ROOT / "world" / "ancestries" / "PEOPLES_OF_TARIM_SHAIEL.md"
OUTPUT_PATH = DOCS_DIR / "peoples-of-tarim-shaiel.html"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.page_shell import build_page

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

# ---------------------------------------------------------------------------
# Ancestry data
# Keys match the heading key (uppercase, hyphenated) from PEOPLES_OF_TARIM_SHAIEL.md.
# Feature flavor text is in-world only — no roll language, no game-system terms.
# ---------------------------------------------------------------------------

ANCESTRY_DATA = {
    "VANARA": {
        "world_name": "Vanara",
        "dh_name": "Simiah",
        "features": [
            {
                "name": "Natural Climber",
                "flavor": (
                    "Prehensile extremities are not a curiosity — they are an integrated "
                    "part of Vanara physical life and culture. Vanara children learn to use "
                    "feet and tail from birth. The advantage this provides in climbing, "
                    "combat, and fine manipulation is real and recognized by every people "
                    "that has traveled with them."
                ),
            },
            {
                "name": "Nimble",
                "flavor": (
                    "Vanara martial traditions were developed for bodies with four or five "
                    "potential grip points rather than two. The result is a fighting style "
                    "built around repositioning and redirection — one that makes a Vanara "
                    "in motion exceptionally difficult to corner or hold."
                ),
            },
        ],
    },
    "DIV-BORN": {
        "world_name": "Div-Born",
        "dh_name": "Infernis",
        "features": [
            {
                "name": "Fearless",
                "flavor": (
                    "Div-Born carry something from the Outer Reaches in their physical "
                    "constitution that makes them harder to diminish than their appearance "
                    "might suggest. Within Div-Born culture this is understood as the "
                    "inheritance being protective as well as complicated — the Outer Reaches "
                    "shaped beings who endure."
                ),
            },
            {
                "name": "Dread Visage",
                "flavor": (
                    "The shift in appearance that surfaces under strong emotion is something "
                    "the Div-Born lives with, not deploys. That said, when it surfaces in a "
                    "tense negotiation, it tends to clarify the situation rapidly. Whether "
                    "that is useful depends on what outcome the Div-Born wanted."
                ),
            },
        ],
    },
    "GAVAR": {
        "world_name": "Gavar",
        "dh_name": "Firbolg",
        "features": [
            {
                "name": "Charge",
                "flavor": (
                    "Gavar can move with explosive force when they decide to. The decision "
                    "is the critical element — a Gavar charge is the physical expression of "
                    "a commitment already fully made. The people of Tarim-Shaiel who have "
                    "seen one tend to describe not so much the impact as the moment just "
                    "before it, when the Gavar stopped considering and simply became what "
                    "they had decided to be."
                ),
            },
            {
                "name": "Unshakable",
                "flavor": (
                    "Gavar strength is consistent across their lifespan in a way that is "
                    "unusual even among large ancestries. An elder Gavar is not weaker than "
                    "a young one. This is understood within Gavar culture as the body "
                    "holding what the threshold-keeper needs for as long as the keeper stands."
                ),
            },
        ],
    },
    "TADBIR": {
        "world_name": "Tadbir",
        "dh_name": "Clank",
        "features": [
            {
                "name": "Purposeful Design",
                "flavor": (
                    "The purpose for which a Tadbir was made leaves physical traces in their "
                    "mechanisms. The articulation of specific joints, the calibration of "
                    "certain sensors, the arrangement of their maker's marks — all of it "
                    "encodes the original intention in material form. In the domain of that "
                    "purpose, a Tadbir operates with a precision that feels less like skill "
                    "and more like being correctly configured for the work."
                ),
            },
            {
                "name": "Efficient",
                "flavor": (
                    "Tadbir do not recover the way biological beings do. What they have "
                    "they conserve, and when rest is available, they can use it with a "
                    "thoroughness that other peoples cannot match — completing in a short "
                    "period what would take a biological being much longer. The oldest "
                    "Tadbir are particularly good at this. They have had centuries to learn "
                    "what rest is actually for."
                ),
            },
        ],
    },
    "PARI-KIN": {
        "world_name": "Pari-Kin",
        "dh_name": "Faun",
        "features": [
            {
                "name": "Caprine Leap",
                "flavor": (
                    "Pari-Kin leaping ability is a physical fact that informs everything "
                    "about how they move through the world. It is not a special technique — "
                    "it is simply how Pari-Kin bodies work. The gaps and ascents that "
                    "present obstacles to other peoples are, to a Pari-Kin, features of "
                    "terrain to be read and used."
                ),
            },
            {
                "name": "Kick",
                "flavor": (
                    "The same legs that carry a Pari-Kin over a barrier carry significant "
                    "force when directed at a person. A Pari-Kin kick used in contact is "
                    "not a defensive gesture — it is a propulsive one, capable of sending "
                    "either the kicker or the kicked across real distance. Most Pari-Kin "
                    "treat this as one more way of managing the space between themselves "
                    "and a problem."
                ),
            },
        ],
    },
    "KHAVAR": {
        "world_name": "Khavar",
        "dh_name": "Fungril",
        "features": [
            {
                "name": "Fungril Network",
                "flavor": (
                    "The ancestor-web connection between Khavar is biological and constant. "
                    "It is not a skill or a practice — it is a condition of being Khavar. "
                    "What passes through it is not language but emotional register and "
                    "presence. Coordinated Khavar action across distances is possible "
                    "because of it, but requires communities to have developed conventions "
                    "for what to send and how to read it."
                ),
            },
            {
                "name": "Death Connection",
                "flavor": (
                    "The ability to recover a memory from a corpse is specific: one memory, "
                    "tied to a strong emotion or sensation, recovered through contact within "
                    "the window after death. The Khavar cannot choose which memory surfaces. "
                    "They specify the emotion or sensation they are looking for, but the "
                    "memory that answers is chosen by whatever remains in the dead — the "
                    "dead retaining some agency in what they reveal."
                ),
            },
        ],
    },
    "HUMAN": {
        "world_name": "Human",
        "dh_name": "Human",
        "features": [
            {
                "name": "High Stamina",
                "flavor": (
                    "Human bodies are built for endurance rather than peak output — a "
                    "design that does not impress in a single moment but accumulates over "
                    "time into something other ancestries find difficult to match. A human "
                    "who has decided not to stop is, practically speaking, difficult to stop."
                ),
            },
            {
                "name": "Adaptability",
                "flavor": (
                    "Humans adjust to new climates and conditions with a speed that other "
                    "ancestries find remarkable. A human who has lived five years somewhere "
                    "tends to look and move like someone who belongs there. When a method "
                    "fails, they do not insist on it — they find another way, and they "
                    "do it faster than most."
                ),
            },
        ],
    },
    "ELF": {
        "world_name": "Elf",
        "dh_name": "Elf",
        "features": [
            {
                "name": "Quick Reactions",
                "flavor": (
                    "Elven senses are acutely attuned in ways that make them difficult to "
                    "surprise. They track more simultaneous signals than most ancestries "
                    "can consciously register — sound, light, the shift in air that "
                    "precedes movement. When something happens before they expect it, "
                    "they are already responding."
                ),
            },
            {
                "name": "Celestial Trance",
                "flavor": (
                    "Elves do not sleep — they enter a trance that achieves the same "
                    "restoration in a fraction of the time, and from which they emerge "
                    "with a sharpness that has made their night watches legendary. The "
                    "trance also gives them a quality of reflection unavailable to "
                    "ancestries that lose consciousness entirely."
                ),
            },
        ],
    },
    "DWARF": {
        "world_name": "Dwarf",
        "dh_name": "Dwarf",
        "features": [
            {
                "name": "Thick Skin",
                "flavor": (
                    "Dwarven skin and nails contain an unusually high concentration of "
                    "keratin — dense enough to accept embedded gemstones, and resilient "
                    "enough to take impacts that would cause more damage to other "
                    "ancestries. Minor injuries that would slow others down tend not "
                    "to slow dwarves down."
                ),
            },
            {
                "name": "Increased Fortitude",
                "flavor": (
                    "Dwarven physical constitution includes a capacity for deliberate "
                    "resistance that goes beyond their frame. A dwarf who decides to "
                    "absorb something rather than avoid it can reduce the damage through "
                    "sheer accumulated hardness. Among people who have fought alongside "
                    "dwarves, this is considered one of their defining qualities."
                ),
            },
        ],
    },
    "ORC": {
        "world_name": "Orc",
        "dh_name": "Orc",
        "features": [
            {
                "name": "Sturdy",
                "flavor": (
                    "When an Orc is down to their last reserves, something in the way "
                    "they carry themselves makes the next blow harder to land cleanly. "
                    "Experienced fighters describe it as the body becoming harder to read "
                    "when it has nothing left to spare. The Orc proverb applies: you are "
                    "what you carry, and what they carry, at the end, is the determination "
                    "not to go down easily."
                ),
            },
            {
                "name": "Tusks",
                "flavor": (
                    "Orc tusks grow continuously throughout their lives and are decorated "
                    "with meaningful ornamentation — metal bands, carved symbols, tokens "
                    "that mark significant commitments. In contact range, they are also "
                    "weapons. An Orc who chooses to use them has made a statement beyond "
                    "the damage itself."
                ),
            },
        ],
    },
    "KATARI": {
        "world_name": "Katari",
        "dh_name": "Katari",
        "features": [
            {
                "name": "Feline Instincts",
                "flavor": (
                    "Katari hunting instincts are not separate from their social selves — "
                    "the read on a room, the tracking of movement at the edge of "
                    "perception, and the precise assessment of threat are natural "
                    "functions rather than practiced skills. When a situation requires "
                    "them to be fast, they are usually already moving."
                ),
            },
            {
                "name": "Retracting Claws",
                "flavor": (
                    "Katari retractable claws are part of how they engage with the world "
                    "at close range. Deployed in contact, they can create a vulnerability "
                    "in an opponent that wasn't there before — a disruption precise enough "
                    "to change how that opponent is able to defend themselves in the "
                    "moments that follow."
                ),
            },
        ],
    },
    "GOBLIN": {
        "world_name": "Goblin",
        "dh_name": "Goblin",
        "features": [
            {
                "name": "Surefooted",
                "flavor": (
                    "Goblins move through complex environments with an ease that owes as "
                    "much to their large eyes and exceptional hearing as to their size. "
                    "They read the ground they are moving over while they are still "
                    "moving, and are rarely caught off-balance by terrain that would "
                    "require other peoples to slow down."
                ),
            },
            {
                "name": "Danger Sense",
                "flavor": (
                    "Goblins are extremely difficult to sneak up on. Their ears rotate "
                    "independently, their eyes function well in conditions where most "
                    "ancestries are effectively blind, and they have developed the habit "
                    "of reading a situation for threat without appearing to do so. An "
                    "attack that was supposed to be a surprise often isn't."
                ),
            },
        ],
    },
    "HALFLING": {
        "world_name": "Halfling",
        "dh_name": "Halfling",
        "features": [
            {
                "name": "Luckbringer",
                "flavor": (
                    "Halflings treat the care of a community as a form of craft, and "
                    "there is something in their presence — in how they attend to the "
                    "people around them, in how they create the conditions for things "
                    "to go right — that other peoples notice and benefit from. Parties "
                    "that include a Halfling tend to start their days a little better "
                    "resourced than they expected."
                ),
            },
            {
                "name": "Internal Compass",
                "flavor": (
                    "Halflings are magnetically attuned to their world in a way that "
                    "means they do not get lost. This is not metaphor. Their internal "
                    "compass functions regardless of weather, terrain, or how long it "
                    "has been since they last knew where they were. To a Halfling, this "
                    "seems basic. To their traveling companions, it is frequently "
                    "invaluable."
                ),
            },
        ],
    },
    "GIANT": {
        "world_name": "Giant",
        "dh_name": "Giant",
        "features": [
            {
                "name": "Endurance",
                "flavor": (
                    "Giant frames carry more than other ancestries can, in the simplest "
                    "physical sense. They sustain more before they stop, and sustain it "
                    "without the visible deterioration that would slow other peoples "
                    "down. Their shorter lifespan seems to have produced a constitution "
                    "built for density of use rather than length of service."
                ),
            },
            {
                "name": "Reach",
                "flavor": (
                    "Giants have wide frames and elongated arms that give them a reach "
                    "that can be startling at close quarters. What other ancestries can "
                    "only touch by moving, a Giant can touch from where they stand. "
                    "In practice, this means that the distance a Giant considers "
                    "'close' is further than most people expect."
                ),
            },
        ],
    },
}

# Rendering order
ANCESTRY_ORDER = [
    "VANARA", "DIV-BORN", "GAVAR", "TADBIR", "PARI-KIN", "KHAVAR",
    "HUMAN", "ELF", "DWARF", "ORC", "KATARI", "GOBLIN", "HALFLING", "GIANT",
]

# ---------------------------------------------------------------------------
# CSS (extends CSS_BASE from page_shell)
# ---------------------------------------------------------------------------

CSS_ANCESTRY = """\

    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;500&display=swap');

    body {
      background: #1a1208;
      background-image: url('images/paper-texture-top-view-2.jpg');
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 17px;
      line-height: 1.72;
      color: var(--ink);
    }

    .cover { min-height: 280px; }

    .content {
      position: relative;
      z-index: 1;
      padding: 0 3rem 3.5rem;
    }

    /* ---- Jump navigation ---- */

    .jump-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem 1.1rem;
      padding: 1.1rem 0 1.4rem;
      border-bottom: 1px solid var(--rule);
      margin-bottom: 2.8rem;
      font-family: 'Cinzel', serif;
      font-size: 0.7rem;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }

    .jump-nav a {
      color: var(--gold);
      text-decoration: none;
      transition: color 0.15s;
    }

    .jump-nav a:hover { color: var(--gold-light); }

    /* ---- Ancestry section ---- */

    .ancestry-section { scroll-margin-top: 1.5rem; }

    .ancestry-header { margin-bottom: 1.1rem; }

    .ancestry-name {
      display: block;
      font-family: 'Cinzel', serif;
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--crimson);
      letter-spacing: 0.04em;
      line-height: 1.15;
    }

    .ancestry-dh-name {
      font-family: 'Inconsolata', monospace;
      font-size: 0.76rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--steel);
      opacity: 0.75;
    }

    .ancestry-lore p {
      margin-bottom: 0.85rem;
      font-size: 1.02rem;
    }

    .ancestry-lore p:last-child { margin-bottom: 0; }

    /* ---- Feature boxes ---- */

    .feature-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.9rem;
      margin-top: 1.3rem;
    }

    .feature-box {
      background: var(--parchment2);
      border: 1px solid var(--rule);
      border-radius: 2px;
      padding: 0.95rem 1.1rem 1rem;
      box-shadow: inset 0 1px 4px rgba(26,18,8,0.06);
    }

    .feature-name {
      font-family: 'Cinzel', serif;
      font-size: 0.76rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--steel);
      margin-bottom: 0.45rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid var(--rule);
    }

    .feature-box p {
      font-size: 0.95rem;
      line-height: 1.6;
      margin: 0;
    }

    /* ---- Divider between ancestries ---- */

    .ancestry-divider {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--rule), transparent);
      margin: 2.4rem 0;
    }

    @media (max-width: 640px) {
      .content { padding: 0 1.4rem 2.5rem; }
      .feature-grid { grid-template-columns: 1fr; }
      .jump-nav { gap: 0.4rem 0.9rem; }
    }
"""

# ---------------------------------------------------------------------------
# Parse PEOPLES_OF_TARIM_SHAIEL.md
# ---------------------------------------------------------------------------

def parse_peoples_md(path: Path) -> dict[str, str]:
    """Return {HEADING_KEY: lore_text} for each ## heading in the file.

    HEADING_KEY is the uppercase name portion, e.g. 'VANARA', 'DIV-BORN'.
    lore_text is the body paragraphs with leading/trailing whitespace and
    trailing '---' stripped.
    """
    raw = path.read_text(encoding="utf-8")
    # Split on lines that start a ## heading
    chunks = re.split(r'\n(?=## [A-Z])', raw)
    result = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("## "):
            continue
        lines = chunk.splitlines()
        heading = lines[0]  # e.g. "## VANARA (Simiah)"
        m = re.match(r"## ([A-Z][A-Z\-]*)", heading)
        if not m:
            continue
        key = m.group(1)
        # Body = everything after the heading line, stripped of trailing ---
        body = "\n".join(lines[1:]).strip()
        body = re.sub(r'\n---\s*$', '', body).strip()
        result[key] = body
    return result


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def paragraphs_html(text: str) -> str:
    """Convert plain-text paragraphs (blank-line-separated) to <p> tags."""
    paras = re.split(r'\n{2,}', text.strip())
    parts = []
    for p in paras:
        p = p.strip()
        if p:
            parts.append(f"<p>{escape(p)}</p>")
    return "\n".join(parts)


def slug(name: str) -> str:
    return name.lower().replace("-", "-").replace(" ", "-")


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def build_jump_nav(order: list[str]) -> str:
    links = []
    for key in order:
        data = ANCESTRY_DATA[key]
        world_name = data["world_name"]
        anchor = slug(world_name)
        links.append(f'<a href="#{anchor}">{escape(world_name)}</a>')
    return (
        '\n    <div class="jump-nav">\n      '
        + "\n      ".join(links)
        + "\n    </div>\n"
    )


def build_ancestry_section(key: str, lore_text: str) -> str:
    data = ANCESTRY_DATA[key]
    world_name = data["world_name"]
    dh_name = data["dh_name"]
    features = data["features"]
    anchor = slug(world_name)

    lore_html = paragraphs_html(lore_text)

    feature_boxes = ""
    for feat in features:
        feature_boxes += (
            f'\n          <div class="feature-box">'
            f'\n            <div class="feature-name">{escape(feat["name"])}</div>'
            f'\n            <p>{escape(feat["flavor"])}</p>'
            f"\n          </div>"
        )

    return f"""\
    <div class="ancestry-section" id="{anchor}">
      <div class="ancestry-header">
        <span class="ancestry-name">{escape(world_name)}</span>
        <span class="ancestry-dh-name">{escape(dh_name)}</span>
      </div>
      <div class="ancestry-lore">
        {lore_html}
      </div>
      <div class="feature-grid">{feature_boxes}
      </div>
    </div>
"""


def build_content(lore_map: dict[str, str]) -> str:
    parts = [build_jump_nav(ANCESTRY_ORDER)]
    for i, key in enumerate(ANCESTRY_ORDER):
        lore_text = lore_map.get(key, "")
        parts.append(build_ancestry_section(key, lore_text))
        if i < len(ANCESTRY_ORDER) - 1:
            parts.append('    <div class="ancestry-divider"></div>\n')
    return "".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Peoples of Tarim-Shaiel ancestry HTML page."
    )
    parser.add_argument(
        "--out", default=None,
        help="Output path (default: docs/peoples-of-tarim-shaiel.html)"
    )
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else OUTPUT_PATH

    lore_map = parse_peoples_md(SOURCE_PATH)

    # Warn if any requested ancestry is missing from the source file
    for key in ANCESTRY_ORDER:
        if key not in lore_map:
            print(f"WARNING: '{key}' not found in {SOURCE_PATH.name}")

    content_html = build_content(lore_map)

    credits_html = (
        "    Tarim-Shaiel &middot; Ancestry Guide &middot; "
        "Peoples of Tarim-Shaiel &middot; 2026\n"
    )

    html = build_page(
        title="Peoples of Tarim-Shaiel",
        cover_subtitle="Fourteen Ancestries of the Known World",
        banner_left="Ancestry Guide",
        banner_right="Peoples of Tarim-Shaiel · Daggerheart",
        content_html=content_html,
        credits_html=credits_html,
        cover_image_url=COVER_IMAGE_URL,
        css_extra=CSS_ANCESTRY,
        generator_name="utilities/ancestries/generate_ancestry_html.py",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}")
    print(f"  Ancestries: {len(ANCESTRY_ORDER)}")


if __name__ == "__main__":
    main()
