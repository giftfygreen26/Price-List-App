#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builds data.js for the Digital Stainless Steel Price List app
from data manually transcribed off the 25-page scanned PDF.
"""
import json, re

PRODUCTS = []
PRICES = []
REVIEW = []  # extra free-text review notes not tied to a single price row

_pid_counter = 0
def new_pid():
    global _pid_counter
    _pid_counter += 1
    return f"P{_pid_counter:04d}"

_price_counter = 0
def new_price_id():
    global _price_counter
    _price_counter += 1
    return f"H{_price_counter:05d}"

PRODUCT_INDEX = {}  # key -> product id, to reuse products across dates

def get_or_create_product(ptype, ptype_th, grade, surface, dim_label, dims, unit, needs_review=False, review_note=""):
    key = (ptype, grade, surface, dim_label, unit)
    if key in PRODUCT_INDEX:
        return PRODUCT_INDEX[key]
    pid = new_pid()
    tokens = set()
    for t in [ptype, ptype_th, grade, surface, dim_label]:
        if not t:
            continue
        for w in re.split(r"[\s×x'\"()/,-]+", str(t)):
            w = w.strip().lower()
            if w:
                tokens.add(w)
    prod = {
        "id": pid,
        "productType": ptype,
        "productTypeTh": ptype_th,
        "grade": grade,
        "surface": surface,
        "dimensionLabel": dim_label,
        "dimensions": dims,
        "unit": unit,
        "active": True,
        "searchTokens": sorted(tokens),
        "needsReview": needs_review,
        "reviewNote": review_note,
    }
    PRODUCTS.append(prod)
    PRODUCT_INDEX[key] = pid
    return pid

def add_price(pid, price, price_per_kg, eff_date, source, notes="", needs_review=False, price_per_kg_calculated=False):
    if price is None and price_per_kg is None:
        return
    PRICES.append({
        "id": new_price_id(),
        "productId": pid,
        "price": price,
        "pricePerKg": price_per_kg,
        "pricePerKgCalculated": price_per_kg_calculated,
        "currency": "THB",
        "effectiveDate": eff_date,
        "source": source,
        "notes": notes,
        "needsReview": needs_review,
    })

def add_review(area, note):
    REVIEW.append({"area": area, "note": note})

# =========================================================================
# SHEET PRODUCTS - SUS 304 2B
# =========================================================================
SRC_P1 = "PDF p.1 (19 May 2026)"
SRC_P2 = "PDF p.2 (29 Apr 2026)"

sheet_304_2b_4x8 = {
    # thickness: (bkg, bpc, bpc_full, bpc_4x10)
    "19 May 2026": {
        "0.3": (122, None, None, None),
        "0.4": (95, 830, 890, None),
        "0.5": (93, 1015, 1115, None),
        "0.6": (92, 1195, None, None),
        "0.7": (91, 1385, None, 1720),
        "0.8": (89, 1530, 1720, 1960),
        "0.9": (88, 1715, 1855, 2155),
        "1.0": (87, 1880, 2035, 2375),
        "1.2": (86.5, 2250, 2420, 2815),
        "1.5": (86, 2775, 3010, 3450),
        "2.0": (85, 3690, 3995, 4530),
        "2.5": (85, 4515, None, 5655),
        "3.0": (85, 5610, 5910, 6815),
        "4.0": (103, 9620, None, None),
        "5.0": (103, 11950, None, None),
        "6.0": (103, 14420, None, None),
    },
    "29 Apr 2026": {
        "0.3": (120, None, None, None),
        "0.4": (93, 820, 870, None),
        "0.5": (91, 990, 1090, None),
        "0.6": (90, 1170, None, None),
        "0.7": (89, 1355, None, 1680),
        "0.8": (87, 1495, 1680, 1915),
        "0.9": (86, 1675, 1815, 2105),
        "1.0": (85, 1840, 1990, 2295),
        "1.2": (84.5, 2195, 2375, 2750),
        "1.5": (84, 2710, 2940, 3360),
        "2.0": (83, 3550, 3820, 4425),
        "2.5": (83, 4360, None, 5445),
        "3.0": (83, 5335, 5935, 6655),
        "4.0": (100, 9340, None, None),
        "5.0": (100, 11600, None, None),
        "6.0": (100, 14000, None, None),
    },
}
date_src = {"19 May 2026": ("2026-05-19", SRC_P1), "29 Apr 2026": ("2026-04-29", SRC_P2)}

for dkey, rows in sheet_304_2b_4x8.items():
    eff_date, src = date_src[dkey]
    for th, (bkg, bpc, bpcfull, bpc10) in rows.items():
        dim_label = f"{th}mm x 4' x 8'"
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "2B", dim_label,
                                     {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        add_price(pid, bpc, bkg, eff_date, src)
        if bpcfull:
            dim_label_full = f"{th}mm x 4' x 8' (Full Thickness / หนาเต็ม)"
            pid_full = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "2B", dim_label_full,
                                              {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8, "variant": "full_thickness"}, "Sheet")
            add_price(pid_full, bpcfull, bkg, eff_date, src, notes="Full-thickness special order variant")
        if bpc10:
            dim_label_10 = f"{th}mm x 4' x 10'"
            pid10 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "2B", dim_label_10,
                                           {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid10, bpc10, bkg, eff_date, src)

# 0.4 x 1m variant (ambiguous size meaning)
for dkey, price in {"19 May 2026": 665, "29 Apr 2026": 660}.items():
    eff_date, src = date_src[dkey]
    pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "2B", "0.4mm x 1m (special width) x 8'",
                                 {"thickness_mm": 0.4, "note": "width recorded as 1m in source, needs verification"}, "Sheet",
                                 needs_review=True, review_note="Size row printed as '0.4 x 1m' - exact width/length basis unclear, verify with source.")
    add_price(pid, price, 95 if dkey == "19 May 2026" else 93, eff_date, src, needs_review=True)

# SUS 304 2B 5x10
sheet_304_2b_5x10 = {
    "19 May 2026": {"0.7": (91, 2220), "0.8": (89, 2470), "0.9": (88, 2745), "1.0": (87, 3030),
                     "1.2": (86.5, 3600), "1.5": (86, 4470), "2.0": (85, 5890), "2.5": (85, 7405),
                     "3.0": (85, 9325), "4.0": (103, 14925), "5.0": (103, 18665), "6.0": (103, 21800)},
    "29 Apr 2026": {"0.7": (87, 2125), "0.8": (85, 2360), "0.9": (84, 2620), "1.0": (83, 2895),
                     "1.2": (82.5, 3430), "1.5": (82, 4265), "2.0": (81, 5595), "2.5": (81, 7055),
                     "3.0": (81, 8385), "4.0": (100, 14490), "5.0": (100, 18120), "6.0": (100, 21165)},
}
for dkey, rows in sheet_304_2b_5x10.items():
    eff_date, src = date_src[dkey]
    for th, (bkg, bpc) in rows.items():
        dim_label = f"{th}mm x 5' x 10'"
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "2B", dim_label,
                                     {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
        add_price(pid, bpc, bkg, eff_date, src)

# SUS 304 BA 4x8 / 4x10
sheet_304_ba = {
    "19 May 2026": {"0.40": (99.0, 890, None, None), "0.50": (97.0, 1085, None, None), "0.60": (96.0, 1285, None, None),
                     "0.70": (95.0, 1490, 1550, 1845), "0.80": (93.0, 1660, 1705, 2070), "0.90": (92.0, 1840, None, 2290),
                     "1.00": (91.0, 2050, None, 2540), "1.20": (90.5, 2390, None, 2970), "1.50": (90, 2980, None, 3725)},
    "29 Apr 2026": {"0.40": (97.0, 860, None, None), "0.50": (95.0, 1065, None, None), "0.60": (94.0, 1270, None, None),
                     "0.70": (93.0, 1460, 1515, 1805), "0.80": (91.0, 1625, 1670, 2025), "0.90": (90.0, 1800, None, 2240),
                     "1.00": (89.0, 2005, None, 2485), "1.20": (88.5, 2335, None, 2905), "1.50": (88, 2900, None, 3645)},
}
for dkey, rows in sheet_304_ba.items():
    eff_date, src = date_src[dkey]
    for th, (bkg, bpc, bpcfull, bpc10) in rows.items():
        dim_label = f"{th}mm x 4' x 8'"
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "BA", dim_label,
                                     {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        add_price(pid, bpc, bkg, eff_date, src)
        if bpcfull:
            pidf = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "BA", f"{th}mm x 4' x 8' (Full Thickness / หนาเต็ม)",
                                          {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8, "variant": "full_thickness"}, "Sheet")
            add_price(pidf, bpcfull, bkg, eff_date, src, notes="Full-thickness special order variant")
        if bpc10:
            pid10 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "BA", f"{th}mm x 4' x 10'",
                                           {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid10, bpc10, bkg, eff_date, src)

# SUS 430 BA / 430 2B  (26 Mar 2026)
eff_date, src = "2026-03-26", "PDF p.5 (26 Mar 2026)"
p430_ba = {"0.3x1m": (81, 485), "0.4": (66, 575), "0.5": (64, 705), "0.6": (63, 820), "0.7": (62, 940),
           "0.8": (60, 1085), "0.9": (59, 1140), "1.0": (58, 1245), "1.2": (57.5, 1495), "1.5": (57, 1840)}
for th, (bkg, bpc) in p430_ba.items():
    dim_label = f"{th}mm x 4' x 8'"
    pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "BA", dim_label,
                                 {"thickness_mm": th, "width_ft": 4, "length_ft": 8}, "Sheet")
    add_price(pid, bpc, bkg, eff_date, src)

p430_2b = {  # th: (bkg, bpc4x8, bpc4x10, bpc5x10)
    "0.9": (57, 1130, None, None),
    "1.0": (None, None, None, None),
    "1.2": (55.5, 1485, None, None),
    "1.5": (55, 1855, 2305, 2740),
    "2.0": (54, 2345, 2915, 3630),
    "2.5": (54, 3025, 3585, None),
    "3.0": (54, 3565, 4430, 5700),
}
for th, (bkg, bpc, bpc10, bpc510) in p430_2b.items():
    if bpc:
        dim_label = f"{th}mm x 4' x 8'"
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "2B", dim_label,
                                     {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        add_price(pid, bpc, bkg, eff_date, src)
    if bpc10:
        pid10 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "2B", f"{th}mm x 4' x 10'",
                                       {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
        add_price(pid10, bpc10, None, eff_date, src)
    if bpc510:
        pid510 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "2B", f"{th}mm x 5' x 10' (1500mm width)",
                                        {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
        add_price(pid510, bpc510, None, eff_date, src)

add_review("430 Sheet", "Handwritten notes '0.7mm หนาเต็ม 945' and '0.8mm หนาเต็ม 1355' on the 26 Mar 2026 page were not confidently attributable to BA vs 2B and were not entered as price records — verify manually.")

# =========================================================================
# SHEET - SUS 304 NO.1 (thick plate)
# =========================================================================
no1_data = {
    "2026-05-19": {"src": "PDF p.6 (19 May 2026)", "rows": {
        "3.0": (77, 4930, 8060, 15745, 6365), "4.0": (77, 7155, 10705, 21100, None),
        "4.5": (77, 7955, 12490, 24395, None), "5.0": (77, 8645, 13165, 28180, None),
        "6.0": (77, 10855, "REVIEW", None, None),
        "8.0": (78, 14430, 22540, 45125, None), "9.0": (78, 16460, 25975, None, None),
        "10.0": (78, 18215, 28550, None, None), "12.0": (82, 22920, 35750, 72490, None),
        "16.0": (97, 36520, 57620, None, None), "18.0": (97, 42680, 66930, None, None),
        "19.0": (97, 43475, 68795, None, None), "20.0": (97, 46345, None, None, None),
        "25.0": (97, 57325, 89920, None, None), "30.0": (97, 69280, 104155, None, None),
        "35.0": (97, 80580, 125710, None, None),
    }},
    "2026-05-08": {"src": "PDF p.7 (8 May 2026)", "rows": {
        "3.0": (75, 4790, 7865, 15340, 6200), "4.0": (75, 6960, 10425, 20550, None),
        "4.5": (75, 7750, 12150, 23765, None), "5.0": (75, 8420, 12880, 27450, None),
        "6.0": (75, 10500, 15500, None, None),
        "8.0": (76, 14060, 21965, 43965, None), "9.0": (76, 16035, 25310, None, None),
        "10.0": (76, 16950, 27890, None, None), "12.0": (80, 22360, 34880, 70720, None),
        "15.0": (97, 34775, 53600, None, None), "16.0": (97, 36520, 57620, None, None),
        "18.0": (97, 42680, 66930, None, None), "19.0": (97, 43475, 68795, None, None),
        "20.0": (97, 46345, 71875, None, None), "25.0": (97, 57325, 89920, None, None),
        "30.0": (97, 69280, 104155, None, None), "35.0": (97, 80580, 125710, None, None),
    }},
}
for eff_date, d in no1_data.items():
    src = d["src"]
    for th, (bkg, p4x8, p5x10, p5x20, p4x10) in d["rows"].items():
        dim_label = f"{th}mm x 4' x 8'"
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลสหนา (Plate)", "304", "NO.1", dim_label,
                                     {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        if p4x8 == "REVIEW":
            add_price(pid, None, bkg, eff_date, src, needs_review=True,
                      notes="6.0mm 5x10 cell had an ambiguous handwritten correction ('16,900' overwritten near printed '15,500'); price omitted pending verification.")
        else:
            add_price(pid, p4x8, bkg, eff_date, src)
        if p5x10:
            pid510 = get_or_create_product("Sheet", "แผ่นสแตนเลสหนา (Plate)", "304", "NO.1", f"{th}mm x 5' x 10'",
                                            {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
            add_price(pid510, p5x10, None, eff_date, src)
        elif th == "6.0":
            pid510 = get_or_create_product("Sheet", "แผ่นสแตนเลสหนา (Plate)", "304", "NO.1", f"{th}mm x 5' x 10'",
                                            {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
            add_price(pid510, None, None, eff_date, src, needs_review=True,
                      notes="Handwritten correction on this cell is ambiguous ('16,900' vs printed '15,500'); verify manually.")
        if p5x20:
            pid520 = get_or_create_product("Sheet", "แผ่นสแตนเลสหนา (Plate)", "304", "NO.1", f"{th}mm x 5' x 20'",
                                            {"thickness_mm": float(th), "width_ft": 5, "length_ft": 20}, "Sheet")
            add_price(pid520, p5x20, None, eff_date, src)
        if p4x10:
            pid410 = get_or_create_product("Sheet", "แผ่นสแตนเลสหนา (Plate)", "304", "NO.1", f"{th}mm x 4' x 10'",
                                            {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid410, p4x10, None, eff_date, src)

# =========================================================================
# SHEET - 304 / 430 HL, NO.4, NO.8   (three dates)
# =========================================================================
hl48_data = {
    "2026-05-19": {"src": "PDF p.8 (19 May 2026)", "rows": {
        "0.5": (1425, 1985, None, None, None, None),
        "0.6": (1340, 1890, None, None, 965, None),
        "0.7": (1515, 2065, 1880, 2520, 1070, None),
        "0.8": (1660, 2210, 2120, 2760, 1215, None),
        "0.9": (1845, 2395, 2315, 2955, 1270, None),
        "1.0": (2010, 2560, 2535, 3175, 1375, None),
        "1.2": (2380, 2930, 2975, 3615, 1625, None),
        "1.5": (2905, 3455, 3610, 4250, 1970, None),
        "2.0": (3820, 4370, 4690, 5330, 2475, 3075),
        "2.5": (4645, 5195, 5815, 6455, 3155, 3745),
        "3.0": (5740, 6290, 6975, 7615, 3695, 4590),
    }, "hl510": {"0.9": None, "1.0": 3480, "1.2": 4050, "1.5": 4920, "2.0": 6340, "2.5": 7855, "3.0": 9775},
       "no8_510": {"0.9": None, "1.0": 4230, "1.2": 4800, "1.5": 5670, "2.0": 7090, "2.5": 8605, "3.0": 10525}},
    "2026-04-29": {"src": "PDF p.9 (29 Apr 2026)", "rows": {
        "0.5": (1425, 1985, None, None, None, None),
        "0.6": (1315, 1865, None, None, 965, None),
        "0.7": (1485, 2035, 1840, 2480, 1070, None),
        "0.8": (1625, 2175, 2075, 2715, 1215, None),
        "0.9": (1805, 2355, 2265, 2905, 1270, None),
        "1.0": (1970, 2520, 2455, 3095, 1375, None),
        "1.2": (2325, 2875, 2910, 3550, 1625, None),
        "1.5": (2840, 3390, 3520, 4160, 1970, None),
        "2.0": (3680, 4230, 4585, 5225, 2475, 3075),
        "2.5": (4490, 5040, 5605, 6245, 3155, 3745),
        "3.0": (5465, 6015, 6815, 7455, 3695, 4590),
    }, "hl510": {"0.9": None, "1.0": 3345, "1.2": 3880, "1.5": 4715, "2.0": 6045, "2.5": 7505, "3.0": 8835},
       "no8_510": {"0.9": None, "1.0": 4095, "1.2": 4630, "1.5": 5465, "2.0": 6795, "2.5": 8255, "3.0": 9585}},
    "2026-03-26": {"src": "PDF p.10 (26 Mar 2026)", "rows": {
        "0.5": (1400, 1960, None, None, None, None),
        "0.6": (1290, 1840, None, None, 965, None),
        "0.7": (1460, 2010, 1805, 2445, 1070, None),
        "0.8": (1620, 2170, 2060, 2700, 1215, None),
        "0.9": (1770, 2320, 2220, 2860, 1270, None),
        "1.0": (1925, 2475, 2400, 3040, 1375, None),
        "1.2": (2265, 2815, 2820, 3460, 1625, None),
        "1.5": (2775, 3325, 3440, 4080, 1970, None),
        "2.0": (3595, 4145, 4475, 5115, 2475, 3075),
        "2.5": (4425, 4975, 5475, 6115, 3155, 3745),
        "3.0": (5320, 5870, 6655, 7295, 3695, 4590),
    }, "hl510": {"0.9": None, "1.0": 3260, "1.2": 3800, "1.5": 4610, "2.0": 5930, "2.5": 7330, "3.0": 8625},
       "no8_510": {"0.9": None, "1.0": 4010, "1.2": 4550, "1.5": 5360, "2.0": 6680, "2.5": 8080, "3.0": 9375},
       "note": "Marked 'ต่ำสุด' (lowest recorded) by hand on source page."},
}
for eff_date, d in hl48_data.items():
    src = d["src"]
    for th, (p304hl48, p304no848, p304hl410, p304no8410, p430hl48, p430hl410) in d["rows"].items():
        pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "HL/NO.4", f"{th}mm x 4' x 8'",
                                     {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        add_price(pid, p304hl48, None, eff_date, src)
        pid2 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "NO.8", f"{th}mm x 4' x 8'",
                                      {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
        add_price(pid2, p304no848, None, eff_date, src)
        if p304hl410:
            pid3 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "HL/NO.4", f"{th}mm x 4' x 10'",
                                          {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid3, p304hl410, None, eff_date, src)
        if p304no8410:
            pid4 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "NO.8", f"{th}mm x 4' x 10'",
                                          {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid4, p304no8410, None, eff_date, src)
        if p430hl48:
            pid5 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "HL/NO.4", f"{th}mm x 4' x 8'",
                                          {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
            add_price(pid5, p430hl48, None, eff_date, src)
        if p430hl410:
            pid6 = get_or_create_product("Sheet", "แผ่นสแตนเลส", "430", "HL/NO.4", f"{th}mm x 4' x 10'",
                                          {"thickness_mm": float(th), "width_ft": 4, "length_ft": 10}, "Sheet")
            add_price(pid6, p430hl410, None, eff_date, src)
    for th, price in d["hl510"].items():
        if price:
            pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "HL", f"{th}mm x 5' x 10'",
                                         {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
            add_price(pid, price, None, eff_date, src)
    for th, price in d["no8_510"].items():
        if price:
            pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "304", "NO.8", f"{th}mm x 5' x 10'",
                                         {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10}, "Sheet")
            add_price(pid, price, None, eff_date, src)

# =========================================================================
# SHEET - SUS 201 2B J1 4x8   (8 Jun 2026)
# =========================================================================
eff_date, src = "2026-06-08", "PDF p.25 (8 Jun 2026)"
p201 = {"0.4": (7.82, 500), "0.5": (10.37, 580), "0.7": (14.21, 715), "0.8": (17.2, 840),
        "0.9": (None, 935), "1.0": (18.91, 995), "1.2": (23.92, 1265), "1.5": (30.95, 1560),
        "2.0": (40.39, 1995), "3.0": (62.06, 3150)}
for th, (kgpc, bpc) in p201.items():
    dim_label = f"{th}mm x 4' x 8'"
    pid = get_or_create_product("Sheet", "แผ่นสแตนเลส", "201", "2B J1", dim_label,
                                 {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8}, "Sheet")
    ppk = round(bpc / kgpc, 2) if (kgpc and bpc) else None
    add_price(pid, bpc, ppk, eff_date, src, price_per_kg_calculated=bool(ppk))

# =========================================================================
# ACCESSORIES - PVC coating
# =========================================================================
pvc_items = [
    ("PVC Coating - Blue, 4'x8'", 100), ("PVC Coating - Black/White, 4'x8'", 120),
    ("PVC Coating - Blue, 4'x10'", 130), ("PVC Coating - Black/White, 4'x10'", 150),
    ("PVC Coating - Black/White, 5'x10'", 300),
    ("PVC Novacel - Black/White, 4'x8'", 150), ("PVC Novacel - Blue, 4'x10'", 190),
]
for label, price in pvc_items:
    pid = get_or_create_product("Accessory", "บริการเคลือบผิว", "-", "-", label, {"note": "Coating service add-on, price per sheet"}, "Sheet")
    add_price(pid, price, None, "2026-05-19", "PDF p.1-2 (consistent both 19 May & 29 Apr 2026)")

# =========================================================================
# PIPE - Round polished SUS304  (3 Jul 2026)
# =========================================================================
eff_date, src = "2026-07-03", "PDF p.11 (3 Jul 2026)"
round_pipe = {
    ('3/8"', 9.5): {"0.8": 100, "1": 120, "1.2": 140},
    ('1/2"', 12.7): {"0.8": 120, "1": 145, "1.2": 185, "1.5": 225, "2": 330},
    ('5/8"', 15.9): {"0.8": 180, "1": 190, "1.2": 225, "1.5": 320, "2": 370},
    ('3/4"', 19.0): {"0.8": 235, "1": 230, "1.2": 270, "1.5": 330, "2": 480},
    ('7/8"', 22.2): {"0.8": 251, "1": 270, "1.2": 320, "1.5": 390, "2": 565},
    ('1"', 25.4): {"1": 310, "1.2": 365, "1.5": 450, "2": 580, "3": 955},
    ('1-1/4"', 31.8): {"1": 390, "1.2": 460, "1.5": 570, "2": 740, "3": 1225},
    ('1-1/2"', 38.1): {"1": 470, "1.2": 560, "1.5": 690, "2": 895, "3": 1495},
    ('2"', 50.8): {"1": 630, "1.2": 750, "1.5": 925, "2": 1210, "3": 1930},
    ('2-1/2"', 63.5): {"1.2": 945, "1.5": 1165, "2": 1525, "3": 2565},
    ('3"', 76.2): {"1.2": 1135, "1.5": 1405, "2": 1840, "3": 3035},
    ('4"', 101.6): {"1.5": 1880, "2": 2470, "3": 4175},
}
for (size_in, size_mm), th_map in round_pipe.items():
    for th, price in th_map.items():
        dim_label = f'{size_in} OD ({size_mm}mm), wall {th}mm x 6m'
        pid = get_or_create_product("Round Pipe", "ท่อกลม", "304", "Polished (ขัดเงา)", dim_label,
                                     {"size_inch": size_in, "od_mm": size_mm, "wallThickness_mm": float(th)}, "เส้น (Length/pc)")
        add_price(pid, price, None, eff_date, src)
add_review("Round Pipe (304 Polished)", "Brand price adjustments noted on source: TOYO brand +5 THB/length for 5/8\"-2\", +10-15 THB/length for 2-1/2\" and up. Not applied to base prices — treat as a surcharge note for Sales.")

# =========================================================================
# SQUARE / RECTANGULAR TUBE  SUS304  6m length (3 Jul 2026) - two finishes
# =========================================================================
eff_date, src = "2026-07-03", "PDF p.12 (3 Jul 2026, matte finish)"
sq_tube_matte = {
    '3/8"x3/8"': {"1.0": 155},
    '1/2"x1/2"': {"1.0": 200, "1.2": 240, "1.5": 295},
    '3/4"x3/4"': {"1.0": 310, "1.2": 370, "1.5": 460, "2.0": 605},
    '1"x1"': {"1.0": 410, "1.2": 490, "1.5": 605, "2.0": 800, "3.0": 1215},
    '1-1/4"x1-1/4"': {"1.0": 520, "1.2": 620, "1.5": 770, "2.0": 1015, "3.0": 1655},
    '1-1/2"x1-1/2"': {"1.0": 625, "1.2": 745, "1.5": 925, "2.0": 1220, "3.0": 1975},
    '2"x2"': {"1.2": 975, "1.5": 1210, "2.0": 1600, "3.0": 2625},
    '3"x3"': {"1.5": 2530, "2.0": 2555, "3.0": 4035, "4.0": 7425, "5.0": 8970},
    '4"x4"': {"2.0": 3195, "3.0": 5045, "4.0": 9350, "5.0": 11500},
    '5"x5"': {"4.0": 11575, "5.0": 14580},
}
for size, th_map in sq_tube_matte.items():
    for th, price in th_map.items():
        pid = get_or_create_product("Square Tube", "ท่อสี่เหลี่ยมด้านเท่า", "304", "Matte (ด้าน)", f"{size}, wall {th}mm x 6m",
                                     {"size_inch": size, "wallThickness_mm": float(th)}, "เส้น (Length/pc)")
        add_price(pid, price, None, eff_date, src)

rect_tube_nomark = {
    "10x20": {"1.2": 325}, "13x26": {"1.0": 315, "1.2": 370, "1.5": 495},
    "15x39": {"1.0": 485, "1.5": 525, "2.0": 955},
    "20x40": {"1.0": 490, "1.2": 585, "1.5": 730, "2.0": 960},
    "25x50": {"1.0": 615, "1.2": 730, "1.5": 910, "2.0": 1200, "3.0": 1960},
    "40x80": {"1.2": 1170, "1.5": 1455, "2.0": 1920, "3.0": 2945},
    "50x100": {"1.5": 1820, "2.0": 2400, "3.0": 3680, "4.0": 6925, "5.0": 8450},
    "75x150": {"5.0": 13100},
}
for size, th_map in rect_tube_nomark.items():
    for th, price in th_map.items():
        needs_rev = (size == "15x39" and th == "1.5")  # 1.2 column value was illegible, 1.5 kept but flagged for cross-check
        pid = get_or_create_product("Rectangular Tube", "ท่อสี่เหลี่ยมกล่อง (ไม่ขีด)", "304", "Matte (ไม่ขีด)", f"{size}mm, wall {th}mm x 6m",
                                     {"size_mm": size, "wallThickness_mm": float(th)}, "เส้น (Length/pc)")
        add_price(pid, price, None, eff_date, src)
add_review("Rectangular Tube 15x39mm", "1.2mm-wall column price was illegible on the source page (appeared as '-90'); omitted — verify manually.")

eff_date, src = "2026-07-03", "PDF p.13 (3 Jul 2026, polished finish - ท่อเงา)"
sq_tube_polished = {
    '3/8"x3/8"': {"1.0": 190},
    '1/2"x1/2"': {"1.0": 200, "1.2": 245, "1.5": 300},
    '5/8"x5/8"': {"1.2": 345},
    '3/4"x3/4"': {"1.0": 275, "1.2": 280, "1.5": 445},
    '1"x1"': {"1.0": 410, "1.2": 465, "1.5": 625, "2.0": 965},
    '1-1/4"x1-1/4"': {"1.0": 535, "1.2": 580, "1.5": 785, "2.0": 1090, "3.0": 1665},
    '1-1/2"x1-1/2"': {"1.0": 635, "1.2": 695, "1.5": 895, "2.0": 1665},
    '2"x2"': {"1.2": 990, "1.5": 1180, "2.0": 1780, "3.0": 2535},
    '3"x3"': {"2.0": 2770, "3.0": 4190},
}
for size, th_map in sq_tube_polished.items():
    for th, price in th_map.items():
        pid = get_or_create_product("Square Tube", "ท่อสี่เหลี่ยมด้านเท่า", "304", "Polished (ขัดเงา)", f"{size}, wall {th}mm x 6m",
                                     {"size_inch": size, "wallThickness_mm": float(th)}, "เส้น (Length/pc)")
        add_price(pid, price, None, eff_date, src)

rect_tube_polished = {
    "13x26": {"1.0": 275, "1.2": 370, "1.5": 450},
    "15x30": {"1.0": 505, "1.5": 725},
    "20x40": {"1.0": 500, "1.2": 605, "1.5": 765},
    "25x50": {"1.5": 905, "2.0": 1225, "3.0": 1985},
    "40x80": {"1.2": 1230, "1.5": 1490, "2.0": 2000, "3.0": 3020},
    "50x100": {"1.2": 1470, "1.5": 1955, "2.0": 2960},
}
for size, th_map in rect_tube_polished.items():
    for th, price in th_map.items():
        pid = get_or_create_product("Rectangular Tube", "ท่อสี่เหลี่ยมกล่อง (ไม่ขีด)", "304", "Polished (ขัดเงา)", f"{size}mm, wall {th}mm x 6m",
                                     {"size_mm": size, "wallThickness_mm": float(th)}, "เส้น (Length/pc)")
        add_price(pid, price, None, eff_date, src)
add_review("Rectangular Tube 15x30mm (polished)", "1.2mm-wall column value looked implausibly lower than the 1.0mm column ('430' vs '505') — omitted, verify manually.")

# =========================================================================
# SCHEDULE PIPE (3 Jul 2026) - grade not printed on page, assumed 304
# =========================================================================
eff_date, src = "2026-07-03", "PDF p.14 (3 Jul 2026)"
sch_pipe = [
    ('1/4"', 13.7, [("10", 1.65, 595), ("40", 2.24, None)]),
    ('3/8"', 17.1, [("10", 1.65, 610), ("40", 2.31, 715)]),
    ('1/2"', 21.34, [("10", 2.11, 635), ("40", 2.77, 815)]),
    ('3/4"', 26.67, [("10", 2.11, 815), ("40", 2.87, 1075)]),
    ('1"', 33.4, [("10", 2.77, 1165), ("40", 3.38, 1410)]),
    ('1-1/4"', 42.18, [("10", 2.77, 1485), ("40", 3.56, 1880)]),
    ('1-1/2"', 48.26, [("10", 2.77, 1730), ("40", 3.68, 2250)]),
    ('2"', 60.33, [("10", 2.77, 2160), ("40", 3.91, 2995)]),
    ('2-1/2"', 73.03, [("10", 3.05, 2890), ("40", 5.16, 4710)]),
    ('3"', 88.9, [("10", 3.05, 3520), ("40", 5.49, 6205)]),
    ('4"', 114.3, [("10", 3.05, 4550), ("40", 6.02, 8935)]),
    ('5"', 141.3, [("10", 3.4, 6410), ("40", 6.55, 12305)]),
    ('6"', 168.28, [("10", 3.4, 7480), ("40", 7.11, 16370)]),
    ('8"', 219.08, [("10", 3.76, 11020), ("40", 8.18, 30630)]),
    ('10"', 273.05, [("10", 4.19, 15915), ("40", 9.27, 40935)]),
    ('12"', 323.85, [("10", 4.57, 20345), ("40", 9.52, 49335)]),
]
for size_in, od, schs in sch_pipe:
    for sch, wt, price in schs:
        if price is None:
            continue
        dim_label = f'{size_in} NB, OD {od}mm, SCH {sch}, wall {wt}mm'
        pid = get_or_create_product("Schedule Pipe", "ท่ออุตสาหกรรม (SCH)", "304 (unconfirmed)", "-", dim_label,
                                     {"size_inch": size_in, "od_mm": od, "schedule": sch, "wallThickness_mm": wt}, "เส้น (Length/pc)",
                                     needs_review=True, review_note="Grade (304) not explicitly printed on this page; inferred from surrounding pages. Verify.")
        add_price(pid, price, None, eff_date, src, needs_review=True)
# extra 2-1/2" 76.3mm OD variant
pid = get_or_create_product("Schedule Pipe", "ท่ออุตสาหกรรม (SCH)", "304 (unconfirmed)", "-", '2-1/2" NB, OD 76.3mm, wall 3.00mm',
                             {"size_inch": '2-1/2"', "od_mm": 76.3, "wallThickness_mm": 3.00}, "เส้น (Length/pc)",
                             needs_review=True, review_note="Grade not explicitly printed on this page; verify.")
add_price(pid, 4750, None, eff_date, src, needs_review=True)

# =========================================================================
# ROUND BAR / SHAFT (เพลา)
# =========================================================================
# Page 15: 19 Jul 2023 - heavy illegible handwritten corrections -> flag whole set
eff_date, src = "2023-07-19", "PDF p.15 (19 Jul 2023)"
bar304_2023 = {
    '1/8"': (3.18, 0.38, 62), '3/16"': (4.76, 0.85, 90), '1/4"': (6.35, 1.51, 160),
    '5/16"': (7.95, 2.36, 250), '3/8"': (9.52, 3.38, 355), '7/16"': (11.13, 4.56, 515),
    '1/2"': (12.7, 6.04, 635), '5/8"': (15.88, 9.42, 985), '3/4"': (19.05, 13.55, 1420),
    '7/8"': (22.23, 18.45, 2090), '1"': (25.41, 24.11, 2730), '1-1/8"': (28.58, 30.51, 3115),
    '1-1/4"': (31.75, 37.66, 3845), '1-3/8"': (34.92, 45.52, 4645), '1-1/2"': (38.10, 54.22, 5700),
    '1-5/8"': (41.28, 63.84, 6510), '1-3/4"': (44.45, 73.80, 7530), '2"': (50.80, 96.40, 9840),
    '2-1/8"': (53.98, 96.40, 11135), '2-1/4"': (57.15, 121.99, 12450), '2-3/8"': (60.30, 136.23, 13900),
    '2-1/2"': (63.50, 150.60, 15360), '2-3/4"': (69.80, 183.67, 18740), '3"': (76.20, 216.87, 22120),
    '3-1/8"': (79.38, 236.07, 24100), '3-1/4"': (82.55, 255.00, 26000), '3-1/2"': (88.90, 296.09, 30200),
    '3-3/4"': (95.20, 342.00, 34890), '4"': (101.60, 385.55, 39350),
}
for size_in, (mm, wt, price) in bar304_2023.items():
    dim_label = f'{size_in} ({mm}mm) round bar'
    pid = get_or_create_product("Round Bar", "เพลากลม", "304", "-", dim_label,
                                 {"size_inch": size_in, "size_mm": mm, "weightPer6m_kg": wt}, "เส้น (6m Length)",
                                 needs_review=True,
                                 review_note="Page has extensive illegible handwritten discount/markup annotations (dated 2024) layered over the printed 2023 prices. Printed base price kept; verify current pricing.")
    add_price(pid, price, round(price / wt, 2) if wt else None, eff_date, src, needs_review=True, price_per_kg_calculated=True,
              notes="Superseded by 9 Apr 2026 price list below; kept for history per business rule.")
add_review("Round Bar SUS304 (2023 sheet)", "Margin annotations reference later adjustment dates (2/3/67, 26/9/67 = Mar/Sep 2024) with values that are only partially legible ('เกิน 10', 'เกิน 15', etc). These were not converted into price records — flagged for manual review.")

# Page 16: 9 Apr 2026 (mm sizes)
eff_date, src = "2026-04-09", "PDF p.16 (9 Apr 2026)"
bar304_2026 = {
    "3.00": (0.34, 50), "4.00": (0.60, 65), "5.00": (0.93, 100), "6.00": (1.34, 140), "7.00": (1.83, 190),
    "8.00": (2.40, 250), "9.00": (3.03, 320), "10.00": (3.74, 395), "12.00": (5.38, 565), "15.00": (8.45, 885),
    "16.00": (9.56, 1005), "18.00": (12.20, 1280), "20.00": (14.94, 1570), "22.00": (18.20, 1910),
    "25.00": (23.60, 2480), "30.00": (33.86, 3555), "35.00": (46.00, 4830), "40.00": (59.95, 6295),
    "45.00": (76.90, 8075), "50.00": (93.67, 9835), "70.00": (184.30, 19350),
}
for mm, (wt, price) in bar304_2026.items():
    dim_label = f"{mm}mm round bar"
    pid = get_or_create_product("Round Bar", "เพลากลม", "304", "-", dim_label,
                                 {"size_mm": float(mm), "weightPer6m_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2) if wt else None, eff_date, src, price_per_kg_calculated=True)

# Page 17: Square bar & Hex bar, 9 Apr 2026
eff_date, src = "2026-04-09", "PDF p.17 (9 Apr 2026)"
sqbar304 = {
    '3/16"': (1.10, 175), '1/4"': (1.90, 305), '5/16"': (3.00, 480), '3/8"': (4.30, 690), '1/2"': (7.50, 975),
    '5/8"': (12.00, 1560), '3/4"': (17.20, 2235), '7/8"': (23.38, 3040), '1"': (30.45, 3960),
    '1-1/4"': (48.20, 6265), '1-1/2"': (69.71, 9060), '2"': (123.45, 16050), '2-1/2"': (192.50, 25025),
    '3"': (301.50, 39195), '4"': (527.00, 68510),
}
for size_in, (wt, price) in sqbar304.items():
    pid = get_or_create_product("Square Bar", "เพลาสี่เหลี่ยม", "304", "-", f'{size_in} square bar', {"size_inch": size_in, "weightPer6m_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True,
              notes="Source page had a handwritten discount note (partially illegible, possibly a cash-payment discount) — verify.")

hexbar304 = {
    '1/4"': (2.80, 420), '1/2"': (6.70, 1005), '5/8"': (10.40, 1560), '3/4"': (15.00, 1950),
    '7/8"': (20.26, 2635), '1"': (27.00, 3510), '1-1/8"': (33.45, 4350), '1-1/4"': (41.30, 5370),
    '1-3/8"': (50.50, 6565), '1-1/2"': (60.00, 7800), '1-3/4"': (81.50, 10595), '2"': (106.60, 13860),
    '2-1/2"': (166.70, 21670), '3"': (242.00, 31460),
}
for size_in, (wt, price) in hexbar304.items():
    pid = get_or_create_product("Hex Bar", "เพลาหกเหลี่ยม", "304", "-", f'{size_in} hex bar', {"size_inch": size_in, "weightPer6m_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True)

# Page 18: SUS316L round bar, 8 Apr 2026
eff_date, src = "2026-04-08", "PDF p.18 (8 Apr 2026)"
bar316l = {
    '3/16"': (4.76, 0.84, 155), '1/4"': (6.35, 1.51, 280), '5/16"': (7.95, 2.36, 425), '3/8"': (9.52, 3.38, 610),
    '1/2"': (12.7, 6.04, 1085), '5/8"': (15.88, 9.42, 1695), '3/4"': (19.05, 13.55, 2440),
    '1"': (25.41, 24.11, 4340), '1-1/8"': (28.58, 30.51, 5490), '1-1/4"': (31.80, 38.17, 6870),
    '1-1/2"': (38.10, 54.22, 9760), '1-3/4"': (44.45, 75.50, 13590), '2"': (50.8, 97.80, 17605),
    '2-1/2"': (63.5, 153.50, 27630), '3"': (76.2, 221.00, 39780), '3-1/2"': (88.90, 300.00, 54000),
}
for size_in, (mm, wt, price) in bar316l.items():
    pid = get_or_create_product("Round Bar", "เพลากลม", "316L", "-", f'{size_in} ({mm}mm) round bar', {"size_inch": size_in, "size_mm": mm, "weightPer6m_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True)

# =========================================================================
# FLAT BAR (เส้นแบน) SUS304  - 20 Jan 2025, price per length + weight
# =========================================================================
eff_date, src = "2025-01-20", "PDF p.19-20 (20 Jan 2025)"
flat_price = {
    "3.0": {"1/2": 170, "3/4": 215, "1": 280, "1-1/4": 355, "1-1/2": 425, "2": 565, "2-1/2": 710, "3": 850, "4": 1130, "5": 1415, "6": 1700, "8": 2265},
    "4.5": {"1/2": 260, "3/4": 315, "1": 425, "1-1/4": 530, "1-1/2": 635, "2": 850, "2-1/2": 1060, "3": 1275, "4": 1700, "5": 2120, "6": 2545, "8": 3395},
    "6.0": {"3/4": 425, "1": 565, "1-1/4": 705, "1-1/2": 850, "2": 1130, "2-1/2": 1415, "3": 1700, "4": 2260, "5": 2830, "6": 3395, "8": 4525},
    "9.0": {"1": 880, "1-1/4": 1100, "1-1/2": 1320, "2": 1765, "2-1/2": 2200, "3": 2645, "4": 3525, "5": 4410, "6": 5290, "8": 7050},
    "12.0": {"1": 1175, "1-1/4": 1470, "1-1/2": 1760, "2": 2350, "2-1/2": 2940, "3": 3525, "4": 4700, "5": 5880, "6": 7050, "8": 9400},
    "4.0": {"1/2": 230, "3/4": 285, "1": 375, "1-1/4": 470, "1-1/2": 565, "2": 755, "2-1/2": 945, "3": 1130, "4": 1510, "5": 1885, "6": 2260, "8": 3015},
    "5.0": {"1/2": 285, "3/4": 355, "1": 470, "1-1/4": 590, "1-1/2": 705, "2": 945, "2-1/2": 1180, "3": 1415, "4": 1885, "5": 2355, "6": 2830, "8": 3770},
    "8.0": {"1": 785, "1-1/4": 980, "1-1/2": 1175, "2": 1565, "2-1/2": 1960, "3": 2350, "4": 3135, "5": 3915, "6": 4700, "8": 6265},
    "10.0": {"1": 980, "1-1/4": 1225, "1-1/2": 1470, "2": 1960, "2-1/2": 2450, "3": 2940, "4": 3915, "5": 4895, "6": 5875, "8": 7835},
}
flat_weight = {
    "3.0": {"1/2": 1.81, "3/4": 2.72, "1": 3.63, "1-1/4": 4.53, "1-1/2": 5.44, "2": 7.25, "2-1/2": 9.06, "3": 10.88, "4": 14.50, "5": 18.13, "6": 21.75, "8": 29.00},
    "4.5": {"1/2": 2.72, "3/4": 4.08, "1": 5.44, "1-1/4": 6.80, "1-1/2": 8.16, "2": 10.88, "2-1/2": 13.60, "3": 16.32, "4": 21.75, "5": 27.18, "6": 32.63, "8": 43.51},
    "6.0": {"1/2": 3.63, "3/4": 5.44, "1": 7.25, "1-1/4": 9.06, "1-1/2": 10.88, "2": 14.50, "2-1/2": 18.13, "3": 21.75, "4": 29.00, "5": 36.26, "6": 43.51, "8": 58.01},
    "9.0": {"1/2": 5.44, "3/4": 8.16, "1": 10.88, "1-1/4": 13.60, "1-1/2": 16.32, "2": 21.75, "2-1/2": 27.19, "3": 32.63, "4": 43.51, "5": 54.38, "6": 65.26, "8": 87.01},
    "12.0": {"1/2": 7.25, "3/4": 10.88, "1": 14.50, "1-1/4": 18.13, "1-1/2": 21.75, "2": 29.00, "2-1/2": 36.26, "3": 43.51, "4": 58.01, "5": 72.51, "6": 87.01, "8": 116.02},
    "4.0": {"1/2": 2.41, "3/4": 3.62, "1": 4.83, "1-1/4": 6.05, "1-1/2": 7.25, "2": 9.67, "2-1/2": 12.09, "3": 14.50, "4": 19.34, "5": 24.17, "6": 29.00, "8": 38.67},
    "5.0": {"1/2": 3.02, "3/4": 4.52, "1": 6.04, "1-1/4": 7.57, "1-1/2": 9.06, "2": 12.09, "2-1/2": 15.11, "3": 18.13, "4": 24.17, "5": 30.21, "6": 36.26, "8": 48.34},
    "8.0": {"1/2": 4.83, "3/4": 7.23, "1": 9.67, "1-1/4": 12.10, "1-1/2": 14.50, "2": 19.34, "2-1/2": 24.17, "3": 29.00, "4": 38.67, "5": 48.34, "6": 58.01, "8": 77.35},
    "10.0": {"1": 12.09, "1-1/4": 15.13, "1-1/2": 18.13, "2": 24.17, "2-1/2": 30.21, "3": 36.26, "4": 48.34, "5": 60.43, "6": 72.51, "8": 96.68},
}
for th, widths in flat_price.items():
    for w, price in widths.items():
        wt = flat_weight.get(th, {}).get(w)
        ppk = round(price / wt, 2) if wt else None
        pid = get_or_create_product("Flat Bar", "เส้นแบน", "304", "-", f'{th}mm x {w}" x 6m',
                                     {"thickness_mm": float(th), "width_inch": w, "weightPer_kg": wt}, "เส้น (6m Length)")
        add_price(pid, price, ppk, eff_date, src, price_per_kg_calculated=bool(ppk))

flat_hl = {'3/4"x1/8"': 340, '1"x1/8"': 450, '1-1/2"x1/8"': 685, '2"x1/8"': 895}
for size, price in flat_hl.items():
    pid = get_or_create_product("Flat Bar", "เส้นแบน", "304", "HL (Polished)", f"{size} x 6m", {"size": size}, "เส้น (6m Length)")
    add_price(pid, price, None, eff_date, src)

add_review("Door Track (รางประตูสแตนเลส)", "Dimension noted on p.19 (width 55mm, thickness 2.5mm, x6m) but no price was printed. NEEDS REVIEW — no price available.")

# Flat bar imported/cold-rolled (เส้นแบนรีดนอก) - 18 Mar 2025
eff_date, src = "2025-03-18", "PDF p.21 (18 Mar 2025)"
flatnok_price = {
    "1/2": {"2": (3295, False), "3": (5510, True), "4": (8465, False), "6": (16945, True)},
    "5/8": {"1": (2615, False), "1-1/4": (3310, False), "1-1/2": (4040, False), "2": (4195, False),
            "2-1/2": (6680, False), "3": (7920, False), "4": (10590, False), "5": (13720, True), "6": (20330, False)},
    "3/4": {"1": (3130, False), "1-1/4": (3965, False), "1-1/2": (4860, False), "2": (6350, False),
            "2-1/2": (7900, False), "3": (9505, False), "4": (12680, False), "6": (23550, False)},
    "1": {"1-1/2": (6355, False), "2": (8475, False), "3": (12330, False), "4": (16955, False), "5": (21420, False), "6": (31500, False)},
}
flatnok_weight = {
    "1/2": {"1": 15.30, "1-1/4": 19.50, "1-1/2": 23.02, "2": 35.05, "3": 46.05, "4": 61.60, "5": 77.30, "6": 92.50, "8": 122.79},
    "5/8": {"1": 19.30, "1-1/4": 24.06, "1-1/2": 28.82, "2": 38.43, "2-1/2": 47.71, "3": 57.65, "4": 77.35, "5": 96.68, "6": 116.05, "8": 154.69},
    "3/4": {"1": 22.60, "1-1/4": 28.75, "1-1/2": 34.65, "2": 46.20, "2-1/2": 57.30, "3": 68.89, "4": 91.85, "5": 114.81, "6": 138.20, "8": 184.50},
    "1": {"1": 31.20, "1-1/4": 39.10, "1-1/2": 46.05, "2": 61.62, "3": 93.20, "4": 122.79, "5": 153.48, "6": 185.10, "8": 246.50},
}
for th, widths in flatnok_price.items():
    for w, (price, rev) in widths.items():
        wt = flatnok_weight.get(th, {}).get(w)
        ppk = round(price / wt, 2) if wt else None
        pid = get_or_create_product("Flat Bar", "เส้นแบนรีดนอก (Imported)", "304", "-", f'{th}" x {w}" x 6m (รีดนอก)',
                                     {"thickness_inch": th, "width_inch": w, "weightPer_kg": wt}, "เส้น (6m Length)",
                                     needs_review=rev, review_note="Price cell was crossed out / corrected by hand on the source page; value uncertain." if rev else "")
        add_price(pid, price, ppk, eff_date, src, needs_review=rev, price_per_kg_calculated=bool(ppk),
                  notes="Handwritten correction mark on source — verify." if rev else "")

# =========================================================================
# ANGLE BAR (ฉากรีด) SUS304 - 28 Nov 2023 (heavy handwritten corrections)
# =========================================================================
eff_date, src = "2023-11-28", "PDF p.22 (28 Nov 2023)"
angle304 = {
    '3/4"x3/4"': {"1/8": (5.28, 590)},
    '1"x1"': {"1/8": (7.19, 750), "3/16": (10.43, 1070), "1/4": (12.96, 1330)},
    '1-1/4"x1-1/4"': {"1/8": (9.11, 940), "3/16": (13.31, 1365), "1/4": (16.31, 1675)},
    '1-1/2"x1-1/2"': {"1/8": (11.03, 1135), "3/16": (16.19, 1655), "1/4": (21.10, 2135)},
    '2"x2"': {"1/8": (14.87, 1430), "3/16": (21.94, 2160), "1/4": (28.79, 2760)},
    '2-1/4"x2-1/4"': {"1/4": (29.20, 2945)},
    '2-1/2"x2-1/2"': {"3/16": (28.50, 2545), "1/4": (36.45, 3310)},
    '3"x3"': {"3/16": (33.60, 3250), "1/4": (44.13, 3790)},
    '4"x4"': {"1/4": (55.56, 5535), "3/8": (85.14, 9370)},
}
for size, ths in angle304.items():
    for th, (wt, price) in ths.items():
        pid = get_or_create_product("Angle Bar", "ฉากรีด", "304", "-", f'{size}, {th}" thick x 6m',
                                     {"size_inch": size, "thickness_inch": th, "weightPer_kg": wt}, "เส้น (6m Length)",
                                     needs_review=True, review_note="Source page has extensive handwritten discount % annotations per row and some crossed-out/circled price corrections — printed base price kept, verify manually.")
        add_price(pid, price, round(price / wt, 2), eff_date, src, needs_review=True, price_per_kg_calculated=True,
                  notes="Page has heavy handwritten corrections; base printed price used.")
add_review("Angle Bar SUS304 (2023 sheet)", "1-1/2\"x1-1/2\" 1/8\" cell: printed 1,135 with a handwritten '1,250' circled nearby — unclear which is current. 3\"x3\" 1/4\" row has a handwritten note '3/8=5,500' for an additional thickness not in the printed columns. Both flagged for manual review.")

# Angle bar SUS316 - 18 Mar 2025
eff_date, src = "2025-03-18", "PDF p.23 (18 Mar 2025)"
angle316 = {
    '3/4"x3/4"': {"1/8": (5.20, 830)},
    '1"x1"': {"1/8": (7.19, 1150), "3/16": (10.43, 1690), "1/4": (12.96, 2160)},
    '1-1/4"x1-1/4"': {"1/8": (8.90, 1430), "3/16": (13.31, 2100)},
    '1-1/2"x1-1/2"': {"1/8": (11.03, 1840), "3/16": (16.17, 2590), "1/4": (21.30, 3360)},
    '2"x2"': {"1/8": (14.87, 2450), "3/16": (21.70, 3480), "1/4": (28.79, 4460)},
}
for size, ths in angle316.items():
    for th, (wt, price) in ths.items():
        pid = get_or_create_product("Angle Bar", "ฉากรีด", "316", "-", f'{size}, {th}" thick x 6m',
                                     {"size_inch": size, "thickness_inch": th, "weightPer_kg": wt}, "เส้น (6m Length)")
        add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True)

# =========================================================================
# CHANNEL / TRACK (ราง) SUS304 - 18 Mar 2025
# =========================================================================
eff_date, src = "2025-03-18", "PDF p.24 (18 Mar 2025)"
fold_channel = [
    ('1"x2"x3.0mm', 89.6, 12.79, 1215), ('1-1/2"x3"x3.0mm', 140.4, 20.10, 1910),
    ('2"x4"x3.0mm', 180, 26.84, 2550), ('2-1/2"x5"x3.0mm', 242, 34.55, 3285),
    ('3"x6"x3.0mm', 292.80, 41.80, 3970), ('1"x2"x4.5mm', None, 19.17, 1820),
    ('1-1/2"x3"x4.5mm', 134.40, 28.78, 2735), ('2"x4"x4.5mm', 185.20, 39.66, 3770),
    ('3"x6"x4.5mm', 286.80, 61.41, 5840), ('1-1/2"x3"x6.0mm', 128.40, 36.66, 3480),
    ('2"x4"x6.0mm', 179.20, 51.16, 4860), ('3"x6"x6.0mm', 280.80, 80.17, 7615),
]
for size, area_mm, wt, price in fold_channel:
    pid = get_or_create_product("Channel", "รางพับสแตนเลส (Folded)", "304", "-", f"{size} x 6m",
                                 {"size": size, "weightPer_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True)

roll_channel = [
    ("40x80x5.0mm", 36.45, 5470), ("40x80x6.0mm", 43.50, 6525), ("50x100x5.0mm", 47.25, 7100),
    ("50x100x6.0mm", 56.40, 8460), ("65x130x6.0mm", 75.71, 11420), ("75x150x6.0mm", 87.50, 13200),
]
for size, wt, price in roll_channel:
    pid = get_or_create_product("Channel", "รางรีดสแตนเลส (Rolled)", "304", "-", f"{size} x 6m",
                                 {"size": size, "weightPer_kg": wt}, "เส้น (6m Length)")
    add_price(pid, price, round(price / wt, 2), eff_date, src, price_per_kg_calculated=True)

pid = get_or_create_product("Channel", "รางรีดสแตนเลส (Rolled, Japan Import)", "304", "-", "75x150x6.0mm x 6m (JAPAN import)",
                             {"size": "75x150x6.0mm", "origin": "Japan"}, "เส้น (6m Length)")
add_price(pid, 16210, None, eff_date, src, notes="Imported Japan-origin variant, noted separately from standard rolled channel.")

# =========================================================================
# ALUMINUM SHEET  (from "Price list(1).pdf", 4 June 2026)
# =========================================================================
eff_date, src = "2026-06-04", "Price list(1).pdf p.1 (4 Jun 2026)"

alu_a1100_4x8 = {
    "0.30": (2.47, 145, 360), "0.4": (3.33, 141, 470), "0.5": (4.15, 141, 585), "0.6": (5.01, 141, 705),
    "0.7": (5.85, 141, 825), "0.8": (6.60, 141, 930), "0.9": (7.40, 140, 1035), "1.0": (8.30, 140, 1160),
    "1.2": (9.71, 140, 1360), "1.5": (12.27, 140, 1720), "2.0": (16.29, 140, 2280), "2.5": (20.39, 140, 2855),
    "3.0": (23.90, 140, 3345), "4.0": (32.55, 141, 4590), "4.5": (36.25, 141, 5110), "5.0": (40.91, 141, 5770),
    "6.0": (48.67, 141, 6860),
}
for th, (wt, kg_price, sheet_price) in alu_a1100_4x8.items():
    dim_label = f"{th}mm x 4' x 8'"
    pid = get_or_create_product("Aluminum Sheet", "แผ่นอลูมิเนียม", "A-1100 H14", "-", dim_label,
                                 {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8, "weightPerSheet_kg": wt}, "Sheet")
    add_price(pid, sheet_price, kg_price, eff_date, src)

alu_a1100_5x10 = {
    "1.0": (12.80, 140, 1790), "1.2": (14.84, 140, 2080), "1.5": (18.80, 140, 2630), "2.0": (25.64, 140, 3590),
    "3.0": (38.24, 140, 5355), "4.0": (51.16, 141, 7215), "4.5": (56.88, 141, 8020), "5.0": (63.13, 141, 8900),
    "6.0": (75.68, 141, 10670),
}
for th, (wt, kg_price, sheet_price) in alu_a1100_5x10.items():
    dim_label = f"{th}mm x 5' x 10'"
    pid = get_or_create_product("Aluminum Sheet", "แผ่นอลูมิเนียม", "A-1100 H14", "-", dim_label,
                                 {"thickness_mm": float(th), "width_ft": 5, "length_ft": 10, "weightPerSheet_kg": wt}, "Sheet")
    add_price(pid, sheet_price, kg_price, eff_date, src)

alu_a5052_4x8 = {
    "1.0": (8.06, 153, 1235), "1.2": (9.66, 153, 1480), "1.5": (12.07, 153, 1845),
    "2.0": (16.04, 153, 2455), "2.5": (20.90, 153, 3200), "3.0": (24.02, 153, 3675),
}
for th, (wt, kg_price, sheet_price) in alu_a5052_4x8.items():
    dim_label = f"{th}mm x 4' x 8'"
    pid = get_or_create_product("Aluminum Sheet", "แผ่นอลูมิเนียม", "A-5052 H32", "-", dim_label,
                                 {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8, "weightPerSheet_kg": wt}, "Sheet")
    add_price(pid, sheet_price, kg_price, eff_date, src)

# Checker / anti-slip plate ("ลายกันลื่น ตีนเป็ด" - duck-foot tread pattern).
# Size confirmed by customer as 4'x8' (2026-08-08). Alloy grade was still not
# explicitly printed on the source page — assumed A-1100 to match the
# surrounding sheets, kept flagged until confirmed.
alu_checker = {
    "1.20": (10.37, 145, 1505), "1.50": (12.97, 143, 1855), "2.0": (16.80, 141, 2370),
    "3.0": (25.07, 141, 3535), "4.0": (33.41, 141, 4710), "4.5": (37.58, 141, 5300), "6.0": (49.39, 141, 6965),
}
for th, (wt, kg_price, sheet_price) in alu_checker.items():
    dim_label = f"{th}mm x 4' x 8'"
    pid = get_or_create_product("Aluminum Checker Plate", "แผ่นอลูมิเนียมลายกันลื่น (ตีนเป็ด/ตีนไก่)", "A-1100 (assumed)", "ลายกันลื่น ตีนเป็ด (Checker/Tread)", dim_label,
                                 {"thickness_mm": float(th), "width_ft": 4, "length_ft": 8, "weightPerSheet_kg": wt}, "Sheet",
                                 needs_review=True, review_note="Size confirmed as 4'x8' by customer (8 Aug 2026). Alloy grade was not explicitly printed on the source page; still assumed A-1100 to match the surrounding sheets — verify.")
    add_price(pid, sheet_price, kg_price, eff_date, src, needs_review=True, notes="Alloy grade inferred (assumed A-1100), not explicitly printed — verify. Size confirmed 4'x8'.")

add_review("Aluminum Sheet (Price list(1).pdf)", "The source page also includes two small side tables comparing 'นน/แผ่น' (nominal weight) vs 'น้ำหนักจริง' (actual weight) for A-1100 H14 4x8/5x10 and for the checker plate — these contain no separate pricing and were not imported as price records.")

# =========================================================================
# Write output
# =========================================================================
DB = {"products": PRODUCTS, "priceHistory": PRICES, "reviewNotes": REVIEW,
      "meta": {"generatedFrom": "price list (2).pdf", "pageCount": 25}}

with open("data.js", "w", encoding="utf-8") as f:
    f.write("// Auto-generated from the source PDF. Do not hand-edit; see build_db.py\n")
    f.write("const DB = ")
    f.write(json.dumps(DB, ensure_ascii=False, indent=None))
    f.write(";\n")

print("Products:", len(PRODUCTS))
print("Price history records:", len(PRICES))
print("Review notes:", len(REVIEW))
review_prices = [p for p in PRICES if p["needsReview"]]
review_products = [p for p in PRODUCTS if p["needsReview"]]
print("Price records flagged needsReview:", len(review_prices))
print("Products flagged needsReview:", len(review_products))
dates = sorted(set(p["effectiveDate"] for p in PRICES))
print("Date range:", dates[0], "to", dates[-1])
ptypes = sorted(set(p["productType"] for p in PRODUCTS))
print("Product types:", ptypes)
grades = sorted(set(p["grade"] for p in PRODUCTS))
print("Grades:", grades)
surfaces = sorted(set(p["surface"] for p in PRODUCTS))
print("Surfaces:", surfaces)
