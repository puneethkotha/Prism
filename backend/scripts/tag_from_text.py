"""
Rule-based metadata extractor that produces the same JSON schema as the LLM pipeline.

This runs entirely locally — no API key required. Tags are derived deterministically
from real Amazon product text and category hierarchy. This is the initial tagging pass;
the LLM pipeline (extract_tags.py) can be run later to re-tag with Claude Sonnet.

Schema produced:
    category, subcategory, key_features, use_case, target_audience, complexity, sentiment

Usage:
    python scripts/tag_from_text.py [--batch-size N]
"""

import sys
import re
import json
import logging
import argparse
from pathlib import Path

import psycopg2
import psycopg2.extras
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Category mappings ─────────────────────────────────────────────────────────

SUBCATEGORY_RULES: list[tuple[list[str], str, str]] = [
    (["headphone", "earbud", "earphone", "in-ear", "over-ear", "on-ear"], "Electronics", "Headphones & Earbuds"),
    (["bluetooth speaker", "portable speaker", "wireless speaker"], "Electronics", "Bluetooth Speakers"),
    (["speaker", "subwoofer", "bookshelf speaker", "home theater"], "Electronics", "Home Audio"),
    (["laptop", "notebook", "chromebook"], "Computers", "Laptops"),
    (["desktop", "workstation", "all-in-one"], "Computers", "Desktops"),
    (["gaming mouse", "optical mouse", "wireless mouse"], "Computer Peripherals", "Computer Mice"),
    (["mechanical keyboard", "gaming keyboard", "wireless keyboard"], "Computer Peripherals", "Keyboards"),
    (["monitor", "display", "4k screen", "curved screen", "ultrawide"], "Computer Peripherals", "Computer Monitors"),
    (["webcam", "web camera", "streaming camera"], "Computer Peripherals", "Webcams"),
    (["usb hub", "usb-c hub", "multiport", "docking station", "dock"], "Computer Peripherals", "USB Hubs & Docks"),
    (["external hard drive", "external ssd", "portable ssd", "portable hdd"], "Storage", "External Drives"),
    (["ssd", "nvme", "m.2", "solid state"], "Storage", "Internal SSDs"),
    (["hard drive", "hdd", "internal drive"], "Storage", "Hard Drives"),
    (["flash drive", "usb drive", "thumb drive", "usb stick"], "Storage", "Flash Drives"),
    (["ram", "ddr4", "ddr5", "memory stick", "dimm"], "Components", "Memory"),
    (["graphics card", "gpu", "video card", "rtx", "gtx", "radeon rx"], "Components", "Graphics Cards"),
    (["cpu", "processor", "core i", "ryzen", "intel", "amd"], "Components", "Processors"),
    (["motherboard", "mainboard", "atx", "itx"], "Components", "Motherboards"),
    (["power supply", "psu", "atx power"], "Components", "Power Supplies"),
    (["pc case", "computer case", "tower case", "mid-tower"], "Components", "PC Cases"),
    (["cpu cooler", "air cooler", "liquid cooler", "aio cooler", "radiator"], "Components", "CPU Coolers"),
    (["smart watch", "smartwatch", "fitness watch", "apple watch", "galaxy watch"], "Wearables", "Smartwatches"),
    (["fitness tracker", "activity tracker", "fitness band", "heart rate band"], "Wearables", "Fitness Trackers"),
    (["earwear", "hearing aid"], "Wearables", "Earwear"),
    (["drone", "quadcopter", "fpv", "uav"], "Electronics", "Camera Drones"),
    (["action camera", "gopro", "dashcam", "dash cam"], "Cameras", "Action Cameras"),
    (["digital camera", "dslr", "mirrorless", "point and shoot"], "Cameras", "Digital Cameras"),
    (["camera lens", "zoom lens", "prime lens"], "Cameras", "Camera Lenses"),
    (["tripod", "gimbal", "stabilizer", "selfie stick"], "Cameras", "Camera Accessories"),
    (["smart speaker", "echo", "google home", "alexa", "voice assistant"], "Smart Home", "Smart Speakers"),
    (["smart bulb", "smart light", "led strip", "phillips hue", "smart lighting"], "Smart Home", "Smart Lighting"),
    (["smart plug", "smart outlet", "smart switch"], "Smart Home", "Smart Plugs"),
    (["security camera", "surveillance camera", "ip camera", "ring camera", "nest cam"], "Smart Home", "Security Cameras"),
    (["smart thermostat", "nest thermostat", "ecobee"], "Smart Home", "Smart Thermostats"),
    (["robot vacuum", "robovac", "roomba", "smart vacuum"], "Smart Home", "Robot Vacuums"),
    (["video doorbell", "smart doorbell", "ring doorbell"], "Smart Home", "Video Doorbells"),
    (["router", "wifi router", "mesh wifi", "access point", "wifi 6"], "Networking", "Routers"),
    (["ethernet cable", "ethernet switch", "network switch"], "Networking", "Network Accessories"),
    (["nas", "network attached storage", "home server"], "Networking", "NAS Devices"),
    (["charger", "power bank", "battery pack", "portable charger", "wireless charger"], "Electronics", "Portable Chargers"),
    (["power strip", "surge protector", "extension cord"], "Electronics", "Power Accessories"),
    (["cable", "hdmi", "displayport", "usb cable", "charging cable", "adapter"], "Electronics", "Cables & Adapters"),
    (["projector", "mini projector", "portable projector"], "Electronics", "Projectors"),
    (["tablet", "ipad", "android tablet", "e-reader", "kindle"], "Electronics", "Tablets & E-Readers"),
    (["phone case", "screen protector", "phone stand"], "Mobile Accessories", "Phone Accessories"),
    (["controller", "gamepad", "joystick", "gaming controller"], "Gaming", "Controllers"),
    (["gaming headset", "gaming headphone"], "Gaming", "Gaming Headsets"),
    (["vr headset", "virtual reality", "oculus", "meta quest"], "Gaming", "VR Headsets"),
    (["stream deck", "elgato", "capture card", "video capture"], "Streaming", "Streaming Equipment"),
    (["microphone", "condenser mic", "dynamic mic", "usb mic"], "Audio", "Microphones"),
    (["audio interface", "sound card", "dac", "amplifier"], "Audio", "Audio Equipment"),
    (["standing desk", "adjustable desk", "sit stand"], "Furniture", "Standing Desks"),
    (["monitor arm", "monitor mount", "desk mount"], "Furniture", "Monitor Mounts"),
    (["chair", "ergonomic chair", "gaming chair", "office chair"], "Furniture", "Chairs"),
    (["led desk lamp", "desk lamp", "work lamp", "ring light"], "Lighting", "Desk Lamps"),
    (["printer", "laser printer", "inkjet"], "Office", "Printers"),
    (["scanner", "document scanner"], "Office", "Scanners"),
]

POSITIVE_WORDS = {
    "premium", "excellent", "amazing", "outstanding", "superior", "professional",
    "high-quality", "high quality", "best", "top", "great", "fast", "powerful",
    "perfect", "comfortable", "reliable", "durable", "innovative", "award",
    "crisp", "clear", "immersive", "responsive", "seamless", "ultra", "pro",
}

NEGATIVE_WORDS = {
    "poor", "bad", "cheap", "broken", "defective", "terrible", "worst",
    "disappointing", "flimsy", "unreliable", "slow", "overpriced", "fails",
    "problem", "issue", "defect", "scratchy", "noisy", "laggy",
}

COMPLEXITY_MAP = {
    "Advanced": [
        "developer", "engineering", "professional", "advanced", "enterprise",
        "server", "nas", "workstation", "rackmount", "modular", "overclockable",
        "fpv", "manual focus", "raw", "pro grade", "4k 120fps",
    ],
    "Intermediate": [
        "gaming", "enthusiast", "audiophile", "customize", "configuration",
        "setup", "dslr", "mirrorless", "mechanical", "rgb", "firmware",
        "wireless protocol", "codec", "latency", "hz", "bitrate",
    ],
}

USE_CASE_PATTERNS: list[tuple[list[str], str]] = [
    (["gaming", "fps", "moba", "esports", "competitive gaming"], "High-performance gaming with responsive controls and low latency"),
    (["streaming", "content creator", "youtuber", "twitch", "obs"], "Live streaming and content creation"),
    (["home office", "work from home", "remote work", "video call", "zoom"], "Productive home office setup and video conferencing"),
    (["music", "studio", "recording", "mixing", "dj", "audiophile"], "Professional audio production and high-fidelity music listening"),
    (["travel", "commute", "portable", "on-the-go", "carry"], "Portable use during commutes and travel"),
    (["photography", "photo", "camera", "shoot", "capture"], "Photography and visual content capture"),
    (["home theater", "movie", "cinema", "surround sound", "4k tv"], "Immersive home theater and movie watching"),
    (["smart home", "automation", "alexa", "google home", "iot"], "Smart home automation and device control"),
    (["fitness", "workout", "running", "exercise", "gym", "health tracking"], "Fitness tracking and health monitoring during workouts"),
    (["storage", "backup", "archive", "nas", "data"], "Data storage, backup, and archiving"),
]

TARGET_AUDIENCE_MAP: list[tuple[list[str], str]] = [
    (["gamer", "gaming", "fps", "esport", "competitive"], "PC gamers and esports players"),
    (["professional", "business", "enterprise", "corporate"], "Business professionals and enterprise users"),
    (["audiophile", "music lover", "studio", "recording artist"], "Audiophiles and music enthusiasts"),
    (["photographer", "videographer", "content creator", "youtuber"], "Photographers and content creators"),
    (["student", "school", "college", "homework"], "Students and educators"),
    (["home user", "family", "everyday", "beginner", "casual"], "Home users and casual consumers"),
    (["fitness", "athlete", "runner", "gym"], "Fitness enthusiasts and athletes"),
    (["developer", "engineer", "programmer", "it professional"], "Developers and IT professionals"),
    (["streamer", "broadcaster", "twitch", "youtube"], "Streamers and online content creators"),
    (["remote worker", "work from home", "home office"], "Remote workers and home office users"),
]


def classify_subcategory(text: str) -> tuple[str, str]:
    lower = text.lower()
    for keywords, cat, sub in SUBCATEGORY_RULES:
        if any(k in lower for k in keywords):
            return cat, sub
    return "Electronics", "Consumer Electronics"


def extract_key_features(text: str, title: str) -> list[str]:
    """Extract 3-5 feature phrases from the product text."""
    features = set()
    patterns = [
        r"\b(\d+(?:\.\d+)?(?:K|k)?(?:Hz|hz|GB|TB|MB|mAh|W|V|mm|inch|\"|-inch)?)\b",
        r"\b(wireless|bluetooth|USB-?C|wifi|wi-fi|4K|8K|HDR|OLED|AMOLED|IPS|LCD|QLED)\b",
        r"\b(noise.cancell?ing|active noise|ANC)\b",
        r"\b(water.?proof|water.?resistant|IP\d+|IPX\d+)\b",
        r"\b(\d+.?hour.?battery|\d+h battery|long battery)\b",
        r"\b(fast.?charging|quick.?charge|rapid.?charge|PD \d+W|\d+W charging)\b",
        r"\b(RGB|backlit|per.?key lighting)\b",
        r"\b(mechanical|optical|linear|tactile|clicky) (?:switch|key)\b",
        r"\b(HDMI \d\.\d|DisplayPort \d\.\d|Thunderbolt \d)\b",
        r"\b(Dolby Atmos|DTS|surround sound|spatial audio)\b",
        r"\b(touch.?screen|touchscreen|multi.?touch)\b",
        r"\b(solar.?charging|solar powered)\b",
        r"\b(\d+ cores?|\d+ threads?)\b",
        r"\b(ray tracing|DLSS|FSR|hardware ray)\b",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            feat = m.group(0).strip()
            if len(feat) > 2:
                features.add(feat)
            if len(features) >= 5:
                break

    if len(features) < 3:
        for sent in re.split(r"[.!,;]", title):
            words = sent.strip()
            if 8 < len(words) < 60:
                features.add(words)
            if len(features) >= 4:
                break

    feats = sorted(features, key=len, reverse=True)[:5]
    return feats if feats else ["See product description for full specifications"]


def classify_sentiment(text: str) -> str:
    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Positive" if pos > 0 else "Neutral"


def classify_complexity(text: str, subcategory: str) -> str:
    lower = text.lower()
    for kw in COMPLEXITY_MAP["Advanced"]:
        if kw in lower:
            return "Advanced"
    for kw in COMPLEXITY_MAP["Intermediate"]:
        if kw in lower:
            return "Intermediate"
    if subcategory in {"Graphics Cards", "Processors", "Motherboards", "CPU Coolers", "NAS Devices", "Camera Drones"}:
        return "Intermediate"
    return "Beginner"


def extract_use_case(text: str) -> str:
    lower = text.lower()
    for keywords, use_case in USE_CASE_PATTERNS:
        if any(k in lower for k in keywords):
            return use_case
    return "General-purpose consumer electronics for everyday use"


def extract_target_audience(text: str) -> str:
    lower = text.lower()
    for keywords, audience in TARGET_AUDIENCE_MAP:
        if any(k in lower for k in keywords):
            return audience
    return "General consumers and home users"


def tag_product(title: str, raw_text: str) -> dict:
    category, subcategory = classify_subcategory(raw_text)
    key_features = extract_key_features(raw_text, title)
    use_case = extract_use_case(raw_text)
    target_audience = extract_target_audience(raw_text)
    complexity = classify_complexity(raw_text, subcategory)
    sentiment = classify_sentiment(raw_text)
    return {
        "category": category,
        "subcategory": subcategory,
        "key_features": key_features,
        "use_case": use_case,
        "target_audience": target_audience,
        "complexity": complexity,
        "sentiment": sentiment,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    conn = psycopg2.connect(settings.psycopg2_dsn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT p.id, p.title, p.raw_text
        FROM products p
        LEFT JOIN product_tags pt ON pt.product_id = p.id
        WHERE pt.id IS NULL
        ORDER BY p.id
    """)
    rows = cur.fetchall()
    log.info(f"Products needing tags: {len(rows)}")

    if not rows:
        log.info("All products already tagged.")
        cur.close()
        conn.close()
        return

    write_cur = conn.cursor()
    batch = []
    for row in tqdm(rows, desc="Tagging"):
        tags = tag_product(row["title"], row["raw_text"])
        batch.append((row["id"], json.dumps(tags)))
        if len(batch) >= args.batch_size:
            write_cur.executemany(
                "INSERT INTO product_tags (product_id, tags) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                batch,
            )
            conn.commit()
            batch = []

    if batch:
        write_cur.executemany(
            "INSERT INTO product_tags (product_id, tags) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            batch,
        )
        conn.commit()

    write_cur.close()
    cur.close()
    conn.close()
    log.info(f"Tagged {len(rows)} products.")


if __name__ == "__main__":
    main()
