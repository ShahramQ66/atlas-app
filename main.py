# -*- coding: utf-8 -*-
import os, json, threading, time
from datetime import datetime
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.text import LabelBase

# ---------- فارسی ----------
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def fa(s):
        if not s: return ""
        out = []
        for line in str(s).split("\n"):
            out.append(get_display(arabic_reshaper.reshape(line)))
        return "\n".join(out)
except Exception:
    def fa(s):
        return "" if s is None else str(s)

# ---------- فونت ----------
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)
FONT_PATH = os.path.join(FONT_DIR, "Vazir.ttf")
FONT_URL = "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@master/fonts/ttf/Vazirmatn-Regular.ttf"

def ensure_font():
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 10000:
        return True
    try:
        r = requests.get(FONT_URL, timeout=20)
        if r.status_code == 200 and len(r.content) > 10000:
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

# ---------- تنظیمات ----------
CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cfg.json")
DEFAULTS = {"token": "", "chat": "", "ins": "11427939669935844"}

def load_cfg():
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k in DEFAULTS:
            d.setdefault(k, DEFAULTS[k])
        return d
    except Exception:
        return dict(DEFAULTS)

def save_cfg(d):
    try:
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass

# ---------- API ----------
BASE = "https://cdn.tsetmc.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
TIMEOUT = 15

def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def fnum(v):
    return "نامشخص" if v is None else f"{v:,.0f}"

def ff(v, d=None):
    try:
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d

def fd(data, keys):
    if isinstance(data, dict):
        for k in keys:
            if isinstance(data.get(k), dict): return data[k]
    return {}

def fl(data, keys):
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for k in keys:
            if isinstance(data.get(k), list): return data[k]
    return []

def fetch_data(ins):
    p = get_json(f"{BASE}/ClosingPrice/GetClosingPriceDaily/{ins}/0")
    n = get_json(f"{BASE}/Fund/GetETFByInsCode/{ins}")
    h = get_json(f"{BASE}/ClosingPrice/GetClosingPriceDailyList/{ins}/0")
    price = fd(p, ["closingPriceDaily", "closingPrice", "data"])
    nav = fd(n, ["etf", "fund", "data"])
    hist = fl(h, ["closingPriceDaily", "closingPriceDailyList", "data"])
    if not price and isinstance(p, list) and p: price = p[0]
    if not nav and isinstance(n, list) and n: nav = n[0]
    if not price: raise ValueError("قیمت خوانده نشد")
    if not nav: raise ValueError("NAV خوانده نشد")
    hist = [x for x in hist if isinstance(x, dict)]
    hist.sort(key=lambda x: str(x.get("dEven", "")), reverse=True)
    return price, nav, hist

def analyze(price, nav, hist):
    lt = ff(price.get("pDrCotVal") or price.get("lastPrice"))
    cl = ff(price.get("pClosing") or price.get("closingPrice"))
    ys = ff(price.get("priceYesterday") or price.get("yesterdayPrice"))
    vol = ff(price.get("qTotTran5J") or price.get("volume"))
    val = ff(price.get("qTotCap") or price.get("value"))
    pd_ = str(price.get("dEven") or "?")
    nr = ff(nav.get("pRedTran") or nav.get("redemptionNAV"))
    ns = ff(nav.get("pSubTran") or nav.get("subscriptionNAV"))
    nd = str(nav.get("deven") or nav.get("dEven") or "?")

    dp = ((cl/ys - 1)*100) if (cl and ys) else None
    pr = ((lt/nr - 1)*100) if (lt and nr) else None

    rows = []
    for r in hist:
        c = ff(r.get("pClosing") or r.get("closingPrice"))
        v = ff(r.get("qTotTran5J") or r.get("volume"))
        if c: rows.append({"d": str(r.get("dEven","")), "c": c, "v": v})
    rows.sort(key=lambda x: x["d"], reverse=True)

    mc = None
    if len(rows) >= 5:
        mc = (rows[0]["c"]/rows[4]["c"] - 1)*100
    avgv = None
    if len(rows) >= 6:
        vs = [x["v"] for x in rows[1:6] if x["v"]]
        if vs: avgv = sum(vs)/len(vs)
    vr = (rows[0]["v"]/avgv*100) if (rows and avgv) else None

    score = 0
    if dp is not None: score += 20 if dp >= 1 else 14 if dp > 0 else 5 if dp > -1 else 0
    if mc is not None: score += 20 if mc >= 2 else 14 if mc > 0 else 6 if mc > -2 else 0
    if pr is not None: score += 35 if pr <= 0 else 30 if pr <= 0.5 else 23 if pr <= 1 else 12 if pr <= 1.5 else 0
    if vr is not None: score += 15 if vr >= 130 else 12 if vr >= 100 else 8 if vr >= 70 else 3
    if pd_ == nd: score += 10

    warns = []
    if pd_ != nd: warns.append("تاریخ قیمت و NAV یکسان نیست.")
    if pr is not None and pr > 1.5: warns.append("حباب نسبت به NAV.")
    if dp is not None and dp < -2: warns.append("افت روزانه بیش از ۲٪.")
    if vr is not None and vr < 50: warns.append("حجم کمتر از نصف میانگین.")

    if pd_ != nd: act = "احتیاط — تاریخ ناهمگون"
    elif pr is not None and pr > 1.5: act = "احتیاط — حباب"
    elif score >= 75: act = "نامزد بررسی خرید"
    elif score >= 60: act = "صبر و بررسی مجدد"
    else: act = "ورود توصیه نمی‌شود"

    return dict(lt=lt, cl=cl, dp=dp, nr=nr, ns=ns, pr=pr, vol=vol, val=val,
                pd=pd_, nd=nd, score=score, act=act, warns=warns, vr=vr)

# ---------- اعلان بله ----------
def send_bale(token, chat, title, msg):
    if not token or not chat: return False
    try:
        r = requests.post(f"https://tapi.bale.ai/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": f"📊 {title}\n\n{msg}"}, timeout=15)
        r.raise_for_status()
        return True
    except Exception:
        return False

# ---------- UI ----------
class AtlasApp(App):
    def build(self):
        self.title = "Atlas Analyzer"
        self.cfg = load_cfg()
        self.last_action = None

        if ensure_font():
            try:
                LabelBase.register(name="Vazir", fn_regular=FONT_PATH)
                self.font = "Vazir"
            except Exception:
                self.font = None
        else:
            self.font = None

        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        # تنظیمات
        root.add_widget(Label(text=fa("Bale Token"), size_hint_y=None, height=30, font_name=self.font))
        self.inp_token = TextInput(text=self.cfg["token"], multiline=False,
                                    size_hint_y=None, height=45)
        root.add_widget(self.inp_token)

        root.add_widget(Label(text=fa("Chat ID"), size_hint_y=None, height=30, font_name=self.font))
        self.inp_chat = TextInput(text=self.cfg["chat"], multiline=False,
                                   size_hint_y=None, height=45)
        root.add_widget(self.inp_chat)

        root.add_widget(Label(text=fa("INS Code"), size_hint_y=None, height=30, font_name=self.font))
        self.inp_ins = TextInput(text=self.cfg["ins"], multiline=False,
                                  size_hint_y=None, height=45)
        root.add_widget(self.inp_ins)

        btn_save = Button(text=fa("ذخیره"), size_hint_y=None, height=45,
                          background_color=(0.2, 0.6, 0.8, 1), font_name=self.font)
        btn_save.bind(on_release=self.save_settings)
        root.add_widget(btn_save)

        # نمایش
        sv = ScrollView()
        self.out = Label(text=fa("آماده. دکمه «تحلیل» را بزن."),
                         size_hint_y=None, halign="right", valign="top",
                         font_name=self.font)
        self.out.bind(texture_size=lambda i, v: setattr(i, "height", v[1] + 20))
        self.out.bind(width=lambda i, v: setattr(i, "text_size", (v - 10, None)))
        sv.add_widget(self.out)
        root.add_widget(sv)

        # دکمه تحلیل
        btn_go = Button(text=fa("تحلیل"), size_hint_y=None, height=60,
                        background_color=(0.2, 0.75, 0.5, 1), font_name=self.font)
        btn_go.bind(on_release=self.run_analysis)
        root.add_widget(btn_go)

        # پایش خودکار هر ۵ دقیقه
        Clock.schedule_interval(lambda dt: self.run_analysis(None, auto=True), 300)

        return root

    def save_settings(self, *a):
        self.cfg["token"] = self.inp_token.text.strip()
        self.cfg["chat"] = self.inp_chat.text.strip()
        self.cfg["ins"] = self.inp_ins.text.strip() or DEFAULTS["ins"]
        save_cfg(self.cfg)
        self.set_out("تنظیمات ذخیره شد.")

    def set_out(self, text):
        Clock.schedule_once(lambda dt: setattr(self.out, "text", fa(text)), 0)

    def run_analysis(self, *a, auto=False):
        threading.Thread(target=self._worker, args=(auto,), daemon=True).start()

    def _worker(self, auto):
        try:
            if not auto:
                self.set_out("در حال دریافت داده...")
            p, n, h = fetch_data(self.cfg["ins"])
            a = analyze(p, n, h)
            txt = (
                f"زمان: {datetime.now():%H:%M:%S}\n"
                f"تاریخ قیمت: {a['pd']} | NAV: {a['nd']}\n"
                f"آخرین معامله: {fnum(a['lt'])}\n"
                f"پایانی: {fnum(a['cl'])}\n"
                f"تغییر روزانه: {a['dp']:+.2f}%\n" if a['dp'] is not None else "تغییر روزانه: ?\n"
            )
            if a['dp'] is None:
                txt = txt.replace("تغییر روزانه: ?\n", "تغییر روزانه: نامشخص\n")
            txt += (
                f"NAV ابطال: {fnum(a['nr'])}\n"
                f"NAV صدور: {fnum(a['ns'])}\n"
            )
            if a['pr'] is not None:
                txt += f"اختلاف با NAV: {a['pr']:+.2f}%\n"
            txt += f"حجم: {fnum(a['vol'])}\n"
            if a['vr'] is not None:
                txt += f"نسبت حجم: {a['vr']:.1f}%\n"
            txt += f"\nامتیاز: {a['score']}/100\nنتیجه: {a['act']}\n"
            if a['warns']:
                txt += "\n" + "\n".join("⚠️ " + w for w in a['warns'])
            self.set_out(txt)

            if a["act"] != self.last_action:
                self.last_action = a["act"]
                msg = f"{a['act']}\nامتیاز: {a['score']}/100\nآخرین معامله: {fnum(a['lt'])}"
                send_bale(self.cfg["token"], self.cfg["chat"], "تحلیل‌گر اطلس", msg)
        except Exception as e:
            self.set_out(f"خطا: {e}")

if __name__ == "__main__":
    AtlasApp().run()
