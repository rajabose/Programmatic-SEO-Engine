# ============================================================
# config.py — Global Variables for Vanchai Programmatic SEO Engine
# Edit ONLY this file to update brand/UTM settings site-wide.
# ============================================================

BRAND_NAME        = "Vanchai"
BRAND_DOMAIN      = "https://www.vanchai.in"
DISCOVER_DOMAIN   = "https://discover.vanchai.in"

# UTM parameters appended to all outbound marketplace links
UTM_SOURCE   = "discover"
UTM_MEDIUM   = "programmatic_seo"
UTM_CAMPAIGN = "organic_landing"

# OpenAI model — mini keeps API costs under $50 for 10k pages
OPENAI_MODEL      = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 900   # yields ~500 words

# Output directory served by GitHub Pages
OUTPUT_DIR   = "docs"

# Product catalogue CSV path — change this if you rename or swap the CSV file
CSV_FILE     = "products.csv"

# Drip deployment: pages pushed per batch (avoid spam flag)
BATCH_SIZE   = 500

# Intent modifiers cross-joined with every product
INTENT_MODIFIERS = [
    # ── Room & Space ──────────────────────────────────────────────────────
    "for Minimalist Balcony Decor",
    "for Boho Living Room Styling",
    "for Bedroom Wall Decor",
    "for Modern Indian Home Decor",
    "for Nursery Room Decor",
    "for Office Desk Styling",
    "for Terrace Garden Decor",
    "for Meditation Corner Styling",
    "for Pooja Room Decoration",
    "for Study Room Decor",
    "for Kitchen Shelf Styling",
    "for Bathroom Decor",
    "for Entrance Foyer Styling",
    "for Dining Table Decor",
    "for Reading Nook Styling",
    "for Work From Home Desk Setup",

    # ── Aesthetic & Style ─────────────────────────────────────────────────
    "for Sustainable Home Interiors",
    "for a Coastal Boho Aesthetic",
    "for Instagrammable Home Decor",
    "for Zero-Waste Home Styling",
    "for Earthy Minimalist Interiors",
    "for Japandi Style Home",
    "for Wabi-Sabi Aesthetic",
    "for Vintage-Inspired Interiors",
    "for Ethnic Indian Interiors",
    "for Tropical Home Decor",
    "for Rustic Farmhouse Decor",
    "for Luxury Home Accents",
    "for Budget Home Makeover",
    "for Small Space Decorating",
    "for Rental Apartment Decor",

    # ── Occasions & Gifting ───────────────────────────────────────────────
    "as a Unique Wedding Gift",
    "as a Housewarming Gift",
    "for Eco-Friendly Gifting",
    "for Rustic Wedding Arrangements",
    "for Boho Wedding Decor",
    "for Wedding Mandap Decoration",
    "for Bridal Shower Gifting",
    "for Anniversary Gifting",
    "for Corporate Gifting India",
    "for Baby Shower Decor",
    "for Birthday Party Decoration",
    "for Diwali Home Decor",
    "for Festive Home Decoration",

    # ── Functional Uses ───────────────────────────────────────────────────
    "for DIY Floral Arrangements",
    "as Elegant Vase Filler",
    "as a Table Centerpiece",
    "for Dried Flower Bouquets",
    "for Floral Wreaths and Garlands",
    "for Shelf Styling Ideas",

    # ── Content & Commercial ──────────────────────────────────────────────
    "for Photography Backdrops",
    "for Flat Lay Photo Props",
    "for YouTube Video Background",
    "for Home Staging Ideas",
    "for Cafe and Restaurant Decor",
    "for Airbnb Property Styling",

    # ── Budget & Value ────────────────────────────────────────────────────
    "under 500 Rupees Gift Ideas",
    "under 1000 Rupees Home Decor",
    "for Affordable Boho Decor",

    # ── Seasonal & Trending ───────────────────────────────────────────────
    "for Monsoon Home Refresh",
    "for Summer Balcony Styling",
    "for Winter Cosy Home Decor",
    "for New Year Home Refresh",
    "Buy Online India with Free Shipping",
]

# Brand voice keywords injected into every AI generation prompt
BRAND_VOICE = (
    "sustainable living, home decor styling, natural materials, "
    "eco-friendly, Indian artisanal craftsmanship"
)
