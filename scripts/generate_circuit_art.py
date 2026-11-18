"""Generate three original, attribution-free circuit scene illustrations."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "images"
SIZE = (1600, 1000)
SCENES = (
    ("neon-harbor.png", (12, 20, 34), (27, 50, 67), (224, 64, 72), (70, 197, 232), "harbor"),
    ("copper-canyon.png", (37, 22, 21), (108, 54, 34), (255, 123, 72), (246, 193, 111), "canyon"),
    ("aurora-night.png", (12, 21, 32), (42, 66, 83), (103, 189, 221), (181, 204, 229), "alpine"),
)


def make_scene(filename, top, horizon, accent, highlight, setting):
    w, h = SIZE
    image = Image.new("RGB", SIZE)
    gradient = ImageDraw.Draw(image)
    for y in range(h):
        t = y / h
        color = tuple(round(a * (1 - t) + b * t) for a, b in zip(top, horizon))
        gradient.line((0, y, w, y), fill=color)

    # Broad, soft pools of venue light give the dusk scenes photographic depth.
    glow = Image.new("RGBA", SIZE)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((1020, 130, 1430, 540), fill=(*highlight, 42))
    gd.ellipse((180, 310, 560, 690), fill=(*accent, 24))
    image = Image.alpha_composite(image.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(80)))
    d = ImageDraw.Draw(image, "RGBA")

    if setting == "harbor":
        # Distant port skyline and gantry lamps.
        d.polygon([(0, 510), (0, 465), (95, 465), (95, 400), (166, 400), (166, 475),
                   (255, 475), (255, 355), (285, 355), (285, 315), (310, 355), (310, 490),
                   (425, 490), (425, 420), (498, 420), (498, 468), (620, 468), (620, 392),
                   (730, 392), (730, 507)], fill=(9, 16, 23, 205))
        d.rectangle((0, 515, w, 750), fill=(8, 18, 27, 125))
        for x, y in ((99, 465), (255, 355), (425, 420), (622, 392), (1460, 430)):
            d.line((x, y, x, y - 75), fill=(*highlight, 125), width=3)
            d.ellipse((x - 8, y - 85, x + 8, y - 69), fill=(*highlight, 220))
        for x in range(40, 680, 37):
            d.rectangle((x, 535 + (x % 31), x + 12, 544 + (x % 31)), fill=(*accent, 100))
    elif setting == "canyon":
        d.polygon([(0, 620), (0, 450), (130, 375), (230, 444), (364, 294), (500, 428),
                   (650, 285), (835, 472), (1000, 350), (1170, 480), (1340, 330), (1600, 450),
                   (1600, 780)], fill=(57, 34, 31, 190))
        d.polygon([(0, 655), (180, 520), (310, 600), (510, 422), (720, 596), (940, 440),
                   (1150, 635), (1360, 476), (1600, 594), (1600, 820), (0, 820)],
                  fill=(105, 52, 34, 170))
        for x in range(90, 1500, 190):
            d.line((x, 545 + (x % 150), x + 70, 480 + (x % 180)), fill=(*highlight, 58), width=4)
    else:
        d.polygon([(0, 650), (0, 390), (160, 200), (300, 430), (440, 170), (620, 460),
                   (820, 130), (1040, 470), (1220, 185), (1430, 445), (1600, 240), (1600, 735)],
                  fill=(31, 48, 62, 210))
        d.polygon([(0, 565), (160, 392), (300, 560), (440, 363), (620, 590), (820, 320),
                   (1040, 605), (1220, 385), (1430, 570), (1600, 385), (1600, 770), (0, 770)],
                  fill=(16, 29, 42, 190))
        for x, y in ((160, 200), (440, 170), (820, 130), (1220, 185), (1600, 240)):
            d.polygon([(x, y), (x - 35, y + 50), (x + 6, y + 33), (x + 32, y + 58)],
                      fill=(189, 213, 228, 165))

    # An elevated, sweeping circuit ribbon, lit at the edges like a broadcast graphic.
    road = [(0, 780), (170, 710), (330, 690), (455, 625), (525, 530), (675, 500),
            (810, 555), (970, 535), (1100, 615), (1270, 625), (1430, 570), (1600, 510)]
    d.line(road, fill=(0, 0, 0, 100), width=88, joint="curve")
    d.line(road, fill=(111, 124, 133, 225), width=67, joint="curve")
    d.line(road, fill=(48, 57, 67, 255), width=58, joint="curve")
    d.line(road, fill=(*accent, 235), width=4, joint="curve")
    d.line([(x, y - 27) for x, y in road], fill=(235, 237, 231, 145), width=2, joint="curve")
    d.line([(x, y + 27) for x, y in road], fill=(235, 237, 231, 120), width=2, joint="curve")
    for index, (x, y) in enumerate(road[2:-2:2]):
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(*highlight, 255))
    # Atmospheric foreground fade leaves room for the game's interface overlay.
    shade = Image.new("RGBA", SIZE)
    sd = ImageDraw.Draw(shade)
    sd.rectangle((0, 0, w, h), fill=(4, 7, 11, 24))
    sd.rectangle((0, 440, w, h), fill=(3, 5, 8, 70))
    image = Image.alpha_composite(image, shade)
    image.convert("RGB").save(OUTPUT / filename, "PNG", optimize=True)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for scene in SCENES:
        make_scene(*scene)


if __name__ == "__main__":
    main()
