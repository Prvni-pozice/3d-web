# Typografické náhrady sponzorských log vozu #89 (podoba podle fotek, ne originální vektory).
# Každá funkce vrací RGBA sprite; velikost na autě určuje Plane.paste(…, výška v metrech).
import os
from PIL import Image, ImageDraw, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
WHITE = (240, 240, 238, 255)
LM_RED = (214, 18, 30, 255)
P_YELLOW = (255, 209, 0, 255)
P_RED = (218, 30, 40, 255)
KTM_ORANGE = (255, 102, 0, 255)
BLACK = (14, 14, 14, 255)


def font(name, px, variation=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), px)
    if variation:
        f.set_variation_by_name(variation)
    return f


def txt(text, f, fill, tracking=0.0, pad=0.08):
    """Text jako ořezaný RGBA sprite; tracking = mezera mezi znaky (podíl velikosti písma)."""
    px = f.size
    gap = int(tracking * px)
    widths = [f.getlength(ch) for ch in text]
    w = int(sum(widths) + gap * (len(text) - 1)) + 2 * int(pad * px) + 4
    h = int(px * 1.6)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = int(pad * px)
    for ch, cw in zip(text, widths):
        d.text((x, int(px * 0.2)), ch, font=f, fill=fill)
        x += cw + gap
    bb = im.getbbox()
    p = int(pad * px)
    return im.crop((max(0, bb[0] - p), max(0, bb[1] - p), min(w, bb[2] + p), min(h, bb[3] + p)))


def stack(sprites, gap=0.12, align="center"):
    """Sprity pod sebou."""
    w = max(s.width for s in sprites)
    g = int(gap * sum(s.height for s in sprites) / len(sprites))
    h = sum(s.height for s in sprites) + g * (len(sprites) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for s in sprites:
        x = (w - s.width) // 2 if align == "center" else 0
        im.alpha_composite(s, (x, y)); y += s.height + g
    return im


def boxed(sprite, bg, pad=(0.18, 0.14), radius=0.08, border=None, border_w=0.0):
    ph, pv = int(sprite.height * pad[0]), int(sprite.height * pad[1])
    w, h = sprite.width + 2 * ph, sprite.height + 2 * pv
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=int(h * radius), fill=bg,
                                         outline=border, width=int(h * border_w) if border else 0)
    im.alpha_composite(sprite, (ph, pv))
    return im


def liqui_moly():
    """Bílý box, červené „LIQUI / MOLY", mírně natočené."""
    f = font("Barlow-BlackItalic.ttf", 200)
    t = stack([txt("LIQUI", f, LM_RED, 0.02), txt("MOLY", f, LM_RED, 0.02)], gap=-0.05)
    return boxed(t, WHITE, pad=(0.08, 0.05), radius=0.06).rotate(5, expand=True, resample=Image.BICUBIC)


def vars_logo():
    """Tři šikmé proužky + „VARS"."""
    f = font("BarlowCondensed-ExtraBoldItalic.ttf", 220)
    word = txt("VARS", f, WHITE, 0.06)
    h = word.height
    icon = Image.new("RGBA", (int(h * 0.75), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon)
    for i in range(3):
        y0 = h * (0.28 + i * 0.17); y1 = y0 + h * 0.1; sh = h * 0.08
        d.polygon([(sh * (2 - i) + h * 0.05 * i, y0), (icon.width, y0), (icon.width - sh, y1), (sh * (1 - i) + h * 0.05 * i, y1)], fill=WHITE)
    im = Image.new("RGBA", (icon.width + word.width, h), (0, 0, 0, 0))
    im.alpha_composite(icon, (0, 0)); im.alpha_composite(word, (icon.width, 0))
    return im


def s_logo():
    return txt("[s]", font("Montserrat-VF.ttf", 200, "Light"), WHITE, 0.25)


def novologix():
    """Bílý ovál (otevřený vpravo dole) kolem „novo", pod ním „logix"."""
    f = font("Montserrat-VF.ttf", 160, "SemiBold")
    n, l = txt("novo", f, WHITE), txt("logix", f, WHITE)
    x0 = int(n.height * 0.55)
    W = x0 + max(n.width, l.width) + int(n.height * 0.3)
    H = int(n.height * 1.25 + l.height * 0.9)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lw = max(4, n.height // 12)
    ImageDraw.Draw(im).arc([lw, lw, x0 + n.width + int(n.height * 0.25), int(n.height * 1.3)], 115, 395, fill=WHITE, width=lw)
    im.alpha_composite(n, (x0, int(n.height * 0.18)))
    im.alpha_composite(l, (x0, int(n.height * 1.15)))
    return im


def pirelli():
    """Žlutý obdélník s červeným „PIRELLI"."""
    t = txt("PIRELLI", font("Barlow-BlackItalic.ttf", 200), P_RED, 0.04)
    t = t.resize((int(t.width * 1.15), t.height), Image.LANCZOS)
    return boxed(t, P_YELLOW, pad=(0.22, 0.16), radius=0.04, border=BLACK, border_w=0.035)


def xtal(weight="Light"):
    return txt("XTAL", font("Montserrat-VF.ttf", 200, weight), WHITE, 0.45)


def camea():
    return txt("camea", font("Montserrat-VF.ttf", 200, "Bold"), WHITE, 0.02)


def orlibit():
    f = font("Montserrat-VF.ttf", 200, "SemiBold")
    word = txt("ORLIBIT", f, WHITE, 0.06)
    h = word.height
    icon = Image.new("RGBA", (int(h * 1.2), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon); lw = max(4, h // 9); r = h * 0.28
    for cx in (h * 0.35, h * 0.75):
        d.ellipse([cx - r, h / 2 - r, cx + r, h / 2 + r], outline=WHITE, width=lw)
    im = Image.new("RGBA", (icon.width + word.width, h), (0, 0, 0, 0))
    im.alpha_composite(icon, (0, 0)); im.alpha_composite(word, (icon.width, 0))
    return im


def spectral_view():
    return txt("(spectral view)", font("Montserrat-VF.ttf", 200, "Medium"), WHITE, 0.02)


def ktm():
    return txt("KTM", font("Barlow-BlackItalic.ttf", 200), KTM_ORANGE, 0.02)


def fender_stack():
    """Sloupec menších log na levém předním blatníku (relativní výšky podle fotky)."""
    unit = 120
    parts = [(spectral_view(), 0.55), (orlibit(), 0.7), (xtal(), 0.7), (camea(), 1.0)]
    parts = [p.resize((int(p.width * unit * k / p.height), int(unit * k)), Image.LANCZOS) for p, k in parts]
    return stack(parts, gap=0.5)


def gt2_tag():
    """Malé označení série na startovní tabulce."""
    f = font("BarlowCondensed-ExtraBoldItalic.ttf", 200)
    g = txt("GT2", f, BLACK, 0.02)
    e = txt("EUROPE", font("BarlowCondensed-Bold.ttf", 90), BLACK, 0.15)
    return stack([g, e], gap=0.05)


def gt2_europe():
    """Pruh na čelním skle: široké kurzivní „GT" červeně (s černým proužkem), „2 EUROPE" bíle."""
    f = font("Barlow-BlackItalic.ttf", 200)
    wide = lambda im: im.resize((int(im.width * 1.7), im.height), Image.LANCZOS)
    gt = wide(txt("GT", f, (236, 28, 36, 255), 0.04))
    d = ImageDraw.Draw(gt)
    y = gt.height // 2
    d.rectangle([0, y - gt.height // 22, gt.width, y + gt.height // 22], fill=(0, 0, 0, 0))
    two = wide(txt("2", f, WHITE))
    eu = wide(txt("EUROPE", f, WHITE, 0.1))
    gap = int(gt.height * 0.5)
    h = max(gt.height, two.height, eu.height)
    im = Image.new("RGBA", (gt.width + two.width + eu.width + gap, h), (0, 0, 0, 0))
    im.alpha_composite(gt, (0, (h - gt.height) // 2))
    im.alpha_composite(two, (gt.width, (h - two.height) // 2))
    im.alpha_composite(eu, (gt.width + two.width + gap, (h - eu.height) // 2))
    return im
