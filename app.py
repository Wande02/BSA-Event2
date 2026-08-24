import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

st.set_page_config(
    page_title="BSA inclusive learning – attendee profile",
    page_icon=":material/school:",
    layout="centered",
)

NAVY = "#102F62"
GOLD = "#E5A91F"
WHITE = "#FFFFFF"

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# Montserrat (SIL Open Font License) is bundled in assets/fonts so the generated
# card renders identically on Windows, macOS and Streamlit Cloud.
FONT_FILES = {
    "regular": FONTS_DIR / "Montserrat-Regular.ttf",
    "medium": FONTS_DIR / "Montserrat-Medium.ttf",
    "semibold": FONTS_DIR / "Montserrat-SemiBold.ttf",
    "bold": FONTS_DIR / "Montserrat-Bold.ttf",
    "extrabold": FONTS_DIR / "Montserrat-ExtraBold.ttf",
}


def fnt(size: int, weight: str = "regular"):
    path = FONT_FILES.get(weight, FONT_FILES["regular"])
    if path.exists():
        return ImageFont.truetype(str(path), size)
    # Portable fallback if the bundled fonts are missing.
    return ImageFont.load_default(size)


def fit_text(draw, text: str, max_width: int, start_size: int, weight: str = "regular"):
    size = start_size
    while size > 18:
        font = fnt(size, weight)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return fnt(max(18, size), weight)


def draw_centered_text(draw, text: str, y: int, font, fill: str, width: int, tracking: int = 0):
    if tracking:
        _draw_tracked_text(draw, text, y, font, fill, width, tracking)
        return
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (width - (bbox[2] - bbox[0])) / 2
    draw.text((x, y), text, fill=fill, font=font)


def _draw_tracked_text(draw, text: str, y: int, font, fill: str, width: int, tracking: int):
    """Draw centered text with extra spacing between letters."""
    widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (width - total) / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, fill=fill, font=font)
        x += w + tracking


def _vertical_gradient(size, top_color, bottom_color):
    """A smooth top-to-bottom gradient background."""
    w, h = size
    base = Image.new("RGB", (1, h))
    tr, tg, tb = top_color
    br, bg, bb = bottom_color
    for y in range(h):
        t = y / max(h - 1, 1)
        base.putpixel((0, y), (
            int(tr + (br - tr) * t),
            int(tg + (bg - tg) * t),
            int(tb + (bb - tb) * t),
        ))
    return base.resize((w, h))


def _paste_logo(canvas, draw, logo, anchor_x, top, target_h=88, pad=16, align="center"):
    """Trim a logo's uniform border and place it on a rounded card that
    matches its own background colour, so each brand lockup reads cleanly."""
    if logo.mode in ("RGBA", "LA", "P"):
        logo = logo.convert("RGBA")
        logo = Image.alpha_composite(Image.new("RGBA", logo.size, WHITE), logo)
    logo = logo.convert("RGB")

    bg = logo.getpixel((0, 0))
    diff = ImageChops.difference(logo, Image.new("RGB", logo.size, bg))
    bbox = diff.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    scale = target_h / logo.height
    logo = logo.resize((max(1, round(logo.width * scale)), target_h), Image.Resampling.LANCZOS)

    chip_w = logo.width + pad * 2
    chip_h = target_h + pad * 2
    if align == "left":
        x0 = anchor_x
    elif align == "right":
        x0 = anchor_x - chip_w
    else:
        x0 = int(anchor_x - chip_w / 2)

    # Soft drop shadow so the card lifts off the navy background
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x0, top + 8, x0 + chip_w, top + chip_h + 8], radius=18, fill=(0, 0, 0, 120)
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))

    draw.rounded_rectangle([x0, top, x0 + chip_w, top + chip_h], radius=18, fill=bg)
    canvas.paste(logo, (x0 + pad, top + pad))


def make_profile(photo: Image.Image, name: str, role: str = "I'm attending") -> Image.Image:
    W, H = 1080, 1350

    bsa_path = ASSETS_DIR / "bsa_logo.png"
    lsst_path = ASSETS_DIR / "lsst_logo.png"
    if not bsa_path.exists() or not lsst_path.exists():
        raise FileNotFoundError("Event logo assets are missing from the assets folder.")

    canvas = _vertical_gradient((W, H), (23, 64, 128), (9, 27, 62)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Gold frame: top bar + thin inner border
    draw.rectangle([0, 0, W, 14], fill=GOLD)
    draw.rectangle([28, 28, W - 28, H - 28], outline=GOLD, width=2)

    # Brand lockups in the top corners
    _paste_logo(canvas, draw, Image.open(bsa_path), 44, 46, align="left")
    _paste_logo(canvas, draw, Image.open(lsst_path), W - 44, 46, align="right")

    # Event association line
    draw_centered_text(
        draw, "A REGIONAL EVENT OF THE BRITISH SOCIOLOGICAL ASSOCIATION",
        202, fnt(19, "semibold"), GOLD, W, tracking=2,
    )

    # Main title
    draw_centered_text(draw, "EDUCATING THE", 250, fnt(46, "extrabold"), WHITE, W)
    title2 = fit_text(draw, "NON-TRADITIONAL LEARNER", 900, 54, "extrabold")
    draw_centered_text(draw, "NON-TRADITIONAL LEARNER", 306, title2, WHITE, W)

    # Subtitle
    draw_centered_text(draw, "The want, the need, and the demand for", 382, fnt(26, "semibold"), GOLD, W)
    draw_centered_text(draw, "inclusive learning in the 21st century", 418, fnt(26, "semibold"), GOLD, W)

    # Divider + role label
    draw.rounded_rectangle([(W - 120) / 2, 470, (W + 120) / 2, 474], radius=2, fill=GOLD)
    draw_centered_text(draw, role.upper(), 492, fnt(56, "extrabold"), WHITE, W, tracking=4)

    # Circular photo with gold ring
    cx, cy, r = 540, 772, 196
    draw.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=GOLD)
    # Respect EXIF orientation so mobile uploads are not rotated/flipped
    upright = ImageOps.exif_transpose(photo)
    fitted = ImageOps.fit(upright.convert("RGB"), (r * 2, r * 2), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, r * 2, r * 2], fill=255)
    canvas.paste(fitted, (cx - r, cy - r), mask)

    # Participant name
    clean_name = name.strip() or "Your name"
    name_font = fit_text(draw, clean_name, 880, 60, "extrabold")
    draw_centered_text(draw, clean_name, 1004, name_font, GOLD, W)

    # Event details card
    draw.rounded_rectangle([95, 1120, 985, 1248], radius=22, fill=WHITE)
    draw.rounded_rectangle([95, 1120, 985, 1248], radius=22, outline=GOLD, width=3)
    draw_centered_text(draw, "3 September 2026   •   10:00 – 15:00", 1146, fnt(27, "bold"), NAVY, W)
    draw_centered_text(draw, "Aston Campus Event Centre  •  Birmingham, UK", 1192, fnt(19, "semibold"), NAVY, W)

    # Hashtags
    draw_centered_text(draw, "#InclusiveLearning     #BSA2026", 1282, fnt(23, "bold"), GOLD, W)

    return canvas.convert("RGB")


st.logo(str(ASSETS_DIR / "bsa_logo.png"), size="large")

# Partner branding
brand = st.container(horizontal=True, horizontal_alignment="center", gap="large")
brand.image(str(ASSETS_DIR / "bsa_logo.png"), width=130)
brand.image(str(ASSETS_DIR / "lsst_logo.png"), width=180)

st.title(":material/school: Create your BSA event profile", text_alignment="center")
st.markdown(
    "**Educating the Non-Traditional Learner:** the want, the need, and the demand "
    "for inclusive learning in the 21st century",
    text_alignment="center",
)
st.markdown(
    ":orange-badge[:material/event: 3 September 2026 · 10:00–15:00]"
    "&nbsp;&nbsp;:gray-badge[:material/location_on: Aston Campus Event Centre · Birmingham]",
    text_alignment="center",
)

st.subheader("Create your personalised profile", text_alignment="center")

with st.form("profile", border=True):
    photo_file = st.file_uploader(
        "Upload your photograph",
        type=["jpg", "jpeg", "png"],
        help="A clear head-and-shoulders photograph works best.",
    )
    name = st.text_input("Your name", placeholder="e.g. Jane Smith")
    role = st.segmented_control(
        "I am...",
        options=["I'm attending", "I'm speaking"],
        default="I'm attending",
    )
    submitted = st.form_submit_button(
        "Create my profile",
        type="primary",
        icon=":material/auto_awesome:",
        width="stretch",
    )

if photo_file:
    preview = ImageOps.exif_transpose(Image.open(photo_file))
    st.image(preview, caption="Your uploaded photo", width=180)

if submitted:
    if not photo_file:
        st.error("Please upload your photograph.", icon=":material/error:")
    elif not name.strip():
        st.error("Please enter your name.", icon=":material/error:")
    else:
        try:
            selected_role = role or "I'm attending"
            with st.spinner("Creating your profile..."):
                result = make_profile(Image.open(photo_file), name, selected_role)

            buf = io.BytesIO()
            result.save(buf, format="PNG")
            data = buf.getvalue()

            file_slug = "Speaker" if selected_role == "I'm speaking" else "Attendee"
            st.success("Your profile is ready!", icon=":material/check_circle:")
            st.image(data, caption="Your BSA event profile", width="stretch")

            st.download_button(
                "Download my profile",
                data=data,
                file_name=f"BSA_2026_{file_slug}_Profile.png",
                mime="image/png",
                icon=":material/download:",
                width="stretch",
            )
        except Exception as exc:
            st.error(
                "We couldn't create the profile. Please try another image or contact the event organiser.",
                icon=":material/error:",
            )
            if st.secrets.get("SHOW_DEBUG", False):
                st.exception(exc)

st.caption(
    ":material/lock: Privacy: your uploaded photograph is used to generate your profile during "
    "this session. The app is designed not to save participant photographs to a permanent database."
)
