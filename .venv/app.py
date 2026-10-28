import math
import re
from decimal import ROUND_HALF_EVEN, Decimal

from flask import Flask, render_template, request

app = Flask(__name__)

SHOP = {"name": "Cafe Bao Tram",
        "address": "12 Lê Lợi, Huế",
        "phone": "0234 3888 999"}
MENU = [
    {"id": 1, "name": "Cà phê đen", "price": 20000, "image": "ca-phe-den.jpg"},
    {"id": 2, "name": "Bạc xỉu", "price": 30000, "image": "bac-xiu.jpg"},
    {"id": 3, "name": "Cà phê sữa", "price": 25000, "image": "ca-phe-sua.jpg"},
    {"id": 4, "name": "Cappuccino", "price": 40000, "image": "cappuccino.jpg"},
    {"id": 5, "name": "Trà đào", "price": 35000, "image": "tra-dao.jpg"},
    {"id": 6, "name": "Trà chanh", "price": 25000, "image": "tra-chanh.jpg"},
    {"id": 7, "name": "Sinh tố bơ", "price": 45000, "image": "sinh-to-bo.jpg"},
]

# Bài 1: máy tính cơ bản
OPERATIONS = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
}
NUMBER_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)")


def parse_number(raw):
    """Đổi chuỗi người dùng nhập thành số; chấp nhận dấu phẩy thập phân (2,5).
    Trả về None nếu không hợp lệ (rỗng, chữ, nan, inf...)."""
    text = raw.strip().replace(",", ".")
    if not NUMBER_RE.fullmatch(text):
        return None
    return float(text)


def fmt(value):
    """8.0 -> '8', 3.5 -> '3.5', -2.5 -> '-2.5'."""
    if value == int(value):
        return str(int(value))
    return repr(round(value, 10))


# Bài 2: tính điểm học phần
SCORE_FIELDS = [
    {"key": "cc", "label": "CC", "title": "Chuyên cần (10%)", "weight": Decimal("0.1")},
    {"key": "gk", "label": "GK", "title": "Giữa kỳ (30%)", "weight": Decimal("0.3")},
    {"key": "ck", "label": "CK", "title": "Cuối kỳ (60%)", "weight": Decimal("0.6")},
]


def check_number(raw, label, low, high, noun="Giá trị"):
    """Hàm kiểm tra dùng chung (Bài 2 và Bài 3): nhập số, chấp nhận dấu phẩy,
    nằm trong [low, high]. Trả về (số, None) hoặc (None, thông báo lỗi)."""
    text = raw.strip().replace(",", ".")
    if not NUMBER_RE.fullmatch(text):
        return None, f"Lỗi ô {label}: Vui lòng nhập một số."
    value = Decimal(text)
    if not low <= value <= high:
        return None, f"Lỗi ô {label}: {noun} phải từ {low} đến {high}."
    return value, None


def check_score(raw, label):
    """Bài 2: điểm từ 0 đến 10 (dùng chung cho cả 3 ô)."""
    return check_number(raw, label, 0, 10, "Điểm")


def letter_grade(total, final_exam):
    if final_exam < 1:  # điểm liệt
        return "F"
    if total >= Decimal("8.5"):
        return "A"
    if total >= Decimal("7.0"):
        return "B"
    if total >= Decimal("5.5"):
        return "C"
    if total >= Decimal("4.0"):
        return "D"
    return "F"


# Bài 3: chỉ số BMI
BMI_FIELDS = [
    {"key": "height", "label": "chiều cao", "title": "Chiều cao (cm)", "low": 50, "high": 250},
    {"key": "weight", "label": "cân nặng", "title": "Cân nặng (kg)", "low": 10, "high": 300},
]


def bmi_category(value):
    """Phân loại theo chuẩn người châu Á. Trả về (tên nhóm, màu)."""
    if value < Decimal("18.5"):
        return "Thiếu cân", "warn"
    if value < 23:
        return "Bình thường", "ok"
    if value < 25:
        return "Thừa cân", "warn"
    return "Béo phì", "danger"


@app.template_filter("vnd")
def vnd(value):
    return f"{value:,.0f}".replace(",", ".") + " đ"


@app.context_processor
def inject_shop():
    # shop dùng được ở mọi template (kể cả base.html và 404.html)
    return {"shop": SHOP}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/menu")
def menu():
    return render_template("menu.html", menu=MENU)


@app.get("/contact")
def contact():
    return render_template("contact.html")


@app.route("/calc", methods=["GET", "POST"])
def calc():
    a, op, b = "", "+", ""
    errors = {}
    result = None

    if request.method == "POST":
        a = request.form.get("a", "")
        op = request.form.get("op", "")
        b = request.form.get("b", "")

        x = parse_number(a)
        y = parse_number(b)

        if x is None:
            errors["a"] = "Lỗi ô a: Vui lòng nhập một số."
        if y is None:
            errors["b"] = "Lỗi ô b: Vui lòng nhập một số."
        if op not in OPERATIONS:
            errors["op"] = "Lỗi: Phép toán không hợp lệ."

        if not errors and op == "/" and y == 0:
            errors["b"] = "Lỗi ô b: Không thể chia cho 0."

        if not errors:
            z = OPERATIONS[op](x, y)
            if math.isfinite(z):
                result = f"{fmt(x)} {op} {fmt(y)} = {fmt(z)}"
            else:
                errors["form"] = "Lỗi: Kết quả quá lớn."

    return render_template("calc.html", a=a, op=op, b=b,
                           errors=errors, result=result)


@app.route("/grade", methods=["GET", "POST"])
def grade():
    values = {f["key"]: "" for f in SCORE_FIELDS}
    errors = {}
    result = None

    if request.method == "POST":
        scores = {}
        for f in SCORE_FIELDS:
            values[f["key"]] = request.form.get(f["key"], "")
            scores[f["key"]], error = check_score(values[f["key"]], f["label"])
            if error:
                errors[f["key"]] = error

        if not errors:
            total = sum(scores[f["key"]] * f["weight"] for f in SCORE_FIELDS)
            total = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN)
            result = {
                "score": str(total),
                "letter": letter_grade(total, scores["ck"]),
                "failed_final": scores["ck"] < 1,
            }

    return render_template("grade.html", fields=SCORE_FIELDS, values=values,
                           errors=errors, result=result)


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    values = {f["key"]: "" for f in BMI_FIELDS}
    errors = {}
    result = None

    if request.method == "POST":
        numbers = {}
        for f in BMI_FIELDS:
            values[f["key"]] = request.form.get(f["key"], "")
            numbers[f["key"]], error = check_number(
                values[f["key"]], f["label"], f["low"], f["high"])
            if error:
                errors[f["key"]] = error

        if not errors:
            tenth = Decimal("0.1")
            height_m_sq = (numbers["height"] / 100) ** 2
            index = (numbers["weight"] / height_m_sq).quantize(tenth, rounding=ROUND_HALF_EVEN)
            category, tone = bmi_category(index)
            result = {
                "index": str(index),
                "category": category,
                "tone": tone,
                # cân nặng ứng với BMI 18,5 – 22,9
                "low": str((Decimal("18.5") * height_m_sq).quantize(tenth, rounding=ROUND_HALF_EVEN)),
                "high": str((Decimal("22.9") * height_m_sq).quantize(tenth, rounding=ROUND_HALF_EVEN)),
            }

    return render_template("bmi.html", fields=BMI_FIELDS, values=values,
                           errors=errors, result=result)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)