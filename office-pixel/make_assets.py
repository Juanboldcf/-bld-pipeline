#!/usr/bin/env python3
"""Genera los assets pixel art de la Oficina BLD (originales, sin licencias externas). Pillow.

  python3 make_assets.py            -> assets/*.png + assets/manifest.json
  python3 make_assets.py --preview  -> además assets/_preview_*.png (hojas de contacto ampliadas)

Estilo: guía de juego de GBA/DS (Pokémon): personajes chibi de 32x48 px con cabeza grande, sombreado de 3 tonos con luz
desde arriba-izquierda, contorno de color (no negro), brillo en los ojos y mejillas. Paleta pastel. Los objetos se dibujan
a mano a baja resolución y se suavizan con EPX (Scale2x) para tener el doble de píxeles sin perder el trazo.
Personajes: 11 cuadros (stand0/1, blink, type0/1, hop0/1, wave0/1, sleep0/1).
"""
import json, pathlib, sys
from PIL import Image

OUT = pathlib.Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)
INK = (74, 66, 112, 255)  # contorno ciruela: más suave que el negro y funciona en tema claro y noche


def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mul(c, f):
    return tuple(max(0, min(255, round(v * f))) for v in c[:3]) + (255,)


def mix(c, d, t):
    return tuple(round(c[i] * (1 - t) + d[i] * t) for i in range(3)) + (255,)


def soft(hexc, t=0.28):
    """Lleva un color de la paleta oscura original a su versión pastel; los casi-negros pasan a ciruela suave."""
    c = rgb(hexc)
    lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    if lum < 70:
        return mix(c, rgb("#6b5f8f"), 0.55)
    return mix(c, (255, 244, 250), t)


# ---------------------------------------------------------------- personajes
FRAMES = ["stand0", "stand1", "blink", "type0", "type1", "hop0", "hop1", "wave0", "wave1", "sleep0", "sleep1"]
W, H = 32, 50

SKINS = {"a": "#ffe3cf", "b": "#f8cfa8", "c": "#e8b088", "d": "#c98c62", "e": "#9c6642"}
G = {"front": "#3b5dc9", "disc": "#257179", "estr": "#8a4fb3", "rev": "#e8e8ef", "dev": "#2f9e5b", "dis": "#c23c85", "uti": "#d9822b", "sr": "#2a7fc1", "es": "#e0b000", "pm": "#5b6ee1"}
# agente: (pelo, estilo, piel, ropa, color, pantalón, accesorio, color acc, acento)
LOOKS = {
    "player": ("#1a1c2c", "short", "c", "suit", "#121e6c", "#091144", "none", "#ff2947", "#ff2947"),
    "bld-pm-orchestrator": ("#333c57", "short", "b", "suit", G["front"], "#29366f", "cap", "#ffcd75", "#ffcd75"),
    "bld-discovery-synthesis": ("#5d275d", "long", "c", "shirt", G["disc"], "#333c57", "glasses", "#f4f4f4", "#73eff7"),
    "bld-pr-agent": ("#b13e53", "pony", "a", "sweater", "#ef7d57", "#333c57", "scarf", "#f4f4f4", "#ffcd75"),
    "bld-prd-agent": ("#1a1c2c", "afro", "e", "vest", "#41a6f6", "#29366f", "glasses", "#ffcd75", "#f4f4f4"),
    "bld-hu-agent": ("#e8c04a", "spiky", "b", "hoodie", "#38b764", "#333c57", "headband", "#b13e53", "#ffcd75"),
    "bld-ux-ui-agent": ("#5d275d", "bun", "c", "sweater", "#c23c85", "#29366f", "beret", "#73eff7", "#73eff7"),
    "bld-stakeholder-comms-agent": ("#333c57", "long", "d", "shirt", "#41a6f6", "#333c57", "headset", "#ffcd75", "#ffcd75"),
    "bld-market-trends": ("#ef7d57", "short", "b", "suit", G["disc"], "#1a1c2c", "none", "#b13e53", "#b13e53"),
    "bld-cx-insights": ("#1a1c2c", "long", "c", "shirt", G["disc"], "#333c57", "headset", "#73eff7", "#73eff7"),
    "bld-idea-tank": ("#a7f070", "spiky", "a", "hoodie", G["disc"], "#333c57", "bulb", "#ffcd75", "#ffcd75"),
    "bld-roadmap-guardian": ("#566c86", "short", "e", "vest", G["estr"], "#1a1c2c", "cap", "#a7f070", "#a7f070"),
    "bld-kr-compass": ("#b13e53", "bun", "b", "sweater", G["estr"], "#29366f", "headband", "#f4f4f4", "#f4f4f4"),
    "bld-dependency-radar": ("#333c57", "afro", "d", "shirt", G["estr"], "#1a1c2c", "shades", "#73eff7", "#73eff7"),
    "bld-prd-reviewer": ("#94b0c2", "short", "b", "lab", G["rev"], "#566c86", "glasses", "#b13e53", "#b13e53"),
    "bld-hu-reviewer": ("#1a1c2c", "short", "e", "lab", G["rev"], "#333c57", "glasses", "#41a6f6", "#41a6f6"),
    "bld-dev-agent": ("#3b5dc9", "spiky", "a", "hoodie", G["dev"], "#29366f", "headset", "#a7f070", "#a7f070"),
    "bld-qa-agent": ("#a7f070", "pony", "d", "hoodie", G["dev"], "#333c57", "shades", "#f4f4f4", "#f4f4f4"),
    "bld-docs-agent": ("#ef7d57", "long", "c", "vest", G["dev"], "#333c57", "bowtie", "#b13e53", "#b13e53"),
    "ux-ui-prototipos-issuing-bold": ("#73eff7", "bun", "b", "sweater", G["dis"], "#1a1c2c", "beret", "#ef7d57", "#ef7d57"),
    "qa-prototipo-ux-regresion": ("#566c86", "long", "c", "shirt", G["dis"], "#333c57", "glasses", "#ffcd75", "#ffcd75"),
    "generador-pr-faq": ("#ffcd75", "short", "e", "suit", G["uti"], "#29366f", "none", "#f4f4f4", "#f4f4f4"),
    "prep-campanas-marketing-prod": ("#b13e53", "pony", "b", "vest", G["uti"], "#333c57", "bowtie", "#ffcd75", "#ffcd75"),
    "reporte-mastercard-sofia": ("#5d275d", "long", "c", "shirt", G["uti"], "#1a1c2c", "scarf", "#ffcd75", "#ffcd75"),
    "pm-discovery-lead": ("#1a1c2c", "long", "b", "sweater", G["pm"], "#29366f", "glasses", "#ffcd75", "#ffcd75"),
    "pm-data-analyst": ("#566c86", "short", "e", "vest", G["pm"], "#1a1c2c", "glasses", "#73eff7", "#73eff7"),
    "pm-gtm-strategist": ("#ef7d57", "pony", "a", "suit", G["pm"], "#333c57", "headset", "#b13e53", "#b13e53"),
    "pm-comms-writer": ("#5d275d", "bun", "c", "shirt", G["pm"], "#333c57", "scarf", "#f4f4f4", "#f4f4f4"),
    "pm-ops-facilitator": ("#a7f070", "spiky", "d", "hoodie", G["pm"], "#29366f", "cap", "#ffcd75", "#ffcd75"),
    "storm-researcher": ("#1a1c2c", "afro", "d", "hoodie", G["sr"], "#29366f", "glasses", "#73eff7", "#73eff7"),
    "storm-expert": ("#94b0c2", "short", "b", "vest", G["sr"], "#333c57", "glasses", "#ffcd75", "#ffcd75"),
    "storm-writer": ("#b13e53", "long", "c", "sweater", G["sr"], "#333c57", "scarf", "#f4f4f4", "#f4f4f4"),
    "storm-start": ("#ef7d57", "pony", "a", "suit", G["es"], "#333c57", "cap", "#b13e53", "#b13e53"),
    "storm-big-picture": ("#5d275d", "bun", "c", "sweater", G["es"], "#333c57", "glasses", "#f4f4f4", "#ef7d57"),
    "storm-process": ("#1a1c2c", "short", "e", "hoodie", G["es"], "#29366f", "headband", "#ef7d57", "#ef7d57"),
    "storm-design": ("#566c86", "afro", "d", "vest", G["es"], "#1a1c2c", "shades", "#f4f4f4", "#1a1c2c"),
    "storm-verify": ("#a7f070", "spiky", "b", "shirt", G["es"], "#333c57", "headset", "#73eff7", "#73eff7"),
    "storm-render": ("#73eff7", "long", "a", "sweater", G["es"], "#1a1c2c", "beret", "#b13e53", "#b13e53"),
}
# personalidad visual: cara y rasgo extra, repartidos para que ningún par vecino se vea igual
EXPR = ["smile", "grin", "calm", "focus", "smile", "calm", "grin", "focus"]
EXTRA = ["none", "freckles", "none", "earring", "none", "beard", "none", "mole", "freckles", "none"]
# expresión fijada a mano donde el rol lo pide (revisores serios, ideas con chispa, QA traviesa…)
EXPR_OVERRIDE = {"bld-prd-reviewer": "focus", "bld-hu-reviewer": "focus", "bld-idea-tank": "grin", "bld-qa-agent": "grin", "bld-roadmap-guardian": "calm",
                 "bld-dependency-radar": "focus", "bld-cx-insights": "smile", "bld-pm-orchestrator": "calm", "player": "smile", "qa-prototipo-ux-regresion": "focus"}


class Canvas(dict):
    """(x, y) -> (color, región). Las regiones se sombrean por separado."""

    def put(self, x, y, c, reg="d"):
        if 0 <= x < W and 0 <= y < H:
            self[(x, y)] = (c, reg)

    def rect(self, x0, y0, x1, y1, c, reg="d"):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c, reg)

    def ell(self, cx, cy, rx, ry, c, reg="d", clip=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1 and (clip is None or clip(x, y)):
                    self.put(x, y, c, reg)

    def pts(self, lst, c, reg="d"):
        for x, y in lst:
            self.put(x, y, c, reg)


SHADE_REGIONS = {"hair", "cloth", "skin", "pants", "shoe", "acc"}


def finish(cv):
    """Sombreado (luz arriba-izquierda): borde inferior/derecho oscuro, borde superior/izquierdo claro; luego contorno."""
    out = {}
    for (x, y), (c, reg) in cv.items():
        if reg in SHADE_REGIONS:
            same = lambda dx, dy: cv.get((x + dx, y + dy), (None, None))[1] == reg
            if not same(1, 0) or not same(0, 1):
                c = mul(c, 0.84)
            elif not same(-1, 0) or not same(0, -1):
                c = mul(c, 1.09)
            if reg == "skin" and (x + y) % 5 == 0 and same(1, 0) and same(0, 1) and same(-1, 0):
                c = c  # piel limpia: sin ruido
        out[(x, y)] = c
    edge = {}
    for (x, y) in out:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in out and 0 <= q[0] < W and 0 <= q[1] < H:
                edge[q] = INK
    out.update(edge)
    return out


def hair_back(cv, style, col):
    c = col
    if style == "afro":
        cv.ell(15.5, 12, 12.5, 10.5, c, "hair")
    elif style == "long":
        cv.rect(5, 12, 26, 30, c, "hair"); cv.ell(15.5, 14, 11, 9.5, c, "hair")
    elif style == "pony":
        cv.rect(25, 10, 28, 22, c, "hair"); cv.pts([(28, 23), (27, 23), (28, 24)], c, "hair")
    elif style == "bun":
        cv.ell(15.5, 4.5, 4.5, 3.5, c, "hair")


def hair_front(cv, style, col):
    c, hl = col, mix(col, (255, 255, 255, 255), 0.35)
    head = lambda x, y: ((x + .5 - 15.5) / 9.5) ** 2 + ((y + .5 - 15) / 8.5) ** 2 <= 1
    if style == "afro":
        cv.ell(15.5, 11, 10.5, 6.5, c, "hair", clip=lambda x, y: y <= 12)
        cv.pts([(10, 8), (11, 8), (12, 7), (19, 7), (20, 8)], hl, "acc")
        return
    # flequillo y mechones laterales
    cv.ell(15.5, 15, 10.2, 9.2, c, "hair", clip=lambda x, y: y <= 11)
    for x in range(6, 26):
        if head(x, 12) and (x < 9 or x > 22 or (x * 7) % 5 in (0, 2)):
            cv.put(x, 12, c, "hair")
    if style == "short":
        cv.pts([(8, 12), (23, 12)], c, "hair")
    cv.rect(6, 12, 7, 17, c, "hair"); cv.rect(24, 12, 25, 17, c, "hair")
    if style == "long":
        cv.rect(5, 17, 7, 28, c, "hair"); cv.rect(24, 17, 26, 28, c, "hair")
    if style == "spiky":
        for x0 in (8, 12, 16, 20):
            cv.pts([(x0 + 1, 4), (x0, 5), (x0 + 1, 5), (x0 + 2, 5), (x0, 6), (x0 + 1, 6), (x0 + 2, 6)], c, "hair")
    if style == "bun":
        cv.ell(15.5, 4.5, 4, 3, c, "hair")
    # brillo del pelo
    cv.pts([(11, 8), (12, 8), (13, 8), (10, 9), (11, 9)], hl, "acc")


def draw_body(cv, kind, col, pants, accent, pose, dy):
    c, d, w = col, mul(col, 0.8), rgb("#fffaf5")
    lane = rgb(accent)
    # piernas y zapatos
    p = pants
    cv.rect(11, 39 + dy, 14, 44, p, "pants"); cv.rect(17, 39 + dy, 20, 44, p, "pants")
    cv.rect(10, 45, 14, 46, rgb("#fffaf5"), "shoe"); cv.rect(17, 45, 21, 46, rgb("#fffaf5"), "shoe")
    cv.rect(10, 46, 14, 46, mix(rgb("#fffaf5"), lane, 0.55), "shoe"); cv.rect(17, 46, 21, 46, mix(rgb("#fffaf5"), lane, 0.55), "shoe")
    # cuello
    # torso (trapecio suave)
    def torso(color, x0=10, x1=21, y0=25, y1=38):
        for y in range(y0 + dy, y1 + dy + 1):
            ex = 1 if y in (y0 + dy, y0 + dy + 1) else 0
            cv.rect(x0 - 1 + ex + (0 if y > y0 + dy + 1 else 0), y, x1 + 1 - ex, y, color, "cloth")
    if kind == "lab":
        torso(w, 9, 22, 25, 41)
        cv.rect(14, 25 + dy, 17, 40 + dy, mix(c, w, .2), "cloth")  # camisa debajo
        for i in range(8):
            cv.pts([(13 - i // 4, 26 + dy + i), (18 + i // 4, 26 + dy + i)], mul(w, .78), "d")  # solapas
        cv.rect(10, 33 + dy, 12, 35 + dy, mul(w, .9), "cloth"); cv.pts([(11, 32 + dy), (11, 33 + dy)], rgb("#ff7d92"), "d")
    elif kind == "vest":
        torso(w)
        cv.rect(10, 26 + dy, 13, 38 + dy, c, "cloth"); cv.rect(18, 26 + dy, 21, 38 + dy, c, "cloth")
        cv.pts([(15, 29 + dy), (16, 29 + dy), (15, 33 + dy), (16, 33 + dy)], mul(c, .6), "d")
        cv.pts([(13, 25 + dy), (18, 25 + dy), (14, 26 + dy), (17, 26 + dy)], mul(w, .8), "d")
    elif kind == "suit":
        torso(c)
        cv.rect(14, 25 + dy, 17, 33 + dy, w, "cloth")
        for i in range(7):
            cv.pts([(13 - 0, 25 + dy + i), (18, 25 + dy + i)], mul(c, .72), "d") if i % 2 == 0 else None
        cv.rect(15, 27 + dy, 16, 33 + dy, lane, "acc"); cv.pts([(15, 26 + dy), (16, 26 + dy)], mul(lane, .8), "d")
        cv.pts([(11, 31 + dy), (12, 31 + dy)], w, "d")  # pañuelo
    elif kind == "hoodie":
        cv.ell(15.5, 25.5 + dy, 7.5, 3.2, d, "cloth")
        torso(c)
        cv.rect(12, 34 + dy, 19, 37 + dy, mul(c, .86), "cloth")
        cv.pts([(13, 27 + dy), (13, 28 + dy), (13, 29 + dy), (18, 27 + dy), (18, 28 + dy), (18, 29 + dy)], w, "d")
        cv.rect(14, 26 + dy, 17, 26 + dy, mul(c, .7), "d")
    elif kind == "sweater":
        torso(c)
        cv.rect(9, 31 + dy, 22, 32 + dy, lane, "acc")
        cv.rect(10, 37 + dy, 21, 38 + dy, d, "cloth")
        cv.rect(13, 25 + dy, 18, 25 + dy, d, "cloth")
    else:  # shirt
        torso(c)
        cv.pts([(14, 25 + dy), (13, 26 + dy), (17, 25 + dy), (18, 26 + dy)], w, "d")
        for yy in (28, 31, 34):
            cv.pts([(15, yy + dy)], mul(c, .6), "d")
        cv.rect(11, 33 + dy, 13, 35 + dy, mul(c, .88), "cloth")
    if kind != "lab":  # credencial con cordón
        cv.pts([(13, 26 + dy), (13, 27 + dy), (18, 26 + dy), (18, 27 + dy)], lane, "d")
        cv.rect(17, 31 + dy, 19, 34 + dy, w, "d"); cv.rect(17, 31 + dy, 19, 32 + dy, lane, "d")
    return c, w


def accessory(cv, acc, col, dy=0):
    c = rgb(col)
    c = mix(c, (255, 244, 250), .1)
    frame = rgb("#5a4f86")
    if acc == "glasses":
        for ox in (9, 17):
            cv.rect(ox, 14, ox + 5, 14, frame, "d"); cv.rect(ox, 19, ox + 5, 19, frame, "d")
            cv.rect(ox, 14, ox, 19, frame, "d"); cv.rect(ox + 5, 14, ox + 5, 19, frame, "d")
        cv.rect(15, 16, 16, 16, frame, "d")
        cv.pts([(10, 15), (11, 15), (18, 15), (19, 15)], rgb("#e9f8ff"), "d")
    elif acc == "shades":
        cv.rect(9, 14, 14, 17, rgb("#4b4373"), "d"); cv.rect(17, 14, 22, 17, rgb("#4b4373"), "d"); cv.rect(15, 14, 16, 14, rgb("#4b4373"), "d")
        cv.pts([(10, 15), (11, 15), (18, 15), (19, 15)], c, "d")
    elif acc == "headset":
        cv.rect(5, 12, 5, 19, c, "acc"); cv.rect(26, 12, 26, 19, c, "acc"); cv.rect(5, 12, 7, 9, c, "acc")
        cv.rect(4, 15, 6, 19, mul(c, .85), "acc"); cv.rect(25, 15, 27, 19, mul(c, .85), "acc")
        cv.rect(8, 5, 23, 5, c, "acc"); cv.rect(6, 7, 7, 8, c, "acc"); cv.rect(24, 7, 25, 8, c, "acc")
        cv.rect(25, 20, 25, 22, c, "acc"); cv.rect(21, 22, 25, 23, c, "acc"); cv.put(20, 23, rgb("#ff8fa3"), "d")
    elif acc == "cap":
        cv.ell(15.5, 12, 10.6, 8, c, "acc", clip=lambda x, y: y <= 10)
        cv.rect(7, 10, 24, 11, mul(c, .9), "acc"); cv.rect(3, 11, 11, 12, mul(c, .78), "acc"); cv.rect(4, 13, 9, 13, mul(c, .78), "acc")
        cv.pts([(15, 5), (16, 5)], mix(c, (255, 255, 255, 255), .5), "d")
    elif acc == "beret":
        cv.ell(15.5, 9, 11.5, 5, c, "acc"); cv.pts([(15, 3), (16, 3), (15, 4), (16, 4)], mul(c, .8), "acc")
        cv.pts([(10, 6), (11, 6), (12, 6)], mix(c, (255, 255, 255, 255), .5), "d")
    elif acc == "headband":
        cv.rect(6, 10, 25, 11, c, "acc"); cv.pts([(24, 12), (25, 13), (26, 14), (24, 13)], c, "acc")
    elif acc == "bulb":
        cv.ell(15.5, 2, 3, 2.3, rgb("#fff0a0"), "acc"); cv.rect(14, 4, 17, 4, rgb("#c9cfe6"), "d")
        cv.pts([(13, 1), (18, 1), (11, 3), (20, 3)], rgb("#ffd96a"), "d")
    elif acc == "bowtie":
        cv.pts([(12, 25), (13, 25), (13, 26), (12, 27), (13, 27), (18, 25), (19, 25), (18, 26), (19, 27), (18, 27)], c, "acc"); cv.rect(14, 25, 17, 27, mul(c, .8), "acc")
    elif acc == "scarf":
        cv.rect(10, 24, 21, 26, c, "acc"); cv.rect(11, 27, 13, 32, mul(c, .86), "acc"); cv.rect(11, 29, 13, 29, rgb(col) if False else mul(c, .7), "d")


def face(cv, expr, eyestate, skin, hair_col, extra, dy=0):
    ink = rgb("#3c3253")
    hairc = mul(hair_col, .75)
    ex = (11, 19)
    if eyestate == "open":
        for x in ex:
            cv.rect(x, 15 + dy, x + 1, 18 + dy, ink, "d"); cv.put(x, 15 + dy, rgb("#fffaf5"), "d"); cv.put(x + 1, 18 + dy, mix(ink, rgb("#9a8fc2"), .5), "d")
    elif eyestate == "wide":
        for x in ex:
            cv.rect(x, 14 + dy, x + 2, 18 + dy, ink, "d"); cv.pts([(x, 14 + dy), (x + 1, 14 + dy)], rgb("#fffaf5"), "d")
    elif eyestate == "blink":
        for x in ex:
            cv.rect(x - 1, 17 + dy, x + 2, 17 + dy, ink, "d")
    elif eyestate == "happy":
        for x in ex:
            cv.pts([(x - 1, 18 + dy), (x, 17 + dy), (x + 1, 17 + dy), (x + 2, 18 + dy)], ink, "d")
    else:  # sleep
        for x in ex:
            cv.pts([(x - 1, 17 + dy), (x, 18 + dy), (x + 1, 18 + dy), (x + 2, 17 + dy)], ink, "d")
    blush = rgb("#ff9fb5")
    cv.pts([(9, 20 + dy), (10, 20 + dy), (9, 19 + dy), (21, 20 + dy), (22, 20 + dy), (22, 19 + dy)], mix(skin, blush, .6), "d")
    brow = hairc
    if expr == "focus":
        cv.pts([(10, 13 + dy), (11, 13 + dy), (12, 14 + dy), (19, 14 + dy), (20, 13 + dy), (21, 13 + dy)], brow, "d")
    elif eyestate == "open":
        cv.pts([(10, 13 + dy), (11, 13 + dy), (12, 13 + dy), (19, 13 + dy), (20, 13 + dy), (21, 13 + dy)], brow, "d")
    m = rgb("#b5495f")
    if expr == "grin" and eyestate != "sleep":
        cv.rect(14, 21 + dy, 17, 22 + dy, m, "d"); cv.rect(14, 21 + dy, 17, 21 + dy, rgb("#fffaf5"), "d"); cv.pts([(15, 22 + dy), (16, 22 + dy)], rgb("#ff8fa3"), "d")
    elif expr == "calm" or expr == "focus" or eyestate == "sleep":
        cv.rect(15, 22 + dy, 16, 22 + dy, m, "d")
    else:
        cv.pts([(14, 21 + dy), (15, 22 + dy), (16, 22 + dy), (17, 21 + dy)], m, "d")
    if extra == "freckles":
        cv.pts([(12, 20 + dy), (14, 20 + dy), (17, 20 + dy), (19, 20 + dy)], mix(skin, rgb("#b0714f"), .55), "d")
    elif extra == "beard":
        for x in range(9, 23):
            for y in (21, 22, 23):
                if ((x + .5 - 15.5) / 9.5) ** 2 + ((y + dy + .5 - 15) / 8.5) ** 2 <= 1 and not (14 <= x <= 17 and y == 22 + 0):
                    cv.put(x, y + dy, mix(skin, hairc, .6), "d")
        cv.rect(14, 22 + dy, 17, 22 + dy, rgb("#b5495f"), "d")
    elif extra == "mole":
        cv.put(19, 21 + dy, mix(skin, rgb("#6b4a3a"), .8), "d")
    elif extra == "earring":
        cv.pts([(5, 19 + dy), (26, 19 + dy)], rgb("#ffd96a"), "d")


def character(name, look, frame):
    hc, style, sk, kind, shirt, pants, acc, accc, accent = look
    skin = mix(rgb(SKINS[sk]), (255, 244, 250), .0)
    hair = soft(hc, .18)
    cloth, pant = soft(shirt, .30), soft(pants, .22)
    i = list(LOOKS).index(name)
    expr = EXPR_OVERRIDE.get(name, EXPR[i % len(EXPR)])
    extra = EXTRA[i % len(EXTRA)]
    base, alt = frame[:-1] if frame[-1].isdigit() else frame, frame.endswith("1")
    gdy = {"stand1": 1, "hop0": -3, "hop1": -1, "sleep0": 1, "sleep1": 2}.get(frame, 0)  # desplazamiento global del cuadro
    dy = 0
    cv = Canvas()
    hair_back(cv, style, hair)
    c, w = draw_body(cv, kind, cloth, pant, accent, base, dy)
    sleeve = rgb("#fffaf5") if kind in ("lab",) else (rgb("#fffaf5") if kind == "vest" else c)
    # brazos
    def arm(x0, y0, y1, sl=sleeve):
        cv.rect(x0, y0 + dy, x0 + 1, y1 + dy, sl, "cloth")
    if base in ("stand", "hop", "sleep", "blink"):
        arm(8, 26, 34); arm(22, 26, 34)
        cv.rect(8, 35 + dy, 9, 36 + dy, skin, "skin"); cv.rect(22, 35 + dy, 23, 36 + dy, skin, "skin")
    elif base == "type":
        arm(8, 26, 31); arm(22, 26, 31)
        cv.rect(8, 32 + dy, 12, 33 + dy, sleeve, "cloth"); cv.rect(19, 32 + dy, 23, 33 + dy, sleeve, "cloth")
        hy = 34 if alt else 33
        cv.rect(12, hy + dy, 13, hy + 1 + dy, skin, "skin"); cv.rect(18, (33 if alt else 34) + dy, 19, (34 if alt else 35) + dy, skin, "skin")
    elif base == "wave":
        arm(8, 26, 34)
        cv.rect(8, 35 + dy, 9, 36 + dy, skin, "skin")
        for y in range(18, 27):
            cv.rect(23 + (1 if y < 22 else 0), y + dy, 24 + (1 if y < 22 else 0), y + dy, sleeve, "cloth")
        hx = 26 if alt else 25
        cv.rect(hx, 14 + dy, hx + 1, 17 + dy, skin, "skin"); cv.rect(hx + (1 if alt else -1), 15 + dy, hx + (2 if alt else 0), 16 + dy, skin, "skin")
        cv.rect(24, 18 + dy, 25, 19 + dy, skin, "skin")
    # cuello y cabeza
    cv.rect(14, 23 + dy, 17, 25 + dy, mul(skin, .88), "skin")
    cv.ell(15.5, 15 + dy, 9.5, 8.5, skin, "skin")
    cv.pts([(5, 17 + dy), (5, 18 + dy), (26, 17 + dy), (26, 18 + dy)], skin, "skin")
    hair_front(cv, style, hair)
    # los pelos de arriba también se desplazan
    eyes = {"blink": "blink", "sleep0": "sleep", "sleep1": "sleep", "hop0": "wide", "hop1": "wide", "wave0": "happy", "wave1": "happy"}.get(frame, "open")
    face(cv, expr, eyes, skin, hair, extra, dy)
    accessory(cv, acc, accc)
    if gdy:
        moved = Canvas()
        for (x, y), v in cv.items():
            if 0 <= y + gdy < H:
                moved[(x, y + gdy)] = v
        cv = moved
    return finish(cv)


def to_image(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), c)
    return im


# ---------------------------------------------------------------- EPX (Scale2x): el doble de píxeles sin perder el trazo
def epx(im):
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    dst = out.load()
    get = lambda x, y: src[x, y] if 0 <= x < w and 0 <= y < h else (0, 0, 0, 0)
    for y in range(h):
        for x in range(w):
            P, A, B, C, D = get(x, y), get(x, y - 1), get(x + 1, y), get(x - 1, y), get(x, y + 1)
            p1 = p2 = p3 = p4 = P
            if C == A and C != D and A != B: p1 = A
            if A == B and A != C and B != D: p2 = B
            if D == C and D != B and C != A: p3 = C
            if B == D and B != A and D != C: p4 = D
            dst[2 * x, 2 * y], dst[2 * x + 1, 2 * y], dst[2 * x, 2 * y + 1], dst[2 * x + 1, 2 * y + 1] = p1, p2, p3, p4
    return out


# ---------------------------------------------------------------- objetos de escritorio (9x8 → EPX 18x16), paleta pastel
IC = {"k": "#4a4270", "w": "#fffaf3", "r": "#ff8fa3", "o": "#ffb48a", "y": "#ffe08a", "g": "#7fd6a0", "l": "#c4f0a0", "b": "#7f9cf5", "c": "#9be8f0",
      "p": "#c3a6f5", "s": "#c9cfe6", "d": "#9aa3c7", "n": "#c99a6b", "m": "#f59ac8"}
PROPS = {
    "compass": ["..kkkkk..", ".kwwwwwk.", "kwwwrwwwk", "kwwwrwwwk", "kwwwbwwwk", "kwwwbwwwk", ".kwwwwwk.", "..kkkkk.."],
    "telescope": ["......kk.", ".....kbbk", "....kbbk.", "...kbbk..", "..ksskk..", ".kssk.k..", "..k...k..", ".k.....k."],
    "news": ["kkkkkkkkk", "kwkkkwddk", "kwkkkwwwk", "kwwwwwddk", "kwddwwwwk", "kwwwwwddk", "kwddddwwk", "kkkkkkkkk"],
    "doc": [".kkkkkk..", ".kwwwwwk.", ".kwdddwk.", ".kwwwwwk.", ".kwdddwk.", ".kwwwwwk.", ".kwdddwk.", ".kkkkkkk."],
    "notes": ["kkkk.kkk.", "kyyk.kcck", "kyyk.kcck", "kkkk.kkk.", "..kkkkkk.", "..kllllk.", "..kllllk.", "..kkkkkk."],
    "palette": ["..kkkkk..", ".kooooyk.", "kobkkgwyk", "kokkkkrrk", "kkkkkkkkk", ".kppkkmk.", "..kkkkk..", "........."],
    "chat": ["kkkkkkkkk", "kcccccccc", "kcwcwcwck", "kcccccccc", "kkkkkcckk", "....kck..", "....kk...", "........."],
    "chart": ["k.......k", "k.....g.k", "k..b..g.k", "k..b.ygyk", "kb.bbygyk", "kb.bbygyk", "kkkkkkkkk", "........."],
    "phones": ["..kkkkk..", ".ksssssk.", "ks.....sk", "ks.....sk", "kr.....rk", "kr.....rk", "krr...rrk", ".kk...kk."],
    "bulb": ["..kkkkk..", ".kyyyyyk.", "kyywwyyyk", "kyywyyyyk", ".kyyyyyk.", "..kssssk.", "...kkkk..", "...kkkk.."],
    "map": ["kkkkkkkkk", "kgglbbbdk", "kgllbbbdk", "kgyyoobbk", "kgyyoo.bk", "kggllbbbk", "kkkkkkkkk", "........."],
    "target": ["..kkkkk..", ".kwwrwwk.", "kwrrwrrwk", "kwrwwwrwk", "kwrrwrrwk", ".kwwrwwk.", "..kkkkk..", "........."],
    "radar": ["...kkkk..", "..kccck..", ".kcckcck.", "kcckccck.", "kcccccck.", "kkkkkkkk.", "...kk....", "..kkkk..."],
    "lens": ["..kkkk...", ".kwcccwk.", "kwcwwcwk.", "kwcwwcwk.", ".kwcccwk.", "..kkkkkk.", "......kkk", ".......kk"],
    "laptop": ["kkkkkkkkk", "kccccccck", "kclllllck", "kclllllck", "kccccccck", "kkkkkkkkk", "ksssssssk", "kkkkkkkkk"],
    "bug": ["..k...k..", ".k.kkk.k.", "..kllgk..", "kkkllgkkk", "..kllgk..", "kkkllgkkk", "..kllgk..", "...kkk..."],
    "book": ["kkkkkkkk.", "kbbbbbbkk", "kbwwwwbkk", "kbwddwbkk", "kbwwwwbkk", "kbbbbbbkk", "kkkkkkkk.", "........."],
    "brush": ["......kkk", ".....kmmk", "....kmmk.", "...kynk..", "..kynk...", ".kynk....", "kynk.....", "kkk......"],
    "check": ["..kkkkk..", ".kssssdk.", "kssggssdk", "ksgggssdk", "kgg.gssdk", "kssssssdk", ".kssssdk.", "..kkkkk.."],
    "faq": ["kkkkkkkkk", "kbbbbbbbk", "kbbwwwbbk", "kbbbbwbbk", "kbbbwwbbk", "kbbbwbbbk", "kbbbbbbbk", "kkkkkkkkk"],
    "mega": ["......kkk", ".....kyyk", "kkkkkyyyk", "kooyyyyyk", "kooyyyyyk", "kkkkkyyyk", ".kk..kyyk", "..k....kk"],
    "globe": ["..kkkkk..", ".kbbgbbk.", "kbgggbbbk", "kbggbgbbk", "kbbbggbbk", ".kbbgbbk.", "..kkkkk..", "...kkk..."],
    "quill": ["......kkk", ".....kwwk", "....kwwk.", "...kwwk..", "..kwwk...", ".kdk.....", "kdk......", "kk......."],
    "card": ["kkkkkkkkk", "kbbbbbbbk", "kyybbbbbk", "kyybbbbbk", "kbbbbbbbk", "kwwwwwdwk", "kbbbbbbbk", "kkkkkkkkk"],
}
AGENT_PROP = {
    "bld-pm-orchestrator": "compass", "bld-discovery-synthesis": "telescope", "bld-pr-agent": "news", "bld-prd-agent": "doc",
    "bld-hu-agent": "notes", "bld-ux-ui-agent": "palette", "bld-stakeholder-comms-agent": "chat", "bld-market-trends": "chart",
    "bld-cx-insights": "phones", "bld-idea-tank": "bulb", "bld-roadmap-guardian": "map", "bld-kr-compass": "target",
    "bld-dependency-radar": "radar", "bld-prd-reviewer": "lens", "bld-hu-reviewer": "lens", "bld-dev-agent": "laptop",
    "bld-qa-agent": "bug", "bld-docs-agent": "book", "ux-ui-prototipos-issuing-bold": "brush", "qa-prototipo-ux-regresion": "check",
    "generador-pr-faq": "faq", "prep-campanas-marketing-prod": "mega", "reporte-mastercard-sofia": "card", "player": "doc",
    "pm-discovery-lead": "telescope", "pm-data-analyst": "chart", "pm-gtm-strategist": "mega", "pm-comms-writer": "quill", "pm-ops-facilitator": "check",
    "storm-researcher": "globe", "storm-expert": "lens", "storm-writer": "quill", "storm-start": "notes", "storm-big-picture": "map",
    "storm-process": "chart", "storm-design": "book", "storm-verify": "check", "storm-render": "palette",
}


def grid_image(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), rgb(pal[ch]))
    return im


# ---------------------------------------------------------------- escenario
def tile(kind):
    im = Image.new("RGBA", (32, 32))
    pix = im.load()
    for y in range(32):
        for x in range(32):
            if kind == "wood":
                base, line, hi = rgb("#f6e2c8"), rgb("#e3c6a0"), rgb("#fff1de")
                row = y // 8
                c = base
                if y % 8 == 0:
                    c = line
                elif (x + row * 11) % 32 == 0:
                    c = line
                elif y % 8 == 1:
                    c = hi
                elif ((x * 5 + y * 3 + row * 7) % 17) == 0 and y % 8 in (3, 4, 5):
                    c = mix(base, line, .45)
                pix[x, y] = c
            elif kind == "wall":
                base, stripe = rgb("#ece6fb"), rgb("#e1d9f6")
                c = base
                if x % 16 in (0, 1):
                    c = stripe
                elif x % 16 == 8 and y % 8 in (3, 4):
                    c = mix(base, rgb("#cbbbf0"), .6)
                pix[x, y] = c
            elif kind == "base":
                c = rgb("#fff6ea")
                if y < 2: c = rgb("#d9c7b4")
                elif y < 4: c = rgb("#fff9f1")
                elif y > 12: c = rgb("#e8d3bb")
                pix[x, y] = c if y < 16 else (0, 0, 0, 0)
    return im.crop((0, 0, 32, 16)) if kind == "base" else im


def make_desk():
    """Escritorio 56x24: tablero con brillo, borde frontal, cajón con tirador y patas."""
    im = Image.new("RGBA", (56, 24), (0, 0, 0, 0))
    top, top_hi, front, front_dk = rgb("#f2c28d"), rgb("#ffe1b9"), rgb("#d9965e"), rgb("#b87a47")
    for y in range(24):
        for x in range(56):
            if y < 9:
                c = top_hi if y == 1 else top
                if (x * 3 + y * 5) % 19 == 0 and 2 < y < 8: c = mix(top, front, .35)
                if y == 8: c = front
            elif y < 21:
                c = front_dk if x in (2, 3, 52, 53) else front
                if y == 9: c = mul(front, .86)
            else:
                c = INK if x in (2, 3, 52, 53) else (0, 0, 0, 0)
            im.putpixel((x, y), c)
    for x in range(18, 38):
        im.putpixel((x, 12), mul(front, .8)); im.putpixel((x, 19), mul(front, .8))
    for y in range(12, 20):
        im.putpixel((18, y), mul(front, .8)); im.putpixel((37, y), mul(front, .8))
    for x in range(25, 31):
        im.putpixel((x, 15), rgb("#ffe08a")); im.putpixel((x, 16), rgb("#d9a840"))
    out = Image.new("RGBA", (56, 24), (0, 0, 0, 0))
    out.alpha_composite(im)
    px = out.load()
    for y in range(24):
        for x in range(56):
            if px[x, y][3] and (x in (0, 55) or y in (0,) or (y == 20 and 1 < x < 54) or (y == 8 and False)):
                px[x, y] = INK
    for y in range(0, 21):
        px[0, y] = INK; px[55, y] = INK
    for x in range(0, 56):
        px[x, 0] = INK; px[x, 20] = INK
    return out


def make_monitor(screen, step):
    """Monitor 20x18 con marco, pantalla con líneas de 'código' que cambian por cuadro (step) y soporte."""
    im = Image.new("RGBA", (20, 18), (0, 0, 0, 0))
    sc = rgb(screen)
    for y in range(0, 14):
        for x in range(0, 20):
            edge = y in (0, 13) or x in (0, 19)
            im.putpixel((x, y), INK if edge else rgb("#e6e9f8") if (y == 1 or x in (1, 18) or y == 12) else sc)
    lit = mix(sc, (255, 255, 255, 255), .55)
    if screen != "#cfd3ea":
        lines = [(3, 3, 9), (3, 5, 13), (3, 7, 7), (3, 9, 11)]
        for i, (x0, y0, ln) in enumerate(lines):
            ln = ln + ((step + i) % 2) * 2
            for x in range(x0, min(x0 + ln, 17)):
                im.putpixel((x, y0), lit)
        im.putpixel((16 if step else 15, 10), rgb("#ffffff"))
    else:
        for (x, y) in [(8, 6), (9, 6), (8, 7), (9, 7)]:
            im.putpixel((x, y), rgb("#aab0d4"))
    for x in range(8, 12):
        for y in (14, 15):
            im.putpixel((x, y), rgb("#b8bedf"))
    for x in range(5, 15):
        im.putpixel((x, 16), INK); im.putpixel((x, 17), (0, 0, 0, 0))
    for x in range(8, 12):
        im.putpixel((x, 14), INK if False else rgb("#aeb4d6"))
    return im


def make_window():
    """Ventana 64x44 con paisaje de montaña: cielo pastel, sol, nubes, cordillera lila, montañas con nieve, pinos y lago. Cortinas a los lados."""
    Wd, Hd = 64, 44
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    P = im.load()
    frame, frame_hi, frame_dk = rgb("#fff3e0"), rgb("#ffffff"), rgb("#e8cfae")
    gx0, gy0, gx1, gy1 = 5, 5, 58, 34  # vidrio
    sky_t, sky_b = rgb("#9fd8ff"), rgb("#fff0dc")
    def ridge(x, base, amp, per, ph):  # perfil pseudo-montañoso determinista (triángulos)
        t = ((x + ph) % per) / per
        return base - amp * (1 - abs(2 * t - 1))
    for y in range(Hd):
        for x in range(Wd):
            if y < 38:
                edge = x in (0, Wd - 1) or y == 0
                if edge: P[x, y] = INK; continue
                inside = gx0 <= x <= gx1 and gy0 <= y <= gy1
                if not inside:
                    P[x, y] = frame_hi if (x == 1 or y == 1) else frame_dk if (x == Wd - 2 or y == 37) else frame
                    continue
                t = (y - gy0) / (gy1 - gy0)
                c = mix(sky_t, sky_b, min(1, t * 1.15))
                if (x - 46) ** 2 + (y - 12) ** 2 <= 14:   # sol
                    c = rgb("#fff1a8")
                elif (x - 46) ** 2 + (y - 12) ** 2 <= 22:
                    c = mix(c, rgb("#fff1a8"), .4)
                if y >= ridge(x, 25, 9, 38, 6):          # cordillera lejana
                    c = rgb("#c9b8f0") if y > ridge(x, 25, 9, 38, 6) + 1 else rgb("#ffffff")
                if y >= ridge(x, 30, 11, 30, 17):        # montañas cercanas
                    top = ridge(x, 30, 11, 30, 17)
                    c = rgb("#fbfdff") if y < top + 2.2 and top < 22 else rgb("#8fcfae") if y < top + 7 else rgb("#74bd9a")
                if y >= 30:                              # pradera y lago
                    c = rgb("#a8e0b0") if y < 33 else rgb("#8ccbf2")
                    if y >= 32 and x % 7 in (2, 3): c = rgb("#d4f1ff")
                for tx, th in ((9, 6), (14, 8), (21, 5), (40, 7), (50, 6), (54, 8)):  # pinos
                    if y <= 31 and y >= 31 - th and abs(x - tx) <= (y - (31 - th)) // 2 + (0 if y > 31 - th else 0):
                        c = rgb("#4fa882") if (x + y) % 3 else rgb("#3d8f6c")
                    if tx == x and 31 - th < y <= 32: c = rgb("#4fa882") if y < 31 else rgb("#8a6b52")
                if (x in (29, 30, 31)) or y in (19, 20): c = frame if gx0 < x < gx1 else c   # cruceta
                P[x, y] = c
            else:
                edge = y in (38, 43) or x in (0, Wd - 1) or (y == 38)
                P[x, y] = INK if edge else rgb("#f1dcc3") if y == 39 else rgb("#d9bfa3")
    for (x0, y0, ln) in [(10, 9, 8), (12, 8, 5), (30, 14, 9), (32, 13, 5)]:  # nubes
        for x in range(x0, x0 + ln):
            if gx0 < x < gx1 and not (29 <= x <= 31): P[x, y0] = rgb("#ffffff")
    for x in range(1, 5):   # cortinas
        for y in range(1, 38):
            P[x, y] = mix(rgb("#ffc2d4"), rgb("#ffa5bf"), 1 if (x + y // 3) % 3 == 0 else 0)
    for x in range(Wd - 5, Wd - 1):
        for y in range(1, 38):
            P[x, y] = mix(rgb("#ffc2d4"), rgb("#ffa5bf"), 1 if (x + y // 3) % 3 == 0 else 0)
    return im


DECO = {
    "plant": (["....g..g....", "..gglggllg..", ".glggllggl..", "gllgggllggl.", ".gggllgggl..", "..gglgggg...", "....ggg.....", "...kkkkk....", "..kooooook..", "..koorooook.", "..kooooook..", "...kooook...", "...kkkkk..."],
              {"k": "#4a4270", "g": "#7fd6a0", "l": "#c4f0a0", "o": "#ffb48a", "r": "#ff8fa3"}),
    "whiteboard": (["kkkkkkkkkkkkkkkkkkkkkkkkkkkk", "ksssssssssssssssssssssssssk", "kswwwwwwwwwwwwwwwwwwwwwwwsk", "kswyyywbbbbwwrrrwwwcccwwwsk", "kswyyywbbbbwwrrrwwwcccwwwsk", "kswwwwwwwwwwwwwwwwwwwwwwwsk", "kswddddddddwwwwdddddwwwwwsk", "kswwwwwwwwwwwwwwwwwwwwwwwsk", "kswgggwwwwwwlllllwwwwwwwwsk", "kswgggwwwwwwlllllwwwwwwwwsk", "kswwwwwwwwwwwwwwwwwwwwwwwsk", "ksssssssssssssssssssssssssk", "kkkkkkkkkkkkkkkkkkkkkkkkkkkk", "...kk..................kk..."],
                   {"k": "#4a4270", "s": "#c9cfe6", "w": "#fffaf3", "y": "#ffe08a", "b": "#9fb4f8", "r": "#ffb0a0", "c": "#9be8f0", "d": "#aab0d4", "g": "#7fd6a0", "l": "#c4f0a0"}),
    "bookshelf": (["kkkkkkkkkkkkkkkk", "knnnnnnnnnnnnnnk", "knrbyrgbpryrbgnk", "knrbyrgbpryrbgnk", "knrbyrgbpryrbgnk", "knnnnnnnnnnnnnnk", "kngybrpgbyrpgynk", "kngybrpgbyrpgynk", "kngybrpgbyrpgynk", "knnnnnnnnnnnnnnk", "kbyrpgbyrgpbyrnk", "kbyrpgbyrgpbyrnk", "kbyrpgbyrgpbyrnk", "knnnnnnnnnnnnnnk", "kkkkkkkkkkkkkkkk"],
                  {"k": "#4a4270", "n": "#d9b085", "r": "#ff8fa3", "b": "#7f9cf5", "y": "#ffe08a", "g": "#7fd6a0", "p": "#c3a6f5"}),
    "cooler": (["..kkkkkk..", ".kcccccck.", ".kcwwcccck", ".kcwwcccck", ".kccccccck", "..kkkkkk..", ".kwwwwwwk.", ".kwsssswk.", ".kwwwwwwk.", ".kwrwwbwk.", ".kwwwwwwk.", ".kwwwwwwk.", ".kkkkkkkk."],
               {"k": "#4a4270", "c": "#9be8f0", "w": "#fffaf3", "s": "#c9cfe6", "r": "#ff8fa3", "b": "#7f9cf5"}),
    "clock": (["..kkkkkk..", ".kwwwwwwk.", "kwwwkwwwwk", "kwwwkwwwwk", "kwwwkkkwwk", "kwwwwwwwwk", ".kwwwwwwk.", "..kkkkkk.."], {"k": "#4a4270", "w": "#fffaf3"}),
    "poster": (["kkkkkkkkkk", "kwwwwwwwwk", "kwyywbbbwk", "kwyywbbbwk", "kwwwwwwwwk", "kwrrrrrrwk", "kwwwwwwwwk", "kwdddddwwk", "kwwwwwwwwk", "kkkkkkkkkk"],
               {"k": "#4a4270", "w": "#fffaf3", "y": "#ffe08a", "b": "#9fb4f8", "r": "#ff8fa3", "d": "#aab0d4"}),
}


# ---------------------------------------------------------------- puertas 32x44 (cerrada y abierta), color por sala
DOOR_COLORS = {"discovery": "#7fd6c8", "estrategia": "#c3a6f5", "revision": "#ff9fb3", "taller": "#8ee0a6", "estudio": "#f5a3cb",
               "storm-research": "#8ccbf2", "event-storming": "#ffe07a", "pm-toolkit": "#a5adf5", "utilidades": "#ffc58a", "nuevo": "#ff8fa3"}


def make_door(col, open_):
    W2, H2 = 32, 44
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    c = rgb(col); cd = mul(c, .82); cl = mix(c, (255, 255, 255, 255), .4)
    P = im.load()
    for y in range(H2):
        for x in range(W2):
            arch = y < 8 and ((x + .5 - 16) / 15.5) ** 2 + ((y + .5 - 8) / 8) ** 2 > 1
            if arch:
                continue
            if y in (0, 43) and not (y == 0): pass
            P[x, y] = INK if (x in (0, 31) or y == 43 or (y < 8 and ((x + .5 - 16) / 15.5) ** 2 + ((y + .5 - 8) / 8) ** 2 > (1 - .13))) else cd if x in (1, 30) else c
    # marco claro
    for y in range(8, 43):
        for x in (1, 2, 29, 30):
            P[x, y] = cl if x in (1, 29) else cd
    if not open_:
        for (x0, y0, x1, y1) in [(5, 6, 26, 19), (5, 23, 26, 40)]:   # paneles hundidos
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    edge = x in (x0, x1) or y in (y0, y1)
                    P[x, y] = (cd if (x == x0 or y == y0) else cl) if edge else mix(c, (255, 255, 255, 255), .08)
        for y in range(8, 17):  # vidrio con brillo
            for x in range(8, 24):
                t = (y - 8) / 9
                P[x, y] = mix(rgb("#cdeeff"), rgb("#fff3e6"), t)
        for (x, y) in [(10, 9), (11, 10), (12, 11), (16, 9), (17, 10)]:
            P[x, y] = rgb("#ffffff")
        for x in range(8, 24):
            P[x, 8] = INK; P[x, 16] = cd
        P[25, 30] = rgb("#ffe08a"); P[26, 30] = rgb("#d9a840"); P[25, 31] = rgb("#d9a840"); P[26, 31] = rgb("#ffe08a")
    else:
        for y in range(5, 43):   # interior cálido con luz
            for x in range(4, 28):
                t = (y - 5) / 38
                P[x, y] = mix(rgb("#fff2c9"), rgb("#ffd9a0"), t) if x > 7 else rgb("#4a4270")
        for x in range(4, 8):    # hoja de la puerta abierta en perspectiva
            for y in range(5 + (x - 4) * 2, 43 - (x - 4) * 2):
                P[x, y] = cl if x == 4 else c if x < 7 else cd
        for y in range(34, 43):  # luz en el suelo
            for x in range(8, 28):
                P[x, y] = mix(rgb("#ffe9b0"), rgb("#ffd08a"), (x - 8) / 20) if (x + y) % 2 == 0 or y > 38 else P[x, y]
        for y in range(18, 34):  # silueta de escritorio y planta
            for x in range(11, 24):
                if y >= 28: P[x, y] = rgb("#e8b784")
        for x in range(12, 22):
            P[x, 22] = rgb("#9be8f0"); P[x, 23] = rgb("#9be8f0")
        for y in range(23, 28):
            for x in range(17, 20): P[x, y] = rgb("#7fd6c8")
    return im


# ---------------------------------------------------------------- marco 9-slice estilo cuadro de diálogo (GBA)
def make_frame(night):
    S = 24
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    P = im.load()
    ink = rgb("#4a4270") if not night else rgb("#0e1020")
    band = rgb("#c9b8f5") if not night else rgb("#566c86")
    band2 = rgb("#ffffff") if not night else rgb("#94b0c2")
    for y in range(S):
        for x in range(S):
            d = min(x, y, S - 1 - x, S - 1 - y)  # distancia al borde
            cx, cy = min(x, S - 1 - x), min(y, S - 1 - y)
            if cx < 3 and cy < 3 and (cx + cy) < 2:
                continue  # esquinas redondeadas
            if d == 0 or (cx < 2 and cy < 2 and cx + cy == 2): P[x, y] = ink
            elif d in (1, 2, 3): P[x, y] = band
            elif d == 4: P[x, y] = band2 if not night else mul(band, .8)
            elif d == 5: P[x, y] = ink if False else (0, 0, 0, 0)
    return im


def main():
    preview = "--preview" in sys.argv
    for f in OUT.glob("*.png"):
        f.unlink()
    agents = list(LOOKS)
    sheet = Image.new("RGBA", (W * len(FRAMES), H * len(agents)), (0, 0, 0, 0))
    for i, name in enumerate(agents):
        for j, fr in enumerate(FRAMES):
            sheet.alpha_composite(to_image(character(name, LOOKS[name], fr), W, H), (j * W, i * H))
    sheet.save(OUT / "characters.png")
    props = list(PROPS)
    ps = Image.new("RGBA", (18 * len(props), 16), (0, 0, 0, 0))
    for i, p in enumerate(props):
        ps.alpha_composite(epx(grid_image(PROPS[p], IC)), (i * 18, 0))
    ps.save(OUT / "props.png")
    for n, (rows, pal) in DECO.items():
        epx(grid_image(rows, pal)).save(OUT / f"{n}.png")
    for rid, col in DOOR_COLORS.items():
        make_door(col, False).save(OUT / f"door_{rid}.png"); make_door(col, True).save(OUT / f"door_{rid}_open.png")
    make_window().save(OUT / "window.png")
    make_desk().save(OUT / "desk.png")
    screens = {"off": "#cfd3ea", "cyan": "#9be8f0", "green": "#b8f0b8", "yellow": "#ffe9a0"}
    for n, c in screens.items():
        for s in (0, 1):
            make_monitor(c, s).save(OUT / f"monitor_{n}{s}.png")
    for n in ("wood", "wall", "base"):
        tile(n).save(OUT / f"tile_{n}.png")
    make_frame(False).save(OUT / "frame_light.png"); make_frame(True).save(OUT / "frame_night.png")
    manifest = {"char": {"w": W, "h": H, "frames": FRAMES, "agents": agents}, "props": {"w": 18, "h": 16, "names": props, "agent_prop": AGENT_PROP}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    if preview:
        S = 4
        n = 12
        cs = sheet.crop((0, 0, W * len(FRAMES), H * n)).resize((W * len(FRAMES) * S, H * n * S), Image.NEAREST)
        bg = Image.new("RGBA", cs.size, rgb("#f4efff")); bg.alpha_composite(cs); bg.save(OUT / "_preview_chars_a.png")
        cs = sheet.crop((0, H * n, W * len(FRAMES), H * len(agents))).resize((W * len(FRAMES) * S, (len(agents) - n) * H * S), Image.NEAREST)
        bg = Image.new("RGBA", cs.size, rgb("#f4efff")); bg.alpha_composite(cs); bg.save(OUT / "_preview_chars_b.png")
        scene = Image.new("RGBA", (360, 200), rgb("#f4efff"))
        x = 4
        for nm in ["window", "plant", "whiteboard", "bookshelf", "cooler", "clock", "poster", "desk", "monitor_cyan0", "monitor_green1"]:
            im = Image.open(OUT / f"{nm}.png"); scene.alpha_composite(im, (x % 340, 4 + (x // 340) * 46)); x += im.width + 6
        for i, rid in enumerate(DOOR_COLORS):
            scene.alpha_composite(Image.open(OUT / f"door_{rid}.png"), (4 + i * 34, 100));
        for i, rid in enumerate(list(DOOR_COLORS)[:5]):
            scene.alpha_composite(Image.open(OUT / f"door_{rid}_open.png"), (4 + i * 34, 150 if False else 146))
        scene.alpha_composite(ps, (4, 4 + 100 + 0)) if False else None
        scene.resize((scene.width * 3, scene.height * 3), Image.NEAREST).save(OUT / "_preview_scene.png")
        ps.resize((ps.width * 3, ps.height * 3), Image.NEAREST).save(OUT / "_preview_props.png")
    print("assets:", len(agents), "personajes ×", len(FRAMES), "cuadros;", len(props), "objetos")


if __name__ == "__main__":
    main()
