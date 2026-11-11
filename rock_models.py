"""Bieniawski RMR89 and Barton Q-system calculations.

Educational implementation. Parameters and joint orientation must be determined
from geotechnical mapping and the applicable original rating tables.
"""
from dataclasses import dataclass


# (Mongolian display label, numeric rating)
PERSISTENCE = [
    ("< 1 м", 6), ("1–3 м", 4), ("3–10 м", 2),
    ("10–20 м", 1), ("> 20 м", 0),
]
APERTURE = [
    ("Ангайлтгүй", 6), ("< 0.1 мм", 5), ("0.1–1 мм", 4),
    ("1–5 мм", 1), ("> 5 мм", 0),
]
ROUGHNESS = [
    ("Маш барзгар", 6), ("Барзгар", 5), ("Бага зэрэг барзгар", 3),
    ("Гөлгөр", 1), ("Толигор / халтиргаатай", 0),
]
INFILL = [
    ("Дүүргэгчгүй", 6), ("Хатуу дүүргэгч < 5 мм", 4),
    ("Хатуу дүүргэгч > 5 мм", 2), ("Зөөлөн дүүргэгч < 5 мм", 2),
    ("Зөөлөн дүүргэгч > 5 мм", 0),
]
WEATHERING = [
    ("Өгөршөөгүй", 6), ("Бага өгөршсөн", 5),
    ("Дунд өгөршсөн", 3), ("Их өгөршсөн", 1), ("Бүрэн өгөршсөн", 0),
]
GROUNDWATER = [
    ("Хуурай", 15), ("Чийгтэй", 10), ("Нойтон", 7),
    ("Дусалж байгаа", 4), ("Урсаж байгаа", 0),
]
ORIENTATIONS = [
    "Маш таатай", "Таатай", "Дунд", "Таагүй", "Маш таагүй",
]
ORIENTATION_PENALTIES = {
    "Туннель / далд уурхай": [0, -2, -5, -10, -12],
    "Суурь": [0, -2, -7, -15, -25],
    "Ил уурхайн хажуу / налуу": [0, -5, -25, -50, -60],
}
JN_OPTIONS = [
    ("Цул, ан цав бараг байхгүй (Jn = 0.5)", 0.5),
    ("Цул, цөөн ан цавтай (Jn = 1)", 1.0),
    ("1 ан цавын систем (Jn = 2)", 2.0),
    ("1 систем + санамсаргүй ан цав (Jn = 3)", 3.0),
    ("2 систем (Jn = 4)", 4.0),
    ("2 систем + санамсаргүй ан цав (Jn = 6)", 6.0),
    ("3 систем (Jn = 9)", 9.0),
    ("3 систем + санамсаргүй ан цав (Jn = 12)", 12.0),
    ("4 ба түүнээс олон систем (Jn = 15)", 15.0),
    ("Маш их бутарсан чулуулгийн цул (Jn = 20)", 20.0),
]
JR_OPTIONS = [
    ("Тасалдсан ан цав (Jr = 4)", 4.0),
    ("Барзгар, долгиолог (Jr = 3)", 3.0),
    ("Гөлгөр, долгиолог (Jr = 2)", 2.0),
    ("Толигор, долгиолог (Jr = 1.5)", 1.5),
    ("Барзгар, хавтгай (Jr = 1.5)", 1.5),
    ("Гөлгөр, хавтгай (Jr = 1)", 1.0),
    ("Толигор, хавтгай (Jr = 0.5)", 0.5),
]
JW_OPTIONS = [
    ("Хуурай эсвэл бага урсац (Jw = 1.0)", 1.0),
    ("Усны нөлөө бага (Jw = 0.66)", 0.66),
    ("Усны нөлөө дунд (Jw = 0.5)", 0.5),
    ("Усны нөлөө их (Jw = 0.33)", 0.33),
    ("Усны нөлөө хүчтэй (Jw = 0.2)", 0.2),
    ("Маш хүчтэй (Jw = 0.1)", 0.1),
    ("Онцгой хүчтэй (Jw = 0.05)", 0.05),
]


@dataclass(frozen=True)
class RockInput:
    ucs_mpa: float
    rqd_percent: float
    spacing_m: float
    persistence: int
    aperture: int
    roughness: int
    infill: int
    weathering: int
    groundwater: int
    structure: str
    orientation_index: int
    jn: float
    jr: float
    ja: float
    jw: float
    srf: float


def rating_ucs(ucs: float) -> int:
    if ucs > 250:
        return 15
    if ucs >= 100:
        return 12
    if ucs >= 50:
        return 7
    if ucs >= 25:
        return 4
    if ucs >= 5:
        return 2
    if ucs >= 1:
        return 1
    return 0


def rating_rqd(rqd: float) -> int:
    if rqd >= 90:
        return 20
    if rqd >= 75:
        return 17
    if rqd >= 50:
        return 13
    if rqd >= 25:
        return 8
    return 3


def rating_spacing(spacing_m: float) -> int:
    if spacing_m > 2:
        return 20
    if spacing_m >= 0.6:
        return 15
    if spacing_m >= 0.2:
        return 10
    if spacing_m >= 0.06:
        return 8
    return 5


def rmr_class(score: int) -> tuple[str, str]:
    if score >= 81:
        return "I", "Маш сайн"
    if score >= 61:
        return "II", "Сайн"
    if score >= 41:
        return "III", "Дунд"
    if score >= 21:
        return "IV", "Муу"
    return "V", "Маш муу"


def q_class(q: float) -> str:
    if q < 0.001:
        return "Онцгой муу (0.001-ээс доош)"
    if q < 0.01:
        return "Онцгой муу"
    if q < 0.1:
        return "Туйлын муу"
    if q < 1:
        return "Маш муу"
    if q < 4:
        return "Муу"
    if q < 10:
        return "Дунд"
    if q < 40:
        return "Сайн"
    if q < 100:
        return "Маш сайн"
    if q < 400:
        return "Туйлын сайн"
    if q <= 1000:
        return "Онцгой сайн"
    return "Онцгой сайн (1000-аас дээш)"


def calculate(values: RockInput) -> dict:
    """Calculate rating breakdown, RMR89 and Q.

    The 10% minimum RQD convention is used for Barton Q only.
    """
    if not (0 <= values.rqd_percent <= 100):
        raise ValueError("RQD нь 0–100% байх ёстой.")
    if values.ucs_mpa < 0 or values.spacing_m < 0:
        raise ValueError("UCS болон ан цавын зай сөрөг байж болохгүй.")
    if values.structure not in ORIENTATION_PENALTIES:
        raise ValueError("Хэрэглээний төрөл буруу.")
    if not (0 <= values.orientation_index < 5):
        raise ValueError("Чиглэлийн ангилал буруу.")
    if values.jn <= 0 or values.jr <= 0 or values.ja <= 0 or values.jw <= 0 or values.srf <= 0:
        raise ValueError("Q-system-ийн бүх коэффициент 0-ээс их байх ёстой.")

    rmr_parts = {
        "UCS": rating_ucs(values.ucs_mpa),
        "RQD": rating_rqd(values.rqd_percent),
        "Ан цавын зай": rating_spacing(values.spacing_m),
        "Ан цавын төлөв": (
            values.persistence + values.aperture + values.roughness
            + values.infill + values.weathering
        ),
        "Усжилт": values.groundwater,
    }
    basic = sum(rmr_parts.values())
    orientation = ORIENTATION_PENALTIES[values.structure][values.orientation_index]
    rmr = basic + orientation
    rmr_group, rmr_name = rmr_class(rmr)

    # Barton (2002) nominal minimum RQD of 10 where measured RQD <= 10.
    effective_rqd = max(10.0, values.rqd_percent)
    block = effective_rqd / values.jn
    shear = values.jr / values.ja
    stress = values.jw / values.srf
    q = block * shear * stress

    return {
        "rmr_basic": basic,
        "rmr_orientation": orientation,
        "rmr": rmr,
        "rmr_class": rmr_group,
        "rmr_quality": rmr_name,
        "rmr_parts": rmr_parts,
        "q_rqd": effective_rqd,
        "q": q,
        "q_quality": q_class(q),
        "q_block": block,
        "q_shear": shear,
        "q_stress": stress,
    }
