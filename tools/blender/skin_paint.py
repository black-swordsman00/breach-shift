"""Bake original mottled skin and facial discoloration into the hm08 UV layout."""
import bpy
import numpy as np


def paint_skin(character, size=1024):
    base = np.asarray(character.spec["skin"], dtype=np.float32)
    pixels = np.ones((size, size, 4), dtype=np.float32)
    pixels[:, :, :3] = base * .70
    points = np.asarray([tuple(p) for p in character.points])
    eyes = [np.asarray(tuple(character.joints["joint-" + side + "-eye"])) for side in ("l", "r")]
    mouth = np.asarray(tuple(character.joints["joint-mouth"]))
    mouth[1] += character.height * .045

    def color(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        mottle = np.sin(x * 119 + np.sin(z * 73)) * np.cos(z * 131 + y * 47)
        fine = np.sin(x * 2459 + z * 1381) * np.cos(y * 1269 + z * 2317)
        broad = np.sin(x * 32 + y * 11) * np.cos(z * 41)
        c = np.repeat(base[None, :], len(p), axis=0) * (.78 + .11 * mottle + .025 * fine + .08 * broad)[:, None]
        for eye in eyes:
            d = ((x - eye[0]) / .031) ** 2 + ((z - eye[2] + .006) / .020) ** 2
            orbit = np.exp(-d * 1.1) * np.clip((y - eye[1]) * 220, 0, 1)
            c *= 1 - orbit[:, None] * np.asarray((.60, .72, .68))
            cheek = np.exp(-(((x - eye[0] * 1.6) / .026) ** 2 + ((z - eye[2] + .045) / .034) ** 2))
            c[:, 0] += cheek * .030
            c[:, 1:] *= 1 - cheek[:, None] * .32
        lips = np.exp(-(((x - mouth[0]) / .035) ** 2 + ((z - mouth[2]) / .018) ** 2)) * np.clip((y - mouth[1] + .02) * 160, 0, 1)
        c *= 1 - lips[:, None] * np.asarray((.35, .77, .76))
        # Fine marbling follows the jaw/neck and the backs of exposed hands.
        vein = np.clip((np.sin(x * 337 + np.sin(z * 91) * 2) - .94) * 8, 0, .3)
        vein *= np.clip((z - character.height * .80) * 15, 0, 1)
        c *= 1 - vein[:, None] * np.asarray((.35, .12, .20))
        return np.clip(c, .008, .8)

    for face, texcoords in character.groups["body"]:
        if min(texcoords) < 0:
            continue
        for i in range(1, len(face) - 1):
            ids = [0, i, i + 1]
            uv = np.asarray([character.uv[texcoords[j]] for j in ids]) * (size - 1)
            xyz = points[[face[j] for j in ids]]
            low = np.maximum(np.floor(uv.min(axis=0)).astype(int) - 1, 0)
            high = np.minimum(np.ceil(uv.max(axis=0)).astype(int) + 1, size - 1)
            if np.any(high < low):
                continue
            yy, xx = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
            a, b, c = uv
            denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denominator) < 1e-7:
                continue
            w0 = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / denominator
            w1 = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / denominator
            w2 = 1 - w0 - w1
            inside = (w0 >= -.08) & (w1 >= -.08) & (w2 >= -.08)
            sample = w0[inside, None] * xyz[0] + w1[inside, None] * xyz[1] + w2[inside, None] * xyz[2]
            pixels[yy[inside], xx[inside], :3] = color(sample)
    image = bpy.data.images.new(character.name + "_painted_decay", width=size, height=size)
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    tex = next(node for node in character.mats["skin"].node_tree.nodes if node.type == "TEX_IMAGE")
    tex.image = image
