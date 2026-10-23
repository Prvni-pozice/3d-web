# Krok 2: spočítá texturu polepu #89 z vypečených map pozice/normály (work/*.npy).
# Polep se kreslí jako 2D vrstvy v rovinách projekce (shora / bok / předek),
# každý texel karoserie si z nich podle své normály vybere barvu.
#
# Souřadnice auta (metry): x = šířka (+x = LEVÝ bok auta), y = délka (předek na −y), z = nahoru.
#
# python3 livery.py  →  work/livery.jpg
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "work")
FONT_NUM = os.path.join(HERE, "fonts", "RussoOne.ttf")

RED = (200, 16, 26)
CARBON = (17, 17, 19)
WHITE = (240, 240, 238)
BLACK = (12, 12, 12)
NUMBER = "89"


class Plane:
    """2D vrstva v rovině projekce. u, v jsou světové osy ('x','y','z'), rozsahy v metrech."""
    AX = {"x": 0, "y": 1, "z": 2}

    def __init__(self, u, v, urange, vrange, ppm=400):
        self.u, self.v = u, v
        self.u0, self.u1 = urange
        self.v0, self.v1 = vrange
        self.ppm = ppm
        self.w = int((self.u1 - self.u0) * ppm)
        self.h = int((self.v1 - self.v0) * ppm)
        self.img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def px(self, pu, pv):
        # v roste nahoru → obrázek má řádek 0 nahoře
        return ((pu - self.u0) * self.ppm, (self.v1 - pv) * self.ppm)

    def poly(self, pts, fill):
        self.d.polygon([self.px(*p) for p in pts], fill=fill)

    def line(self, pts, fill, width_m):
        self.d.line([self.px(*p) for p in pts], fill=fill, width=max(1, int(width_m * self.ppm)), joint="curve")

    def rect(self, c, size, fill, radius_m=0.0, outline=None, outline_m=0.0):
        (cu, cv), (su, sv) = c, size
        a = self.px(cu - su / 2, cv + sv / 2); b = self.px(cu + su / 2, cv - sv / 2)
        self.d.rounded_rectangle([a, b], radius=int(radius_m * self.ppm), fill=fill,
                                 outline=outline, width=int(outline_m * self.ppm))

    def paste(self, sprite, c, height_m):
        """Vloží RGBA sprite se středem c (svět. souřadnice) a výškou height_m."""
        s = height_m * self.ppm / sprite.height
        sp = sprite.resize((max(1, int(sprite.width * s)), max(1, int(sprite.height * s))), Image.LANCZOS)
        x, y = self.px(*c)
        self.img.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))

    def sample(self, P):
        """Bilineárně navzorkuje vrstvu v bodech P (N×3) → RGBA float 0..1."""
        pu = P[:, self.AX[self.u]]; pv = P[:, self.AX[self.v]]
        fx = (pu - self.u0) * self.ppm - 0.5
        fy = (self.v1 - pv) * self.ppm - 0.5
        a = np.asarray(self.img, dtype=np.float32) / 255.0
        x0 = np.clip(np.floor(fx).astype(int), 0, self.w - 2); y0 = np.clip(np.floor(fy).astype(int), 0, self.h - 2)
        tx = np.clip(fx - x0, 0, 1)[:, None]; ty = np.clip(fy - y0, 0, 1)[:, None]
        out = (a[y0, x0] * (1 - tx) * (1 - ty) + a[y0, x0 + 1] * tx * (1 - ty)
               + a[y0 + 1, x0] * (1 - tx) * ty + a[y0 + 1, x0 + 1] * tx * ty)
        outside = (fx < 0) | (fy < 0) | (fx > self.w - 1) | (fy > self.h - 1)
        out[outside] = 0
        return out


def text_sprite(text, px=400, fill=BLACK, italic=0.0, stroke=0, stroke_fill=None, font=FONT_NUM):
    f = ImageFont.truetype(font, px)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = int(px * 0.1)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    if italic:
        sh = italic
        nw = int(im.width + abs(sh) * im.height)
        im = im.transform((nw, im.height), Image.AFFINE, (1, sh, -sh * im.height if sh > 0 else 0, 0, 1, 0),
                          resample=Image.BICUBIC)
    return im


def number_plate(w_px=900, h_px=420, rot=0):
    """Bílá startovní tabulka s černým číslem."""
    im = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w_px - 5, h_px - 5], radius=int(h_px * 0.14), fill=WHITE, outline=BLACK, width=int(h_px * 0.05))
    num = text_sprite(NUMBER, px=int(h_px * 0.95), italic=0.12)
    s = min((w_px * 0.8) / num.width, (h_px * 0.78) / num.height)
    num = num.resize((int(num.width * s), int(num.height * s)), Image.LANCZOS)
    im.alpha_composite(num, ((w_px - num.width) // 2, (h_px - num.height) // 2))
    return im.rotate(rot, expand=True, resample=Image.BICUBIC) if rot else im


def jr_logo(h_px=900):
    """Velké obrysové „JR" týmu (zjednodušené): bílé obrysy, spodní noha R vyplněná červeně."""
    f = ImageFont.truetype(FONT_NUM, h_px)
    l, t, r, b = f.getbbox("JR")
    pad = int(h_px * 0.15)
    W_, H_ = r - l + 2 * pad, b - t + 2 * pad
    sw = max(2, int(h_px * 0.022))

    def mask(stroke):
        im = Image.new("L", (W_, H_), 0)
        ImageDraw.Draw(im).text((pad - l, pad - t), "JR", font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        return np.asarray(im, np.float32) / 255

    inner, outer = mask(0), mask(sw)
    ring = np.clip(outer - inner, 0, 1)
    leg = np.zeros_like(inner); leg[int(H_ * 0.55):, int(W_ * 0.62):] = 1  # noha R
    red = inner * leg
    rgba = np.zeros((H_, W_, 4), np.float32)
    rgba[..., :3] = np.where(ring[..., None] > 0, np.array(WHITE) / 255, np.array(RED) / 255)
    rgba[..., 3] = np.maximum(ring, red)
    out = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    sh = 0.22  # kurzíva
    return out.transform((int(W_ + sh * H_), H_), Image.AFFINE, (1, sh, -sh * H_, 0, 1, 0), resample=Image.BICUBIC)


# ---------------------------------------------------------------- vrstvy

def build_top():
    """Pohled shora: u = x, v = y."""
    L = Plane("x", "y", (-1.15, 1.15), (-2.45, 2.45))
    # kapota + blatníky vpředu
    L.poly([(-1.1, -2.4), (1.1, -2.4), (1.1, -1.05), (-1.1, -1.05)], RED)
    # černý „swoosh" od světla k A-sloupku, s bílou linkou na vnitřní hraně
    for s in (-1, 1):
        sw = [(s * 0.86, -2.05), (s * 0.66, -2.05), (s * 0.52, -1.55), (s * 0.48, -1.05), (s * 0.66, -1.05), (s * 0.74, -1.55)]
        L.poly(sw, CARBON)
        L.line([(s * 0.655, -2.06), (s * 0.505, -1.55), (s * 0.465, -1.0)], WHITE, 0.022)
    # střecha nad kokpitem
    L.poly([(-0.62, -1.05), (0.62, -1.05), (0.6, 0.5), (-0.6, 0.5)], RED)
    # kryt motoru (střed zádi)
    L.poly([(-0.48, 0.45), (0.48, 0.45), (0.44, 1.75), (-0.44, 1.75)], RED)
    for s in (-1, 1):
        L.line([(s * 0.48, 0.45), (s * 0.44, 1.75)], WHITE, 0.018)
    # startovní číslo na kapotě u pravého světla (pravý bok = −x)
    L.paste(number_plate(rot=-8), (-0.40, -1.72), 0.20)
    return L


def build_side(left):
    """Bok: u = y, v = z. Z levého boku (+x) se rovina vidí normálně, z pravého (−x)
    zrcadlově — pro pravý bok se proto sprity kreslí převrácené (na stejných pozicích y)."""
    L = Plane("y", "z", (-2.45, 2.45), (0.0, 1.3))
    flip = (lambda im: im) if left else (lambda im: im.transpose(Image.FLIP_LEFT_RIGHT))
    # červený práh mezi koly
    L.poly([(-0.98, 0.06), (1.08, 0.06), (1.04, 0.2), (-0.92, 0.22)], RED)
    # bočnice křídla
    L.poly([(1.75, 0.88), (2.4, 0.88), (2.4, 1.25), (1.75, 1.25)], RED)
    # JR přes zadní část boku
    L.paste(flip(jr_logo()), (0.45, 0.47), 0.74)
    # svislá startovní tabulka hned za předním kolem, číslo otočené o 90°
    plate = Image.new("RGBA", (420, 900), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([4, 4, 415, 895], radius=50, fill=WHITE, outline=BLACK, width=20)
    num = text_sprite(NUMBER, px=420, italic=0.12).rotate(-90, expand=True, resample=Image.BICUBIC)
    s = min(330 / num.width, 760 / num.height)
    num = num.resize((int(num.width * s), int(num.height * s)), Image.LANCZOS)
    plate.alpha_composite(num, ((420 - num.width) // 2, (900 - num.height) // 2))
    L.paste(flip(plate), (-0.86, 0.40), 0.40)
    return L


def build_front():
    """Zepředu: u = x, v = z."""
    L = Plane("x", "z", (-1.15, 1.15), (0.0, 1.3))
    # horní část nosu (pokračování kapoty)
    L.poly([(-0.6, 0.44), (0.6, 0.44), (0.62, 0.9), (-0.62, 0.9)], RED)
    # červené spodní rohy nárazníku
    for s in (-1, 1):
        L.poly([(s * 0.64, 0.08), (s * 1.08, 0.08), (s * 1.08, 0.42), (s * 0.7, 0.42)], RED)
    return L


def build_rear():
    L = Plane("x", "z", (-1.15, 1.15), (0.0, 1.3))
    # bočnice křídla zezadu
    for s in (-1, 1):
        L.poly([(s * 0.9, 0.88), (s * 1.1, 0.88), (s * 1.1, 1.25), (s * 0.9, 1.25)], RED)
    return L


def main():
    pos = np.load(os.path.join(W, "position.npy"))
    nrm = np.load(os.path.join(W, "normal.npy"))
    H, Wd = pos.shape[:2]
    m = pos[..., 3] > 0.5
    P = pos[..., :3][m].astype(np.float32) * 100.0  # model je v jednotkách 0,01 m
    N = nrm[..., :3][m].astype(np.float32)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    nx, ny, nz = N[:, 0], N[:, 1], N[:, 2]

    col = np.tile(np.array(CARBON, np.float32) / 255.0, (len(P), 1))

    def over(rgba, w):
        a = rgba[:, 3:4] * np.clip(w, 0, 1)[:, None]
        col[:] = col * (1 - a) + rgba[:, :3] * a

    def smooth(v, lo, hi):
        return np.clip((v - lo) / (hi - lo), 0, 1)

    # bok — jen vnější plochy (normála míří ven na tu stranu, kde bod leží)
    for left in (True, False):
        sgn = 1 if left else -1
        over(build_side(left).sample(P), smooth(sgn * nx, 0.3, 0.55) * (sgn * x > 0.35))

    # předek a záď
    over(build_front().sample(P), smooth(-ny, 0.35, 0.6) * (y < -1.6))
    over(build_rear().sample(P), smooth(ny, 0.35, 0.6) * (y > 1.7))
    # shora — jen nad bočnicí; křídlo (vysoko vzadu) zůstává černé
    top_w = smooth(nz, 0.25, 0.5) * (z > 0.42) * ~((y > 1.75) & (z > 0.92))
    top_w *= ~((y > -1.0) & (y < 0.5) & (z < 0.93) & (np.abs(x) < 0.62))  # vnitřek kokpitu ne, jen střecha
    over(build_top().sample(P), top_w)

    out = np.zeros((H, Wd, 3), np.float32) + np.array(CARBON, np.float32) / 255.0
    out[m] = col
    img = Image.fromarray((out[::-1] * 255).clip(0, 255).astype(np.uint8))  # npy má řádek 0 dole
    img.save(os.path.join(W, "livery.jpg"), quality=92)
    # metallicRoughness (glTF: G = roughness, B = metallic): lak a bílé lesklé, karbon saténový
    lum = out.max(axis=2)
    rough = 0.5 - 0.24 * np.clip((lum - 0.12) / 0.2, 0, 1)
    mr = np.zeros_like(out); mr[..., 1] = rough
    Image.fromarray((mr[::-1] * 255).astype(np.uint8)).save(os.path.join(W, "livery_mr.png"))
    print("livery.jpg", img.size, "texelů", m.sum())


if __name__ == "__main__":
    main()
