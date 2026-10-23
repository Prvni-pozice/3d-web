# Do ortografických renderů domaluje mřížku v metrech (pro návrh polygonů polepu)
import sys
from PIL import Image, ImageDraw, ImageFont
S = 1500 / 5.0  # px na metr
# pohled: (osa vpravo, osa nahoru, střed vpravo, střed nahoru, znaménko vpravo)
AX = {"oside": ("y", "z", 0, 0.6, 1), "otop": ("y", "x", 0, 0, -1), "ofront": ("x", "z", 0, 0.6, 1)}
font = ImageFont.load_default(size=18)
for name, (h, v, ch, cv, sh) in AX.items():
    im = Image.open(f"{sys.argv[1]}_{name}.png").convert("RGB"); d = ImageDraw.Draw(im)
    for i in range(-30, 31):
        m = i / 10
        u = 750 + sh * (m - ch) * S; w = 750 - (m - cv) * S
        strong = i % 5 == 0
        col = (255, 0, 0) if strong else (120, 120, 255)
        if 0 <= u < 1500:
            d.line([(u, 0), (u, 1500)], fill=col, width=1)
            if strong: d.text((u + 3, 3), f"{h}={m:g}", fill=(200, 0, 0), font=font)
        if 0 <= w < 1500:
            d.line([(0, w), (1500, w)], fill=col, width=1)
            if strong: d.text((3, w + 2), f"{v}={m:g}", fill=(200, 0, 0), font=font)
    im.save(f"{sys.argv[1]}_{name}_grid.jpg", quality=88)
