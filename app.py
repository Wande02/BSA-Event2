import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

st.set_page_config(
    page_title="BSA Inclusive Learning – Attendee Profile",
    page_icon="🎓",
    layout="centered",
)

NAVY = "#102F62"
GOLD = "#E5A91F"
WHITE = "#FFFFFF"

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Streamlit Cloud does not guarantee the Ubuntu/DejaVu font paths used in the
# earlier version. Use a system font only when available, otherwise fall back
# to Pillow's built-in font so the app works on any host.
FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
]


def fnt(size: int, bold: bool = False):
    index = 1 if bold else 0
    for regular, bold_path in FONT_CANDIDATES:
        path = bold_path if bold else regular
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    # Portable fallback: Pillow's built-in bitmap font.
    return ImageFont.load_default()


def fit_text(draw, text: str, max_width: int, start_size: int, bold: bool = False):
    size = start_size
    while size > 18:
        font = fnt(size, bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        # If a fallback bitmap font is in use, there is no point trying sizes.
        if font.size <= 12 if hasattr(font, "size") else False:
            break
        size -= 2
    return fnt(max(18, size), bold)


def make_profile(photo: Image.Image, name: str) -> Image.Image:
    W, H = 1080, 1350
    canvas = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)

    # Top gold line
    draw.rectangle([0, 0, W, 16], fill=GOLD)

    # Logos
    bsa_path = ASSETS_DIR / "bsa_logo.png"
    lsst_path = ASSETS_DIR / "lsst_logo.png"
    if not bsa_path.exists() or not lsst_path.exists():
        raise FileNotFoundError("Event logo assets are missing from the assets folder.")

    bsa = Image.open(bsa_path).convert("RGB")
    lsst = Image.open(lsst_path).convert("RGB")
    bsa.thumbnail((145, 145))
    lsst.thumbnail((145, 145))
    canvas.paste(bsa, (35, 32))
    canvas.paste(lsst, (900, 30))

    # Header
    header = "A REGIONAL EVENT OF BRITISH SOCIOLOGICAL ASSOCIATION"
    small = fnt(20, True)
    bbox = draw.textbbox((0, 0), header, font=small)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 48), header, fill=WHITE, font=small)

    # Main title
    title_lines = [
        ("EDUCATING THE", 160, WHITE, 42),
        ("NON-TRADITIONAL LEARNER:", 210, WHITE, 42),
        ("THE WANT, THE NEED, AND THE DEMAND FOR", 270, GOLD, 24),
        ("INCLUSIVE LEARNING IN THE 21ST CENTURY", 302, GOLD, 24),
    ]
    for text, y, fill, size in title_lines:
        font = fnt(size, True)
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((W - (bbox[2] - bbox[0])) / 2, y), text, fill=fill, font=font)

    draw.rectangle([110, 355, 970, 360], fill=GOLD)

    # Attending label
    attending = "I'M ATTENDING"
    font = fnt(60, True)
    bbox = draw.textbbox((0, 0), attending, font=font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 390), attending, fill=WHITE, font=font)

    # Circular photo frame
    cx, cy, r = 540, 660, 190
    draw.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=GOLD)
    fitted = ImageOps.fit(photo.convert("RGB"), (r * 2, r * 2), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, r * 2, r * 2], fill=255)
    canvas.paste(fitted, (cx - r, cy - r), mask)

    # Participant name only
    clean_name = name.strip() or "YOUR NAME"
    name_font = fit_text(draw, clean_name.upper(), 850, 42, True)
    bbox = draw.textbbox((0, 0), clean_name.upper(), font=name_font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 900), clean_name.upper(), fill=GOLD, font=name_font)

    # Event details card
    card = [85, 1060, 995, 1180]
    draw.rounded_rectangle(card, radius=24, fill=WHITE, outline=GOLD, width=5)

    details = [
        ("3 SEPTEMBER 2026   •   10:00 – 15:00", 1080, 25),
        ("ASTON CAMPUS EVENT CENTRE • BIRMINGHAM, UK", 1125, 19),
    ]
    for text, y, size in details:
        font = fnt(size, True)
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((W - (bbox[2] - bbox[0])) / 2, y), text, fill=NAVY, font=font)

    hashtags = "#InclusiveLearning   #BSA2026"
    font = fnt(22, True)
    bbox = draw.textbbox((0, 0), hashtags, font=font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 1240), hashtags, fill=GOLD, font=font)

    return canvas


st.markdown(
    f"""
    <style>
    .stApp {{background: #f4f6f9;}}
    .main .block-container {{max-width: 850px; padding-top: 2rem;}}
    .hero {{background: {NAVY}; padding: 24px; border-radius: 18px; color: white;}}
    .hero h1 {{color: white; margin-bottom: 4px;}}
    .hero p {{color: white;}}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🎓 Create Your BSA Event Profile</h1>
      <p>Educating the Non-Traditional Learner: The Want, the Need, and the Demand for Inclusive Learning in the 21st Century</p>
      <p><b>3 September 2026 • 10:00–15:00 • Aston Campus Event Centre, Birmingham</b></p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
st.subheader("Create your personalised profile")

photo_file = st.file_uploader(
    "1. Upload your photograph",
    type=["jpg", "jpeg", "png"],
    help="A clear head-and-shoulders photograph works best.",
)

name = st.text_input("2. Your name", placeholder="e.g. Jane Smith")

if photo_file:
    photo = Image.open(photo_file)
    st.image(photo, caption="Your uploaded photo", width=180)

if st.button("✨ Create My Profile", type="primary", use_container_width=True):
    if not photo_file:
        st.error("Please upload your photograph.")
    elif not name.strip():
        st.error("Please enter your name.")
    else:
        try:
            with st.spinner("Creating your profile..."):
                result = make_profile(Image.open(photo_file), name)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            data = buf.getvalue()

            st.success("Your profile is ready!")
            st.image(data, caption="Your BSA event profile", use_container_width=True)

            st.download_button(
                "⬇️ Download My Profile",
                data=data,
                file_name="BSA_2026_Attendee_Profile.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as exc:
            st.error("We couldn't create the profile. Please try another image or contact the event organiser.")
            st.exception(exc) if st.secrets.get("SHOW_DEBUG", False) else None

st.divider()
st.caption(
    "Privacy: your uploaded photograph is used to generate your profile during this session. "
    "The app is designed not to save participant photographs to a permanent database."
)
