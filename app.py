import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from pathlib import Path
import re
import base64

# Plotly — requerido para gráficos. Si falta: pip install plotly
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(
    page_title="CLUB A. UNIÓN | Rendimiento Físico",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# RUTAS DE IMÁGENES
# ==========================================================
ASSETS_DIR = Path("assets")
ESCUDO_PATH = ASSETS_DIR / "escudo_union.png"
JUGADORES_DIR = ASSETS_DIR / "jugadores"

# ==========================================================
# USUARIOS — desde variables de entorno (seguro para producción)
# En Render: Settings → Environment → Add variables
# PWD_DIRECTOR, PWD_SECRETARIO, PWD_SCOUTING, PWD_ADMIN
# Si no están definidas, usa los valores por defecto (solo para desarrollo local)
# ==========================================================
import os

def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)

USUARIOS = {
    "DIRECTOR DEPORTIVO": _env("PWD_DIRECTOR",  "union123"),
    "SECRETARIO TECNICO": _env("PWD_SECRETARIO", "union123"),
    "JEFE SCOUTING":      _env("PWD_SCOUTING",   "union123"),
    "ADMINISTRADOR":      _env("PWD_ADMIN",       "admin123"),
}

# ==========================================================
# GOOGLE SHEETS
# ==========================================================
SHEETS = {
    "gps": "https://docs.google.com/spreadsheets/d/1W3hUX8zTPYXzDUSmdW7Nj2fXbEKlp1E2Us7kwNBhR6c/edit?gid=0",
    "lesiones": "https://docs.google.com/spreadsheets/d/1irSkXB8V_D_jZurEGUA9JMkLpE3e0_qad16_orjHDi8/edit?gid=0",
    "cmj": "https://docs.google.com/spreadsheets/d/1VQLX1R1M0IW8j_TPXbVE8y5qaOA8-2qpj8cL-eGA1VY/edit?gid=1188054203",
    "nordico": "https://docs.google.com/spreadsheets/d/1fhFajl9ckPYikfIKdBHTORcqQj0802JoNQ8-B3wEJWU/edit?gid=1994839095",
    "data_jug": "https://docs.google.com/spreadsheets/d/1aZ7yXUf3M4NA-7lNp9vlwUU_4tgU7Tecf5w-TrnelY8/edit?gid=0"
}

# ==========================================================
# CSS
# ==========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Zoom 90% solo en el contenido principal, no en sidebar ── */
.main .block-container {
    zoom: 0.90;
}


/* ── FIX: franja superior roja con nombre ── */
header[data-testid="stHeader"] {
    background: linear-gradient(90deg, #1e3a8a 0%, #1e3a8a 100%) !important;
    border-bottom: 2px solid rgba(255,255,255,0.15) !important;
}
header[data-testid="stHeader"]::after {
    content: 'TABLERO RESUMEN INDIVIDUAL';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Bebas Neue', sans-serif;
    font-size: 20px;
    letter-spacing: 8px;
    color: #ffffff;
    pointer-events: none;
}

.stApp {
    background: radial-gradient(circle at top left, rgba(37,99,235,.14), transparent 26%),
                linear-gradient(135deg, #07101f 0%, #0d1a2e 50%, #07101f 100%);
    color: #e8ecf4;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
}

section[data-testid="stSidebar"] {
    background: #081426;
    border-right: 1px solid rgba(255,255,255,0.10);
}

section[data-testid="stSidebar"] * {
    color: #e8ecf4 !important;
}

/* ── Escudo en sidebar ── */
.sidebar-escudo {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 18px 0 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 14px;
}
.sidebar-escudo img {
    width: 72px;
    height: 72px;
    object-fit: contain;
    filter: drop-shadow(0 0 12px rgba(37,99,235,.35));
}
.sidebar-club-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 18px;
    letter-spacing: 3px;
    color: #ffffff !important;
    margin-top: 6px;
}

.stSelectbox label, .stTextInput label, .stNumberInput label {
    color: #cbd5e1 !important;
    font-weight: 700 !important;
}

/* ── Selects / inputs visibles en sidebar y main ── */
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(37,99,235,0.45) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div {
    color: #ffffff !important;
    font-weight: 600 !important;
}
/* Dropdown lista */
[data-baseweb="popover"] ul li {
    background: #0d1a2e !important;
    color: #e8ecf4 !important;
}
[data-baseweb="popover"] ul li:hover {
    background: rgba(37,99,235,.25) !important;
    color: #ffffff !important;
}
/* NumberInput */
.stNumberInput input {
    background: #ffffff !important;
    border: 1px solid rgba(37,99,235,0.55) !important;
    border-radius: 10px !important;
    color: #111827 !important;
    font-weight: 800 !important;
    font-size: 16px !important;
}
.stNumberInput > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(37,99,235,0.45) !important;
    border-radius: 10px !important;
}
/* Botones +/- del NumberInput */
.stNumberInput button {
    background: rgba(37,99,235,0.25) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 900 !important;
}

.stButton button, .stDownloadButton button {
    background: linear-gradient(135deg, #2563eb, #1e40af) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
}

.login-card {
    max-width: 500px;
    margin: 42px auto 0 auto;
    padding: 34px;
    border-radius: 26px;
    text-align: center;
    background: rgba(13, 26, 46, 0.96);
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 20px 70px rgba(0,0,0,0.42);
}

.login-logo {
    width: 150px;
    max-height: 150px;
    object-fit: contain;
    margin-bottom: 14px;
    filter: drop-shadow(0 0 24px rgba(37,99,235,.30));
}

.club-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 42px;
    letter-spacing: 4px;
    color: #ffffff;
    line-height: 1;
}

.club-subtitle {
    color: #38bdf8;
    font-size: 16px;
    margin-top: 8px;
    font-weight: 600;
}

.player-header {
    display: grid;
    grid-template-columns: 120px 1fr 240px 155px;
    gap: 16px;
    align-items: center;
    padding: 18px 20px;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(13,26,46,.98), rgba(17,28,53,.95));
    border: 1px solid rgba(255,255,255,0.11);
    margin-bottom: 20px;
    box-shadow: 0 14px 38px rgba(0,0,0,.26);
}

.campo-col {
    display: flex;
    align-items: center;
    justify-content: center;
}
.campo-col svg {
    filter: drop-shadow(0 0 8px rgba(37,99,235,.20));
    border-radius: 8px;
}

.escudo-header-col {
    display: flex;
    align-items: center;
    justify-content: center;
}
.escudo-header-col img {
    width: 143px;
    height: 143px;
    object-fit: contain;
    filter: drop-shadow(0 0 10px rgba(37,99,235,.30));
}

.player-photo {
    width: 118px;
    height: 118px;
    border-radius: 24px;
    object-fit: cover;
    border: 2px solid rgba(37,99,235,.55);
    background: #111827;
    box-shadow: 0 0 32px rgba(37,99,235,.18);
}

.player-avatar-fallback {
    width: 118px;
    height: 118px;
    border-radius: 24px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:48px;
    border: 2px solid rgba(37,99,235,.55);
    background: linear-gradient(135deg, #111827, #1f2937);
}

.player-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 54px;
    letter-spacing: 2px;
    color: white;
    line-height: .95;
    margin-bottom: 6px;
}

.player-sub {
    color: #3b82f6;
    letter-spacing: 3px;
    font-size: 13px;
    text-transform: uppercase;
    font-weight: 900;
    margin-bottom: 8px;
}

.info-chip {
    display: inline-block;
    padding: 6px 11px;
    margin: 4px 5px 0 0;
    border-radius: 999px;
    background: rgba(255,255,255,0.070);
    border: 1px solid rgba(255,255,255,0.12);
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 700;
}

/* ── PIE ACTIVO / INACTIVO ── */
.boot-box {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 14px;
    margin-right: 10px;
    margin-top: 10px;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.025);
    color: rgba(255,255,255,0.18);
    font-weight: 800;
    font-size: 13px;
    transition: all .2s;
}

/* Pie dominante → rojo brillante */
.boot-active {
    background: linear-gradient(135deg, rgba(37,99,235,.50), rgba(30,64,175,.35));
    border: 2px solid #2563eb;
    color: #ffffff;
    box-shadow: 0 0 20px rgba(37,99,235,.45), inset 0 0 10px rgba(37,99,235,.15);
    text-shadow: 0 0 8px rgba(255,255,255,.4);
}
.boot-active::before {
    content: '●';
    color: #10f2a0;
    font-size: 8px;
    vertical-align: middle;
}

/* ── MINI CARD para evaluaciones (6 en fila) ── */
.mini-eval-card {
    position: relative;
    overflow: hidden;
    padding: 12px 14px;
    border-radius: 14px;
    background: linear-gradient(145deg, rgba(13,26,46,.98), rgba(17,28,53,.92));
    border: 1px solid rgba(255,255,255,0.09);
    box-shadow: 0 4px 14px rgba(0,0,0,.20);
}
.mini-eval-card::after {
    content: '';
    position: absolute;
    right: -18px; top: -18px;
    width: 54px; height: 54px;
    border-radius: 50%;
    background: rgba(37,99,235,.08);
}
.mini-eval-icon { font-size: 22px; margin-bottom: 3px; }
.mini-eval-label {
    font-size: 9px;
    color: #93c5fd;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    font-weight: 900;
    margin-bottom: 4px;
}
.mini-eval-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 26px;
    color: #ffffff;
    line-height: 1;
    letter-spacing: .5px;
}
.mini-eval-sub { font-size: 10px; color: #64748b; margin-top: 2px; font-weight: 600; }

/* highlight izq/der en mini cards */
.mini-eval-card.izq-dom { border-color: rgba(37,99,235,.55); box-shadow: 0 0 12px rgba(37,99,235,.18); }
.mini-eval-card.der-dom { border-color: rgba(37,99,235,.55); box-shadow: 0 0 12px rgba(37,99,235,.18); }
.mini-eval-card.lado-sec { border-color: rgba(255,255,255,0.05); opacity: .55; }

/* ── METRIC CARDS GPS — mismo tamaño que mini-eval ── */
.metric-card {
    position: relative;
    overflow: hidden;
    padding: 12px 14px;
    border-radius: 14px;
    background: linear-gradient(145deg, rgba(13,26,46,.98), rgba(17,28,53,.92));
    border: 1px solid rgba(255,255,255,0.09);
    box-shadow: 0 4px 14px rgba(0,0,0,.20);
}

.metric-card::after {
    content: '';
    position: absolute;
    right: -18px; top: -18px;
    width: 54px; height: 54px;
    border-radius: 50%;
    background: rgba(37,99,235,.08);
}

.metric-icon { font-size: 22px; margin-bottom: 3px; }

.metric-title {
    font-size: 9px;
    color: #93c5fd;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 4px;
    font-weight: 900;
}

.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 26px;
    color: #ffffff;
    line-height: 1;
    letter-spacing: .5px;
}

.metric-sub {
    font-size: 10px;
    color: #64748b;
    margin-top: 3px;
    font-weight: 600;
}

.delta-pos { color: #10f2a0; font-weight: 900; font-size: 10px; }
.delta-neg { color: #ff9f43; font-weight: 900; font-size: 10px; }
.delta-neu { color: #94a3b8; font-weight: 900; font-size: 10px; }

.section-title {
    color: #ffffff;
    font-size: 18px;
    font-weight: 950;
    margin: 28px 0 12px 0;
    letter-spacing: -.2px;
    border-left: 4px solid #2563eb;
    padding-left: 10px;
}

.kpi-box {
    background: linear-gradient(145deg, rgba(13,26,46,.98), rgba(17,28,53,.92));
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 18px;
    padding: 14px;
    min-height: 90px;
}

.kpi-label {
    font-size: 11px;
    color: #93c5fd;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.kpi-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 34px;
    color: #ffffff;
    margin-top: 6px;
}

.small-text {
    color:#cbd5e1;
    font-size:13px;
    font-weight:600;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(13,26,46,.98), rgba(17,28,53,.92));
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 18px;
    padding: 14px;
}

[data-testid="stMetricLabel"] p {
    color: #93c5fd !important;
    font-weight: 900 !important;
    font-size: 12px !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 22px !important;
}

/* ── LESION compacta ── */
.lesion-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 12px;
    background: rgba(37,99,235,.12);
    border: 1px solid rgba(37,99,235,.30);
    color: #fca5a5;
    font-size: 13px;
    font-weight: 700;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.stDataFrame {
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 14px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# HELPERS IMÁGENES
# ==========================================================
def img_to_base64(path: Path):
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()


def html_img(path: Path, css_class: str, fallback: str = "🛡️"):
    b64 = img_to_base64(path)
    if b64:
        ext = path.suffix.lower().replace(".", "") or "png"
        return f'<img src="data:image/{ext};base64,{b64}" class="{css_class}">'
    return f'<div class="player-avatar-fallback">{fallback}</div>'


@st.cache_data(ttl=86400)  # Cache 24hs
def buscar_foto_web(nombre_jugador: str) -> str | None:
    """
    Busca foto del jugador en Wikipedia API.
    Retorna URL de la imagen o None si no encuentra.
    """
    import urllib.request, json, urllib.parse
    # Normalizar nombre: "Del Blanco M" → "Del Blanco" (sin inicial)
    partes = nombre_jugador.strip().split()
    # Intentar con nombre completo y sin la inicial al final
    variantes = [
        nombre_jugador,
        " ".join(partes[:-1]) if len(partes) > 1 else nombre_jugador,
        " ".join(reversed(partes[:-1])) if len(partes) > 1 else nombre_jugador,
    ]
    for variante in variantes:
        try:
            query = urllib.parse.quote(f"{variante} futbolista Argentina")
            url = (f"https://en.wikipedia.org/w/api.php?"
                   f"action=query&titles={query}&prop=pageimages&format=json"
                   f"&pithumbsize=200&redirects=1")
            req = urllib.request.Request(url, headers={"User-Agent": "UnionDashboard/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb
        except Exception:
            continue
    return None


def buscar_foto_jugador(nombre: str):
    """Busca foto local en assets/jugadores/ con matching flexible."""
    if not JUGADORES_DIR.exists():
        return None
    # 1. Exacto: "Profini R.png"
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        p = JUGADORES_DIR / f"{nombre}{ext}"
        if p.exists():
            return p
    # 2. Case-insensitive
    nombre_lower = nombre.lower().strip()
    for f in JUGADORES_DIR.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            if f.stem.lower().strip() == nombre_lower:
                return f
    # 3. Apellido solo (por si el nombre en GPS tiene formato diferente)
    apellido = nombre.split()[0].lower() if nombre.split() else ""
    for f in JUGADORES_DIR.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            if f.stem.lower().startswith(apellido) and len(apellido) >= 3:
                return f
    return None

# ==========================================================
# GOOGLE SHEETS
# ==========================================================
def gsheet_to_csv(url: str) -> str:
    sheet_id = re.search(r"/d/([^/]+)", url).group(1)
    gid_match = re.search(r"gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def rename_any(df: pd.DataFrame, candidatos: list, final: str) -> pd.DataFrame:
    df = df.copy()
    lower = {c.lower().strip(): c for c in df.columns}
    for cand in candidatos:
        key = cand.lower().strip()
        if key in lower and lower[key] != final:
            return df.rename(columns={lower[key]: final})
    return df


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_columnas(df)
    df = rename_any(df, ["JUGADOR", "Jugador", "NAME", "Name", "Player", "PLAYER", "Atleta", "ATHLETE"], "JUGADOR")
    df = rename_any(df, ["POSICION", "Posicion", "POSICIÓN", "POS", "Position", "POSITION"], "POSICION")
    df = rename_any(df, ["FECHA", "Fecha", "fecha", "DATE", "Date"], "FECHA")
    df = rename_any(df, ["RIVAL", "Rival", "Opponent", "OPPONENT"], "RIVAL")
    df = rename_any(df, ["MIN", "Min", "Minutes", "MINUTES", "Duration"], "MIN")
    df = rename_any(df, ["DISTANCIA TOTAL", "Distancia Total", "Total Distance", "TOT DIST", "TOT-DIST"], "TOT DIST")
    df = rename_any(df, ["MTS/MIN", "M/MIN", "Meters Per Min", "MTS MIN"], "MTS/MIN")
    df = rename_any(df, ["HSD", ">19", "MTS>19", "MTS >19", "HSR", "High Speed Running",
                          "MTS>19 KM/H", "MTS > 19 KM/H", "MTS>19KM/H",
                          "MTS > 19KM/H", ">19KM/H", ">19 KM/H"], "HSD")
    df = rename_any(df, ["SPD", ">24", "MTS>24", "MTS >24", "SPRINT", "Sprint Distance",
                          "MTS>24 KM/H", "MTS > 24 KM/H", "MTS>24KM/H",
                          "MTS > 24KM/H", ">24KM/H", ">24 KM/H"], "SPD")
    df = rename_any(df, ["SPRINTS", "Sprints", "SPRINT", "N SPRINTS", "N° SPRINTS"], "SPRINTS")
    df = rename_any(df, ["ACEL", "ACC", "ACCEL", "Aceleraciones"], "ACEL")
    df = rename_any(df, ["DES", "DEC", "DECEL", "Desaceleraciones"], "DES")
    df = rename_any(df, ["V-MAX", "VMAX", "MAX SPEED", "Velocidad Maxima", "Velocidad Máxima"], "V-MAX")
    df = rename_any(df, ["SES", "SESION", "SESIÓN", "Session", "SESSION", "Tipo Sesion", "Tipo sesión"], "SESION")
    return df


@st.cache_data(ttl=300)
def cargar_datos():
    gps      = normalizar(pd.read_csv(gsheet_to_csv(SHEETS["gps"]),      low_memory=False))
    lesiones = normalizar(pd.read_csv(gsheet_to_csv(SHEETS["lesiones"]), low_memory=False))
    data_jug = normalizar(pd.read_csv(gsheet_to_csv(SHEETS["data_jug"]), low_memory=False))

    # CMJ: cargar raw, limpiar strings "None"/"nan" → NaN real ANTES de normalizar
    # El separador decimal puede ser COMA (formato europeo/argentino) → reemplazar
    cmj_raw = pd.read_csv(gsheet_to_csv(SHEETS["cmj"]), low_memory=False)
    cmj_raw.columns = cmj_raw.columns.astype(str).str.strip()
    cmj_raw = cmj_raw.replace({"None": pd.NA, "nan": pd.NA, "": pd.NA, "#N/A": pd.NA})
    CMJ_NUM_COLS = [
        "Jump Height (Imp-Mom) [cm]",
        "Eccentric Peak Power / BM [W/kg]",
        "RSI-modified [m/s]",
        "Concentric Mean Force / BM [N/kg]",
        "Concentric Peak Force / BM [N/kg]",
        "BW [KG]", "Reps", "Additional Load [lb]",
    ]
    for c in CMJ_NUM_COLS:
        if c in cmj_raw.columns:
            # Manejar coma como separador decimal (ej: "36,9" → "36.9")
            col_s = cmj_raw[c].astype(str).str.strip()
            col_s = col_s.str.replace(r"^\s*$", "nan", regex=True)
            col_s = col_s.str.replace(",", ".", regex=False)
            cmj_raw[c] = pd.to_numeric(col_s, errors="coerce")
    cmj = normalizar(cmj_raw)

    # NORDICO: mismo tratamiento con comas
    nord_raw = pd.read_csv(gsheet_to_csv(SHEETS["nordico"]), low_memory=False)
    nord_raw.columns = nord_raw.columns.astype(str).str.strip()
    nord_raw = nord_raw.replace({"None": pd.NA, "nan": pd.NA, "": pd.NA, "#N/A": pd.NA})
    NORD_NUM_COLS = ["R Max Force (N)", "L Max Force (N)", "Max Imbalance (%)"]
    for c in NORD_NUM_COLS:
        if c in nord_raw.columns:
            col_s = nord_raw[c].astype(str).str.strip().str.replace(",", ".", regex=False)
            nord_raw[c] = pd.to_numeric(col_s, errors="coerce")
    nordico = normalizar(nord_raw)

    # DATA_JUG: renombrar columnas reales (POS → POSICION, PERFIL → LADO_HABIL)
    data_jug = rename_any(data_jug, ["FECHA_NAC","FECHA NAC","FECHA NACIMIENTO","Nacimiento","Fecha nacimiento"], "FECHA_NAC")
    data_jug = rename_any(data_jug, ["LADO_HABIL","LADO HABIL","PIERNA","Pierna","PERFIL","Perfil","Dominant Foot","Foot"], "LADO_HABIL")
    data_jug = rename_any(data_jug, ["POSICION","POS","Pos","Position","POSITION"], "POSICION")
    data_jug = rename_any(data_jug, ["ALTURA","Height","HEIGHT"], "ALTURA")
    data_jug = rename_any(data_jug, ["NACIONALIDAD","PAIS","País","Country","COUNTRY"], "NACIONALIDAD")
    data_jug = rename_any(data_jug, ["BANDERA","Flag","FLAG","EMOJI"], "BANDERA")
    data_jug = rename_any(data_jug, ["FOTO","FOTO_URL","IMAGEN","Photo","Image","URL_FOTO","FOTO URL"], "FOTO_URL")
    data_jug = rename_any(data_jug, ["CAMPO","CAMPO_URL","CAMPO URL","Field","FIELD","Posicion Imagen","Campo imagen"], "CAMPO")
    # POS_ESP: posición específica para ubicación en campo (incluye lado)
    data_jug = rename_any(data_jug, ["POS ESP","POS_ESP","POSESP","POSICION ESP","POSICION ESPECIFICA"], "POS_ESP")

    for df in [gps, lesiones, cmj, nordico, data_jug]:
        if "FECHA" in df.columns:
            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce", dayfirst=True)
        if "AÑO" not in df.columns and "FECHA" in df.columns:
            df["AÑO"] = df["FECHA"].dt.year

    return gps, lesiones, cmj, nordico, data_jug


try:
    gps, lesiones, cmj, nordico, data_jug = cargar_datos()
except Exception as e:
    st.error("No pude cargar una o más bases. Revisá permisos de Google Sheets: Cualquier persona con el enlace puede ver.")
    st.exception(e)
    st.stop()

# ==========================================================
# VALIDACIONES BÁSICAS
# ==========================================================
def validar(df, cols, nombre):
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        st.error(f"Faltan columnas en {nombre}: {faltan}")
        st.write(f"Columnas disponibles en {nombre}:", list(df.columns))
        st.stop()

validar(gps, ["JUGADOR", "POSICION", "FECHA", "AÑO", "SESION"], "GPS")
validar(data_jug, ["JUGADOR"], "DATA_JUG")
validar(lesiones, ["JUGADOR", "FECHA", "LESION", "REGION", "DAY_OFF_DXT"], "LESIONES")

# ==========================================================
# FUNCIONES
# ==========================================================
def safe_get(row, col, default="Sin dato"):
    if col in row.index and pd.notna(row[col]) and str(row[col]).strip().lower() not in ["", "nan", "nat", "none"]:
        return row[col]
    return default


def num_series(df, col):
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def val_num(df, col, agg="max"):
    s = num_series(df, col).dropna()
    if s.empty:
        return None
    if agg == "mean":
        return s.mean()
    if agg == "sum":
        return s.sum()
    if agg == "min":
        return s.min()
    return s.max()


def edad_desde(fecha):
    f = pd.to_datetime(fecha, errors="coerce", dayfirst=True)
    if pd.isna(f):
        return "Sin dato"
    hoy = date.today()
    return hoy.year - f.year - ((hoy.month, hoy.day) < (f.month, f.day))


def fecha_txt(fecha):
    f = pd.to_datetime(fecha, errors="coerce", dayfirst=True)
    return "Sin dato" if pd.isna(f) else f.strftime("%d/%m/%Y")


def delta(valor, ref):
    if valor is None or ref is None or pd.isna(valor) or pd.isna(ref) or ref == 0:
        return "Sin referencia", "delta-neu"
    d = ((valor - ref) / ref) * 100
    if d > 3:
        return f"+{d:.1f}% vs posición", "delta-pos"
    if d < -3:
        return f"{d:.1f}% vs posición", "delta-neg"
    return f"{d:+.1f}% vs posición", "delta-neu"


def metric_card(icono, titulo, valor, unidad, ref):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        val_txt   = "Sin dato"
        pct_html  = ""
        ref_html  = ""
        icon_bg   = "rgba(255,255,255,0.06)"
    else:
        val_txt = f"{valor:,.0f} {unidad}"
        if ref is not None and not pd.isna(ref) and ref != 0:
            d = ((valor - ref) / ref) * 100
            clr      = "#10f2a0" if d > 3 else ("#ff6b6b" if d < -3 else "#94a3b8")
            signo    = "+" if d > 0 else ""
            icon_bg  = "rgba(16,242,160,0.12)" if d > 3 else ("rgba(255,107,107,0.12)" if d < -3 else "rgba(255,255,255,0.05)")
            pct_html = f'<div style="font-size:13px;font-weight:900;color:{clr};margin-top:4px;">{signo}{d:.1f}% vs posición</div>'
            ref_html = f'<div style="font-size:8px;color:#64748b;font-weight:700;margin-top:2px;letter-spacing:.8px;">PROM: {ref:,.1f} {unidad}</div>'
        else:
            pct_html = '<div style="font-size:8px;color:#475569;margin-top:4px;letter-spacing:1px;">SIN REFERENCIA</div>'
            ref_html  = ""
            icon_bg   = "rgba(255,255,255,0.05)"

    st.markdown(f"""
<div style="position:relative;overflow:hidden;padding:11px 12px;border-radius:16px;
background:linear-gradient(145deg,rgba(13,26,46,.98),rgba(17,28,53,.92));
border:1px solid rgba(255,255,255,0.10);
box-shadow:0 4px 18px rgba(0,0,0,.22);min-height:110px;
display:flex;flex-direction:column;justify-content:space-between;">
  <div style="font-size:7.5px;color:#93c5fd;letter-spacing:1.5px;text-transform:uppercase;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{titulo}</div>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-top:4px;flex:1;">
    <div style="min-width:0;flex:1;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;color:#fff;line-height:1.1;letter-spacing:.3px;word-break:break-word;">{val_txt}</div>
      {pct_html}
      {ref_html}
    </div>
    <div style="display:flex;align-items:center;justify-content:center;
                width:62px;height:62px;border-radius:14px;background:{icon_bg};
                flex-shrink:0;margin-left:6px;">
      <span style="font-size:36px;line-height:1;">{icono}</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


def filtrar_solo_partidos(df):
    ses = df["SESION"].astype(str).str.upper().str.strip()
    mask = ses.str.contains("PARTIDO|MATCH|\\bMD\\b", regex=True, na=False)
    return df[mask].copy()


# ==========================================================
# PDF MEJORADO — exporta todo el reporte con diseño
# ==========================================================
def generar_pdf(jugador, anio, posicion, tabla, les_df, cmj_val, power_val, rsi_val, max_force, imb, ultima_lesion):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable, KeepTogether)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buffer = BytesIO()
    W, H = A4
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm
    )

    ROJO = colors.HexColor("#1e3a8a")
    AZUL = colors.HexColor("#1e3a5f")
    AZUL_CLARO = colors.HexColor("#1e293b")
    GRIS = colors.HexColor("#334155")
    BLANCO = colors.white
    VERDE = colors.HexColor("#10b981")
    GRIS_TEXTO = colors.HexColor("#64748b")

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=22,
                                   textColor=BLANCO, alignment=TA_CENTER, spaceAfter=4,
                                   backColor=ROJO, borderPad=10)
    sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=11,
                                textColor=BLANCO, alignment=TA_CENTER, spaceAfter=2,
                                backColor=AZUL)
    seccion_style = ParagraphStyle("seccion", fontName="Helvetica-Bold", fontSize=13,
                                    textColor=BLANCO, spaceAfter=6, spaceBefore=14,
                                    backColor=AZUL_CLARO, borderPad=6, leftIndent=0)
    normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=9,
                             textColor=colors.HexColor("#1e293b"), spaceAfter=3)
    label_style = ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=GRIS_TEXTO, spaceAfter=1)

    story = []

    # ── ENCABEZADO ──────────────────────────────────────────
    story.append(Paragraph("CLUB A. UNIÓN", titulo_style))
    story.append(Paragraph("Análisis de Rendimiento Físico", sub_style))
    story.append(Spacer(1, 8))

    # Info jugador en tabla de 2 columnas
    info_data = [
        [Paragraph(f"<b>Jugador:</b> {jugador}", normal),
         Paragraph(f"<b>Posición:</b> {posicion}", normal)],
        [Paragraph(f"<b>Año:</b> {anio}", normal),
         Paragraph(f"<b>Generado:</b> {date.today().strftime('%d/%m/%Y')}", normal)],
    ]
    info_t = Table(info_data, colWidths=[(W - 3.6*cm) / 2] * 2)
    info_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, GRIS),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 10))

    # ── ÚLTIMA LESIÓN (compacta) ─────────────────────────────
    story.append(Paragraph("📌 DISPONIBILIDAD", seccion_style))
    lesion_data = [[
        Paragraph(f"<b>Última lesión:</b> {ultima_lesion}", normal),
        Paragraph(f"<b>Días perdidos:</b> {int(les_df['DAY_OFF_DXT'].sum()) if not les_df.empty else 0}", normal),
        Paragraph(f"<b>N° lesiones:</b> {len(les_df)}", normal),
    ]]
    lesion_t = Table(lesion_data, colWidths=[(W - 3.6*cm) / 3] * 3)
    lesion_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
        ("BOX", (0, 0), (-1, -1), 0.5, ROJO),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(lesion_t)
    story.append(Spacer(1, 10))

    # ── EVALUACIONES FÍSICAS ─────────────────────────────────
    story.append(Paragraph("🏋️ EVALUACIONES FÍSICAS", seccion_style))
    def fmtv(v, suf=""):
        return "Sin dato" if v is None or pd.isna(v) else f"{v:.1f}{suf}"

    eval_data = [
        ["CMJ (mejor)", "Peak Power/BM", "Fuerza isquios", "Imbalance"],
        [fmtv(cmj_val, " cm"), fmtv(power_val, " W/kg"),
         fmtv(max_force, " N"), fmtv(imb, " %")],
    ]
    eval_col = (W - 3.6*cm) / 4
    eval_t = Table(eval_data, colWidths=[eval_col] * 4)
    eval_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eff6ff")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.5, AZUL),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bfdbfe")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(eval_t)
    story.append(Spacer(1, 10))

    # ── TABLA PARTIDOS ───────────────────────────────────────
    story.append(Paragraph("⚽ ÚLTIMOS PARTIDOS", seccion_style))
    if not tabla.empty:
        col_w = (W - 3.6*cm) / len(tabla.columns)
        encabezado = [Paragraph(f"<b>{c}</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                      fontSize=7, textColor=BLANCO, alignment=TA_CENTER)
                      ) for c in tabla.columns]
        filas = [encabezado]
        for _, row in tabla.iterrows():
            fila = [Paragraph(str(v), ParagraphStyle("td", fontName="Helvetica",
                    fontSize=8, alignment=TA_CENTER)) for v in row]
            filas.append(fila)
        part_t = Table(filas, colWidths=[col_w] * len(tabla.columns), repeatRows=1)
        part_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ROJO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), BLANCO]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(part_t)
    else:
        story.append(Paragraph("Sin datos de partidos para el período seleccionado.", normal))

    story.append(Spacer(1, 10))

    # ── TABLA LESIONES ───────────────────────────────────────
    if not les_df.empty:
        story.append(Paragraph("🩺 DETALLE DE LESIONES", seccion_style))
        cols_les = [c for c in ["FECHA", "LESION", "REGION", "DAY_OFF_DXT"] if c in les_df.columns]
        les_disp = les_df[cols_les].copy()
        if "FECHA" in les_disp.columns:
            les_disp["FECHA"] = les_disp["FECHA"].dt.strftime("%d/%m/%Y")
        les_cols_w = (W - 3.6*cm) / len(les_disp.columns)
        les_enc = [Paragraph(f"<b>{c}</b>", ParagraphStyle("lth", fontName="Helvetica-Bold",
                   fontSize=7, textColor=BLANCO, alignment=TA_CENTER)) for c in les_disp.columns]
        les_filas = [les_enc]
        for _, row in les_disp.iterrows():
            fila = [Paragraph(str(v), ParagraphStyle("ltd", fontName="Helvetica",
                    fontSize=8, alignment=TA_CENTER)) for v in row]
            les_filas.append(fila)
        les_t = Table(les_filas, colWidths=[les_cols_w] * len(les_disp.columns), repeatRows=1)
        les_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ROJO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff1f2"), BLANCO]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#fecaca")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(les_t)

    # ── FOOTER ──────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=ROJO))
    story.append(Paragraph(
        f"<font color='#64748b' size='7'>Documento generado el {date.today().strftime('%d/%m/%Y')} · CLUB A. UNIÓN · Área de Rendimiento Físico</font>",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=7,
                       textColor=GRIS_TEXTO, alignment=TA_CENTER, spaceBefore=4)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ==========================================================
# LOGIN
# ==========================================================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    escudo_html = ""
    escudo_b64 = img_to_base64(ESCUDO_PATH)
    if escudo_b64:
        escudo_html = f'<img src="data:image/png;base64,{escudo_b64}" class="login-logo">'
    else:
        escudo_html = '<div style="font-size:92px;line-height:1;margin-bottom:12px;">🛡️</div>'

    st.markdown(f"""
    <div class="login-card">
        {escudo_html}
        <div class="club-title">CLUB A. UNIÓN</div>
        <div class="club-subtitle">Análisis de Rendimiento Físico</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.15, 1])
    with c2:
        st.markdown("### Iniciar sesión")
        user = st.selectbox("Usuario", list(USUARIOS.keys()))
        pwd = st.text_input("Password", type="password")
        if st.button("Ingresar", use_container_width=True):
            if USUARIOS.get(user) == pwd:
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        with st.expander("¿Olvidaste tu contraseña?"):
            mail = st.text_input("Ingresá tu correo")
            if st.button("Solicitar restablecimiento", use_container_width=True):
                st.info("Solicitud registrada. En esta versión inicial, el administrador cambia la clave manualmente.")
    st.stop()

# ==========================================================
# SIDEBAR — con escudo del club
# ==========================================================
escudo_b64_side = img_to_base64(ESCUDO_PATH)
if escudo_b64_side:
    escudo_side_html = f'<img src="data:image/png;base64,{escudo_b64_side}">'
else:
    escudo_side_html = '<span style="font-size:52px;">🛡️</span>'

st.sidebar.markdown(f"""
<div class="sidebar-escudo">
    {escudo_side_html}
    <div class="sidebar-club-name">CLUB A. UNIÓN</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("**⚙️ Filtros**")
if st.sidebar.button("Cerrar sesión", use_container_width=True):
    st.session_state.login = False
    st.rerun()

partidos_base = filtrar_solo_partidos(gps)

anios_validos = sorted(partidos_base["AÑO"].dropna().astype(int).unique(), reverse=True)
anio = st.sidebar.selectbox("AÑO", anios_validos)

jugadores = sorted(partidos_base[partidos_base["AÑO"] == anio]["JUGADOR"].dropna().unique())
jugador = st.sidebar.selectbox("JUGADOR", jugadores)

n_partidos = st.sidebar.number_input("N° PARTIDOS", min_value=1, max_value=30, value=5, step=1)

# ==========================================================
# FILTROS
# ==========================================================
gps_anio = partidos_base[partidos_base["AÑO"] == anio].copy()
gps_jugador = gps_anio[gps_anio["JUGADOR"] == jugador].sort_values("FECHA", ascending=False).head(n_partidos)

perfil_df = data_jug[data_jug["JUGADOR"] == jugador].copy()

# ── Posición más reciente desde GPS (para jugadores poliposición) ──────
pos_reciente = None
if not gps_jugador.empty and "POSICION" in gps_jugador.columns:
    # Usar la posición del partido más reciente
    gps_all_jug = partidos_base[partidos_base["JUGADOR"] == jugador].sort_values("FECHA", ascending=False)
    if not gps_all_jug.empty:
        pos_reciente = str(gps_all_jug["POSICION"].iloc[0]).strip()

if perfil_df.empty:
    perfil = pd.Series({
        "JUGADOR": jugador,
        "POSICION": pos_reciente or "Sin dato"
    })
else:
    # Si hay múltiples filas (poliposición), usar la que coincida con pos_reciente
    if pos_reciente and "POSICION" in perfil_df.columns:
        match = perfil_df[perfil_df["POSICION"] == pos_reciente]
        perfil = match.iloc[0] if not match.empty else perfil_df.iloc[0]
    else:
        perfil = perfil_df.iloc[0]

posicion = pos_reciente or safe_get(perfil, "POSICION", "Sin dato")
ref_pos = gps_anio[(gps_anio["POSICION"] == posicion) & (num_series(gps_anio, "MIN") >= 70)]

# ── Banderas: img desde flagcdn.com (siempre funciona) ─────────────────
NAC_TO_ISO = {
    "ARG":"ar","AR":"ar","URU":"uy","UY":"uy","URY":"uy",
    "ECU":"ec","EC":"ec","COL":"co","CO":"co",
    "CH":"cl","CHI":"cl","CHL":"cl","PAR":"py","PY":"py",
    "BOL":"bo","BO":"bo","PER":"pe","PE":"pe",
    "BRA":"br","BR":"br","VEN":"ve","VE":"ve",
    "MEX":"mx","MX":"mx","ESP":"es","ES":"es",
    "ITA":"it","IT":"it","FRA":"fr","FR":"fr",
    "USA":"us","US":"us","ALE":"de","GER":"de","DE":"de",
    "POR":"pt","PT":"pt","HON":"hn","HN":"hn",
    "GUA":"gt","GT":"gt","CRC":"cr","CR":"cr",
}
NAC_LABEL = {
    "ar":"ARG","uy":"URU","ec":"ECU","co":"COL","cl":"CHI",
    "py":"PAR","bo":"BOL","pe":"PER","br":"BRA","ve":"VEN",
    "mx":"MEX","es":"ESP","it":"ITA","fr":"FRA","us":"USA",
    "de":"ALE","pt":"POR","hn":"HON","gt":"GUA","cr":"CRC",
}

def bandera_badge(nac_raw):
    iso = NAC_TO_ISO.get(str(nac_raw).strip().upper(), "")
    if not iso:
        return f'<span style="color:#94a3b8;font-size:11px;">{str(nac_raw)[:3]}</span>'
    lbl = NAC_LABEL.get(iso, iso.upper())
    return (f'<img src="https://flagcdn.com/20x15/{iso}.png" '
            f'width="20" height="15" style="vertical-align:middle;'
            f'border-radius:2px;margin-right:4px;" alt="{lbl}">'
            f'<span style="font-size:11px;font-weight:700;'
            f'color:#94a3b8;vertical-align:middle;">{lbl}</span>')

# ==========================================================
# HEADER JUGADOR
# ==========================================================
nacionalidad = safe_get(perfil, "NACIONALIDAD", "")
bandera_raw = safe_get(perfil, "BANDERA", "")
nac_raw = bandera_raw if bandera_raw not in ["Sin dato","nan",""] else nacionalidad
bandera_html = bandera_badge(nac_raw)
nac_code = NAC_TO_ISO.get(str(nac_raw).strip().upper(), "")
nac_label = NAC_LABEL.get(nac_code, str(nac_raw)[:3].upper()) if nac_code else str(nac_raw)[:3].upper()

altura = safe_get(perfil, "ALTURA", "Sin dato")
fecha_nac = safe_get(perfil, "FECHA_NAC", None)
edad = edad_desde(fecha_nac)
fecha_nac_formato = fecha_txt(fecha_nac)

# ── FOTO del jugador — busca en assets/jugadores/ ─────────────────────
foto_path = buscar_foto_jugador(jugador)
if foto_path:
    foto_html = html_img(foto_path, "player-photo", "👤")
else:
    foto_html = '<div class="player-avatar-fallback">👤</div>'


# ── CAMPO: SVG HORIZONTAL con posición según perfil ───────────────────
# Campo horizontal: viewBox 160×100 (ancho×alto)
# Orientación: arco propio = IZQUIERDA, arco rival = DERECHA
# El jugador se ubica en X (profundidad) e Y (banda: arriba=izq, abajo=der)

def get_pos_xy(pos_str, perfil_der=True):
    """
    Campo horizontal 160×100. Arco propio=IZQ, rival=DER.
    y: 0=arriba(DER), 100=abajo(IZQ)
    Perfil DER → banda SUPERIOR (y~22), IZQ → banda INFERIOR (y~78)
    """
    p = str(pos_str).upper().strip()
    y_d = 78   # DER = ABAJO del campo (según imagen referencia)
    y_i = 22   # IZQ = ARRIBA del campo (según imagen referencia)

    # Orden CRÍTICO: más específico primero para evitar substring false-matches
    # 1. Arquero
    if any(k in p for k in ["ARQ","ARQUERO","GK","GOALKEEPER","PORTERO"]):
        return 10, 50

    # 2. Extremos explícitos (antes de "EXT" genérico y antes de "DEL")
    if any(k in p for k in ["EXT DER","EXTREMO DER","WING DER","RW"]):
        return 112, 78   # EXT DER = abajo
    if any(k in p for k in ["EXT IZQ","EXTREMO IZQ","WING IZQ","LW"]):
        return 112, 22   # EXT IZQ = arriba

    # 3. Laterales (DEF LAT antes que DEF CEN para evitar match en "LATERAL")
    if any(k in p for k in ["DEF LAT","LATERAL","LAT"]):
        return 32, y_d if perfil_der else y_i

    # 4. Defensores centrales
    if any(k in p for k in ["DEF CEN","DEF CENT","DEFENSOR CENTRAL","CENTRAL","DC"]):
        return 32, 50

    # 5. Mediocampistas defensivos
    if any(k in p for k in ["MEDIO DEF","MED DEF","MDC","VOLANTE DEF","VOL DEF"]):
        return 60, 50

    # 6. Mediocampistas centrales
    if any(k in p for k in ["MEDIO CENT","MEDIO CEN","MED CEN","MED CENT",
                              "MEDIO CENTRAL","MC","BOX","INTERIOR"]):
        return 72, 50

    # 7. Mediocampistas ofensivos / volantes ofensivos
    if any(k in p for k in ["MEDIO OF","MED OF","VOL OF","VOLANTE OF",
                              "ENGANCHE","CAM","MEDIAPUNTA"]):
        return 96, y_d if perfil_der else y_i

    # 8. Extremos genéricos
    if any(k in p for k in ["EXT","EXTREMO","WING","BANDA"]):
        return 112, y_d if perfil_der else y_i

    # 9. Delanteros centros
    if any(k in p for k in ["DEL CEN","DELANTERO CEN","DELANTERO CENTRAL","CF"]):
        return 138, 50

    # 10. Delanteros genéricos — "DEL" ÚLTIMO para no matchear "LATERAL"
    if any(k in p for k in ["DEL","DELANTERO","STRIKER","PTA","PUNTA"]):
        return 134, 50

    # Fallback
    return 80, 50

def dibujar_campo_svg(pos_str, perfil_der=True):
    px, py = get_pos_xy(pos_str, perfil_der)
    p = str(pos_str).upper().strip()
    short = (str(pos_str).upper()
             .replace("MEDIO","M.").replace("CENTRAL","CEN")
             .replace("DEFENSOR","DEF").replace("DELANTERO","DEL")
             .replace("ARQUERO","ARQ"))[:9]

    # ── Calcular zona difuminada según tipo de posición ──────────────────
    # Para laterales/extremos: rectángulo horizontal (zona de recorrido)
    # Para centrales/mediocampistas: elipse/rectángulo centrado
    is_lateral  = any(k in p for k in ["DEF LAT","LATERAL","LAT","EXT","EXTREMO","WING","BANDA"])
    is_central  = any(k in p for k in ["DEF CEN","DEFENSOR CENTRAL","CENTRAL","DC",
                                         "MEDIO CENT","MEDIO CEN","MED CEN","MED CENT","MC",
                                         "MEDIO DEF","MED DEF"])
    is_ofensivo = any(k in p for k in ["MEDIO OF","MED OF","OFENSIVO","VOL OF","ENGANCHE","CAM"])
    is_del      = any(k in p for k in ["DEL","DELANTERO","STRIKER"])
    is_arq      = any(k in p for k in ["ARQ","ARQUERO","GK"])

    # Zona: (x1, y1, x2, y2) — DER=ABAJO(y alto), IZQ=ARRIBA(y bajo)
    if is_arq:
        zx1, zy1, zx2, zy2 = 2, 24, 28, 76
    elif is_lateral:
        # Franja larga a lo largo de la banda
        if perfil_der:
            zx1, zy1, zx2, zy2 = 20, 58, 120, 98   # DER = franja inferior
        else:
            zx1, zy1, zx2, zy2 = 20, 2, 120, 42    # IZQ = franja superior
    elif is_central:
        zx1, zy1, zx2, zy2 = px-22, 20, px+22, 80
    elif is_ofensivo:
        if perfil_der:
            zx1, zy1, zx2, zy2 = 60, 58, 130, 98   # DER = zona inferior ofensiva
        else:
            zx1, zy1, zx2, zy2 = 60, 2, 130, 42    # IZQ = zona superior ofensiva
    elif is_del:
        zx1, zy1, zx2, zy2 = 110, 18, 158, 82
    else:
        zx1, zy1, zx2, zy2 = px-18, py-22, px+18, py+22

    # Clampear a límites del campo
    zx1 = max(2, zx1);   zy1 = max(2, zy1)
    zx2 = min(158, zx2); zy2 = min(98, zy2)
    zw  = zx2 - zx1;     zh  = zy2 - zy1
    zcx = (zx1 + zx2) / 2
    zcy = (zy1 + zy2) / 2

    zone_id = f"zg_{abs(hash(pos_str+str(perfil_der)))%9999}"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100"
         width="228" height="143" style="display:block;border-radius:8px;
         filter:drop-shadow(0 0 10px rgba(37,99,235,.35))">
  <defs>
    <linearGradient id="cg2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#2e9455"/>
      <stop offset="50%"  stop-color="#247a43"/>
      <stop offset="100%" stop-color="#2e9455"/>
    </linearGradient>
    <radialGradient id="{zone_id}" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="#2563eb" stop-opacity="0.50"/>
      <stop offset="60%"  stop-color="#2563eb" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#2563eb" stop-opacity="0.00"/>
    </radialGradient>
  </defs>
  <!-- Fondo verde -->
  <rect width="160" height="100" fill="url(#cg2)" rx="7"/>
  <!-- Franjas verticales sutiles -->
  {''.join(f'<rect x="{i*16}" y="0" width="16" height="100" fill="rgba(0,0,0,{0.045 if i%2==0 else 0})"/>' for i in range(10))}
  <!-- Borde exterior -->
  <rect x="2" y="2" width="156" height="96" fill="none" stroke="rgba(255,255,255,0.82)" stroke-width="1.4" rx="3"/>
  <!-- Línea media vertical -->
  <line x1="80" y1="2" x2="80" y2="98" stroke="rgba(255,255,255,0.82)" stroke-width="1.1"/>
  <!-- Círculo central -->
  <circle cx="80" cy="50" r="14" fill="none" stroke="rgba(255,255,255,0.82)" stroke-width="1.1"/>
  <circle cx="80" cy="50" r="1.6" fill="rgba(255,255,255,0.9)"/>
  <!-- Área grande IZQ -->
  <rect x="2" y="24" width="26" height="52" fill="none" stroke="rgba(255,255,255,0.78)" stroke-width="1"/>
  <rect x="2" y="36" width="11" height="28" fill="none" stroke="rgba(255,255,255,0.72)" stroke-width="0.85"/>
  <circle cx="19" cy="50" r="1.3" fill="rgba(255,255,255,0.88)"/>
  <!-- Área grande DER -->
  <rect x="132" y="24" width="26" height="52" fill="none" stroke="rgba(255,255,255,0.78)" stroke-width="1"/>
  <rect x="147" y="36" width="11" height="28" fill="none" stroke="rgba(255,255,255,0.72)" stroke-width="0.85"/>
  <circle cx="141" cy="50" r="1.3" fill="rgba(255,255,255,0.88)"/>
  <!-- ZONA DIFUMINADA de la posición -->
  <rect x="{zx1}" y="{zy1}" width="{zw}" height="{zh}" rx="6"
        fill="url(#{zone_id})" clip-path="inset(0 round 3px)"/>
  <!-- Punto principal jugador -->
  <circle cx="{px}" cy="{py}" r="8.5" fill="rgba(37,99,235,0.35)"/>
  <circle cx="{px}" cy="{py}" r="6"   fill="#2563eb"/>
  <circle cx="{px}" cy="{py}" r="3.2" fill="#ffffff"/>
  <!-- Etiqueta -->
  <rect x="{px-15}" y="{py+8}" width="30" height="10" rx="3"
        fill="rgba(7,16,31,0.92)" stroke="#2563eb" stroke-width="0.8"/>
  <text x="{px}" y="{py+16.5}" text-anchor="middle" font-size="5.2"
        font-family="Inter,Arial,sans-serif" fill="#ffffff" font-weight="bold">{short}</text>
</svg>"""
    return svg

# Pasar perfil al dibujar el campo (se calcula antes en lado_upper)
campo_html = ""  # se asigna después del cálculo de perfil dominante



# ── Perfil dominante ───────────────────────────────────────────────────
lado_raw = safe_get(perfil, "LADO_HABIL", "Sin dato")
lado_upper = str(lado_raw).upper().strip()
es_izq = lado_upper.startswith("IZQ") or lado_upper.startswith("ZUR") or lado_upper in ["L", "LEFT"]
es_der = lado_upper.startswith("DER") or lado_upper.startswith("DIE") or lado_upper in ["R", "RIGHT"]

izq_active = "boot-active" if es_izq else ""
der_active = "boot-active" if es_der else ""

# Dibujar campo con perfil real del jugador
# ── Posición en campo: usar POS_ESP si existe, sino POS + PERFIL ───────
pos_esp_raw = safe_get(perfil, "POS_ESP", None)
pos_esp_val = str(pos_esp_raw).strip() if pos_esp_raw else ""
_tiene_pos_esp = pos_esp_val not in ["", "Sin dato", "nan", "None"]

if _tiene_pos_esp:
    _pos_campo   = pos_esp_val.upper().strip()
    # El lado viene EXPLÍCITO en POS_ESP: "DEF LAT IZQ" → IZQ, "MEDIO OF DER" → DER
    _es_der_camp = _pos_campo.endswith("DER") or " DER" in _pos_campo
    _es_izq_camp = _pos_campo.endswith("IZQ") or " IZQ" in _pos_campo
    if _es_izq_camp:
        _perfil_camp = False   # IZQ → banda inferior (y=78)
    elif _es_der_camp:
        _perfil_camp = True    # DER → banda superior (y=22)
    else:
        _perfil_camp = es_der  # sin lado explícito → usar perfil del jugador
else:
    _pos_campo   = posicion.upper().strip()
    _perfil_camp = es_der

campo_html = dibujar_campo_svg(_pos_campo, perfil_der=_perfil_camp)

# Debug campo (colapsado — solo para verificar)
with st.expander("🔍 Debug posición campo", expanded=False):
    st.caption(f"**POS_ESP en DB:** `{pos_esp_val or '— (vacío)'}`")
    st.caption(f"**Posición usada:** `{_pos_campo}`")
    st.caption(f"**perfil_der={_perfil_camp}** → DER=abajo(y=78), IZQ=arriba(y=22)")
    st.caption(f"**Perfil jugador (LADO_HABIL):** `{lado_upper}` → es_der={es_der}")

escudo_b64_hdr = img_to_base64(ESCUDO_PATH)
escudo_hdr_html = (f'<img src="data:image/png;base64,{escudo_b64_hdr}">'
                   if escudo_b64_hdr else '<span style="font-size:48px;">🛡️</span>')

st.markdown(f"""
<div class="player-header">
    <div>{foto_html}</div>
    <div>
        <div class="player-sub">{bandera_html} {nac_label} · {posicion}</div>
        <div class="player-name">{jugador}</div>
        <div>
            <span class="info-chip">🎂 {fecha_nac_formato}</span>
            <span class="info-chip">Edad: {edad}</span>
            <span class="info-chip">📏 {altura}</span>
            <span class="info-chip">⚽ {posicion}</span>
        </div>
        <div style="margin-top:8px;">
            <span class="boot-box {izq_active}">👟 IZQ</span>
            <span class="boot-box {der_active}">👟 DER</span>
        </div>
    </div>
    <div class="campo-col">
        {campo_html}
    </div>
    <div class="escudo-header-col">
        {escudo_hdr_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# TARJETAS RESUMEN — 6 en una sola línea
# ==========================================================
st.markdown("<div class='section-title'>Tarjetas resumen | Mejor valor vs promedio posición +70'</div>", unsafe_allow_html=True)

metricas = [
    ("⏱️", "MIN",         "MIN",      "min"),
    ("📏", "Dist. Total", "TOT DIST", "m"),
    ("🏃", "MTS/MIN",     "MTS/MIN",  "m/min"),
    ("🔥", ">19 km/h",    "HSD",      "m"),
    ("⚡", ">24 km/h",    "SPD",      "m"),
    ("🚀", "V-MAX",       "V-MAX",    "km/h"),
]

mcols = st.columns(6)
for i, (icono, titulo, col, unidad) in enumerate(metricas):
    valor = val_num(gps_jugador, col, "max") if col in gps_jugador.columns else None
    ref   = val_num(ref_pos,     col, "mean") if col in ref_pos.columns     else None
    with mcols[i]:
        metric_card(icono, titulo, valor, unidad, ref)

# ==========================================================
# TABLA PARTIDOS
# ==========================================================
st.markdown("<div class='section-title'>Últimos partidos seleccionados</div>", unsafe_allow_html=True)

columnas_tabla = [
    ("FECHA",    "Fecha"),
    ("RIVAL",    "Rival"),
    ("MIN",      "Min"),
    ("TOT DIST", "Dist tot"),
    ("MTS/MIN",  "Mts/min"),
    ("HSD",      ">19 km/h"),
    ("SPD",      ">24 km/h"),
    ("SPRINTS",  "Sprints"),
    ("ACEL",     "Acel"),
    ("DES",      "Des"),
    ("V-MAX",    "V-Max"),
]

cols_existentes = [(c, nombre) for c, nombre in columnas_tabla if c in gps_jugador.columns]
tabla = gps_jugador[[c for c, _ in cols_existentes]].copy()
tabla = tabla.rename(columns={c: nombre for c, nombre in cols_existentes})
if "Fecha" in tabla.columns:
    tabla["Fecha"] = pd.to_datetime(tabla["Fecha"], errors="coerce").dt.strftime("%d/%m/%Y")

# Columnas numéricas para resaltar el mejor
COLS_HIGHLIGHT_MAX = [">19 km/h", ">24 km/h", "Mts/min", "Dist tot", "V-Max"]
COLS_HIGHLIGHT_MIN = ["Min"]   # menor no se destaca, solo las de máximo

def render_tabla_html(df):
    num_cols = [c for c in df.columns if c not in ["Fecha", "Rival"]]
    # Calcular máx por columna
    maximos = {}
    for c in num_cols:
        try:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any():
                maximos[c] = s.max()
        except Exception:
            pass

    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for col in df.columns:
            val = row[col]
            val_str = str(val) if pd.notna(val) else "—"
            style = "text-align:center;padding:7px 10px;"
            # Destacar máximo de columna
            if col in maximos:
                try:
                    v = float(val)
                    if v == maximos[col]:
                        style += ("background:rgba(16,242,160,0.15);"
                                  "color:#10f2a0;font-weight:900;"
                                  "border-radius:6px;")
                except Exception:
                    pass
            if col in ["Fecha", "Rival"]:
                style += "text-align:left;"
            cells += f'<td style="{style}">{val_str}</td>'
        rows_html += f"<tr>{cells}</tr>"

    header = "".join(
        f'<th style="text-align:center;padding:8px 10px;color:#2563eb;'
        f'font-weight:900;font-size:11px;letter-spacing:1px;'
        f'border-bottom:2px solid rgba(37,99,235,.35);white-space:nowrap;">'
        f'{c}</th>'
        for c in df.columns
    )

    html = f"""
<div style="overflow-x:auto;border-radius:14px;border:1px solid rgba(255,255,255,.08);">
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;
              font-size:13px;color:#e2e8f0;background:rgba(13,26,46,.95);">
  <thead><tr style="background:rgba(37,99,235,.10);">{header}</tr></thead>
  <tbody>
  {''.join(f'<tr style="border-bottom:1px solid rgba(255,255,255,.06);">{r}</tr>' for r in rows_html.split("</tr>")[:-1])}
  </tbody>
</table>
</div>"""
    # Simplify — render directly
    return html

# Render tabla estilizada
tabla_html_rows = []
num_cols_t = [c for c in tabla.columns if c not in ["Fecha","Rival"]]
maximos_t = {}
for c in num_cols_t:
    try:
        s = pd.to_numeric(tabla[c], errors="coerce")
        if s.notna().any():
            maximos_t[c] = s.max()
    except Exception:
        pass

header_cells = "".join(
    f'<th style="text-align:{"left" if c in ["Fecha","Rival"] else "center"};'
    f'padding:9px 12px;color:#2563eb;font-weight:900;font-size:11px;'
    f'letter-spacing:1px;border-bottom:2px solid rgba(37,99,235,.40);'
    f'white-space:nowrap;background:rgba(37,99,235,.08);">{c}</th>'
    for c in tabla.columns
)

body_rows = ""
for i, (_, row) in enumerate(tabla.iterrows()):
    row_bg = "rgba(255,255,255,.02)" if i % 2 == 0 else "transparent"
    cells = ""
    for col in tabla.columns:
        val = row[col]
        val_str = str(val) if pd.notna(val) else "—"
        align = "left" if col in ["Fecha","Rival"] else "center"
        extra = ""
        if col in maximos_t:
            try:
                if float(val) == maximos_t[col]:
                    extra = ("background:rgba(16,242,160,.14);color:#10f2a0;"
                             "font-weight:900;border-radius:5px;")
            except Exception:
                pass
        cells += (f'<td style="padding:8px 12px;text-align:{align};{extra}'
                  f'font-size:13px;">{val_str}</td>')
    body_rows += f'<tr style="background:{row_bg};border-bottom:1px solid rgba(255,255,255,.05);">{cells}</tr>'

tabla_html = f"""
<div style="overflow-x:auto;border-radius:14px;border:1px solid rgba(255,255,255,.09);
            box-shadow:0 4px 20px rgba(0,0,0,.25);margin-bottom:8px;">
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;
              color:#e2e8f0;background:rgba(13,26,46,.96);">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{body_rows}</tbody>
</table>
</div>"""

st.markdown(tabla_html, unsafe_allow_html=True)

# ==========================================================
# GRÁFICOS ANALÍTICOS
# ==========================================================
st.markdown("<div class='section-title'>Análisis por rival</div>", unsafe_allow_html=True)

# ── Filtro de fechas (independiente de N° partidos) ────────────────────
gps_jug_all = partidos_base[partidos_base["JUGADOR"] == jugador].copy()
if gps_jug_all.empty:
    st.info("Sin datos de partidos para graficar.")
else:
    fecha_min_d = gps_jug_all["FECHA"].min().date()
    fecha_max_d = gps_jug_all["FECHA"].max().date()

    fc1, fc2 = st.columns(2)
    with fc1:
        fecha_desde = st.date_input("Desde", value=fecha_min_d,
                                     min_value=fecha_min_d, max_value=fecha_max_d,
                                     key="fecha_desde")
    with fc2:
        fecha_hasta = st.date_input("Hasta", value=fecha_max_d,
                                     min_value=fecha_min_d, max_value=fecha_max_d,
                                     key="fecha_hasta")

    mask_f = (gps_jug_all["FECHA"].dt.date >= fecha_desde) & \
             (gps_jug_all["FECHA"].dt.date <= fecha_hasta)
    gps_graf = gps_jug_all[mask_f].copy()

    # Columnas numéricas necesarias
    for _c in ["MIN", "TOT DIST", "MTS/MIN", "HSD", "SPD"]:
        if _c in gps_graf.columns:
            gps_graf[_c] = pd.to_numeric(gps_graf[_c], errors="coerce")

    if not gps_graf.empty and "RIVAL" in gps_graf.columns:
        # Solo agregar columnas que existen en el df
        _agg_dict = {"MTS_MIN_PROM": ("MTS/MIN", "mean"),
                     "MIN_TOTAL":    ("MIN",      "sum"),
                     "N_PARTIDOS":   ("MIN",      "count")}
        if "HSD"      in gps_graf.columns: _agg_dict["HSD_PROM"]      = ("HSD",      "mean")
        if "SPD"      in gps_graf.columns: _agg_dict["SPD_PROM"]      = ("SPD",      "mean")
        if "TOT DIST" in gps_graf.columns: _agg_dict["TOT_DIST_PROM"] = ("TOT DIST", "mean")

        agg_rival = gps_graf.groupby("RIVAL", as_index=False).agg(**_agg_dict)
        # Asegurar columnas con default si no existían
        for _col in ["HSD_PROM", "SPD_PROM", "TOT_DIST_PROM"]:
            if _col not in agg_rival.columns:
                agg_rival[_col] = float("nan")

        drop_subset = ["MTS_MIN_PROM"]
        if "HSD_PROM" in agg_rival.columns:
            drop_subset.append("HSD_PROM")
        agg_rival = agg_rival.dropna(subset=drop_subset)

        gc1, gc2 = st.columns(2)

        # ── SCATTER PLOT con Plotly ───────────────────────────────────────
        with gc1:
            if not HAS_PLOTLY:
                st.warning("Instalá plotly: `pip install plotly`")
            elif agg_rival.empty:
                st.info("Sin datos suficientes.")
            else:
                COLORS_RIVALS = [
                    "#2563eb","#38bdf8","#10f2a0","#ff9f43","#a78bfa",
                    "#f472b6","#facc15","#34d399","#60a5fa","#fb923c",
                    "#e879f9","#4ade80","#f87171","#818cf8","#fbbf24",
                ]

                min_vals = agg_rival["MIN_TOTAL"].values.astype(float)
                # Tamaño fijo grande para logos — minutos reflejados en el borde
                LOGO_SIZE_PX = 55   # tamaño fijo de la imagen del logo
                sz_min, sz_max = 45, 80  # borde del marcador según minutos
                if min_vals.max() != min_vals.min():
                    sizes = sz_min + (min_vals - min_vals.min()) / \
                            (min_vals.max() - min_vals.min()) * (sz_max - sz_min)
                else:
                    sizes = [60.0] * len(min_vals)

                fig_s = go.Figure()

                # ── Logo del club UNION (o logo del rival si existe) ─────
                EQUIPOS_DIR = Path("assets") / "Equipos"

                def logo_b64_rival(rival_name):
                    if not EQUIPOS_DIR.exists():
                        return None
                    rn = rival_name.upper().strip()
                    for f in EQUIPOS_DIR.iterdir():
                        if f.suffix.lower() in [".png",".jpg",".jpeg",".webp"]:
                            if f.stem.upper() == rn or rn in f.stem.upper() or f.stem.upper() in rn:
                                return base64.b64encode(f.read_bytes()).decode()
                    return None

                for idx, (_, row) in enumerate(agg_rival.iterrows()):
                    clr  = COLORS_RIVALS[idx % len(COLORS_RIVALS)]
                    rv   = str(row["RIVAL"])
                    sz   = float(sizes[idx])
                    logo = logo_b64_rival(rv)

                    # Punto invisible solo para tooltip
                    fig_s.add_trace(go.Scatter(
                        x=[row["MTS_MIN_PROM"]], y=[row["HSD_PROM"]],
                        mode="markers",
                        marker=dict(
                            size=sz,
                            color="rgba(0,0,0,0)" if logo else clr,
                            line=dict(color=clr, width=2.5),
                            opacity=0.0 if logo else 0.85,
                        ),
                        customdata=[[row["MTS_MIN_PROM"], row["HSD_PROM"],
                                     row["MIN_TOTAL"], row["N_PARTIDOS"]]],
                        hovertemplate=(
                            f"<b>{rv}</b><br>"
                            "MTS/MIN: %{customdata[0]:.1f}<br>"
                            ">19km/h: %{customdata[1]:.0f} m<br>"
                            "MIN totales: %{customdata[2]:.0f}<br>"
                            "Partidos: %{customdata[3]}<extra></extra>"
                        ),
                        name=rv, showlegend=False,
                    ))

                    if logo:
                        # Logo grande en data units (se calcula tras conocer el rango)
                        fig_s.add_layout_image(dict(
                            source=f"data:image/png;base64,{logo}",
                            x=row["MTS_MIN_PROM"],
                            y=row["HSD_PROM"],
                            xref="x", yref="y",
                            sizex=0,  # placeholder — se sobreescribirá abajo
                            sizey=0,
                            xanchor="center", yanchor="middle",
                            layer="above",
                            name=rv,
                        ))
                    else:
                        # Sin logo: texto grande centrado sobre el marcador
                        fig_s.add_trace(go.Scatter(
                            x=[row["MTS_MIN_PROM"]], y=[row["HSD_PROM"]],
                            mode="text",
                            text=[rv[:5]],
                            textfont=dict(color="white", size=9, family="Inter",
                                         weight="bold" if hasattr(dict, "weight") else None),
                            showlegend=False, hoverinfo="skip",
                        ))

                # Calcular rango de ejes para definir img_size proporcional
                if not agg_rival.empty:
                    x_range = agg_rival["MTS_MIN_PROM"].max() - agg_rival["MTS_MIN_PROM"].min()
                    y_range = agg_rival["HSD_PROM"].max() - agg_rival["HSD_PROM"].min()
                    x_span  = max(x_range * 1.4, 2)
                    y_span  = max(y_range * 1.4, 200)
                    img_sx  = x_span * 0.095   # -15% from 0.112
                    img_sy  = y_span * 0.238   # -15% from 0.28
                    img_s   = max(img_sx, img_sy * (x_span/y_span))
                    # Actualizar tamaños de imágenes
                    for img in fig_s.layout.images:
                        img.sizex = img_sx
                        img.sizey = img_sy

                fig_s.update_layout(
                    title=dict(text="MTS/MIN vs >19km/h | burbuja = MIN jugados",
                               font=dict(color="#ffffff", size=11)),
                    xaxis=dict(title="Prom. MTS/MIN", color="#94a3b8",
                               gridcolor="#1e3a5f", showgrid=True,
                               zeroline=False, tickfont=dict(size=9)),
                    yaxis=dict(title="Prom. >19 km/h (m)", color="#94a3b8",
                               gridcolor="#1e3a5f", showgrid=True,
                               zeroline=False, tickfont=dict(size=9)),
                    plot_bgcolor="#0d1a2e",
                    paper_bgcolor="#0d1a2e",
                    font=dict(color="#e8ecf4"),
                    margin=dict(l=50, r=20, t=45, b=40),
                    height=380,
                )
                st.plotly_chart(fig_s, use_container_width=True)

        # ── BARRAS HORIZONTALES con Plotly ────────────────────────────────
        with gc2:
            if not HAS_PLOTLY:
                st.warning("Instalá plotly: `pip install plotly`")
            else:
              BAR_METRICS = [
                ("TOT DIST", "Dist. Total (m)",  "#38bdf8"),
                ("MTS/MIN",  "MTS/MIN",           "#10f2a0"),
                ("HSD",      ">19 km/h (m)",      "#ff9f43"),
                ("SPD",      ">24 km/h (m)",      "#2563eb"),
              ]
              bar_data = []
              for col_b, label_b, color_b in BAR_METRICS:
                if col_b in gps_graf.columns:
                    val_b = pd.to_numeric(gps_graf[col_b], errors="coerce").mean()
                    if pd.notna(val_b):
                        bar_data.append((label_b, val_b, color_b))

              if not bar_data:
                st.info("Sin datos de métricas locomotivas.")
              else:
                # Rangos dinámicos: promedio y máximo de la posición del jugador
                # ref_pos ya está filtrado por posición + MIN >= 70
                REF_RANGES    = {}
                PROM_POSICION = {}
                FIXED_MIN = {
                    "Dist. Total (m)": 5000,
                    "MTS/MIN":         90,
                    ">19 km/h (m)":    250,
                    ">24 km/h (m)":    100,
                }
                col_map = {
                    "Dist. Total (m)": "TOT DIST",
                    "MTS/MIN":         "MTS/MIN",
                    ">19 km/h (m)":    "HSD",
                    ">24 km/h (m)":    "SPD",
                }
                for lbl, col_r in col_map.items():
                    if col_r in ref_pos.columns:
                        s = pd.to_numeric(ref_pos[col_r], errors="coerce").dropna()
                        if not s.empty:
                            r_min = FIXED_MIN.get(lbl, 0)
                            r_max = round(s.max(), 1)
                            prom  = round(s.mean(), 1)
                            REF_RANGES[lbl]    = (r_min, r_max)
                            PROM_POSICION[lbl] = prom

                FALLBACK = {
                    "Dist. Total (m)": (5000, 12000),
                    "MTS/MIN":         (90,   130),
                    ">19 km/h (m)":    (250,  1300),
                    ">24 km/h (m)":    (100,  500),
                }

                fig_b = go.Figure()
                for (lbl, val, clr) in bar_data:
                    r_min, r_max = REF_RANGES.get(lbl, FALLBACK.get(lbl, (0, max(val*1.5, 1))))
                    if r_max <= r_min:
                        r_max = r_min * 1.5 or 1
                    val_clamped = max(r_min, min(val, r_max))
                    pct = (val_clamped - r_min) / (r_max - r_min) * 100 if r_max != r_min else 50
                    pct = round(min(pct, 100), 1)
                    val_str = f"{val:,.0f} m" if val > 10 else f"{val:.2f}"
                    bar_clr = "#10f2a0" if pct >= 66 else (clr if pct >= 33 else "#ff6b6b")

                    # Fondo gris (100% del rango)
                    fig_b.add_trace(go.Bar(
                        y=[lbl], x=[100],
                        orientation="h",
                        marker=dict(color="#1e3a5f"),
                        showlegend=False, hoverinfo="skip", width=0.55,
                    ))
                    # Barra del jugador
                    fig_b.add_trace(go.Bar(
                        y=[lbl], x=[pct],
                        orientation="h",
                        marker=dict(color=bar_clr, opacity=0.92),
                        showlegend=False,
                        text=[f"{val_str}  ({pct:.0f}%)"] if pct > 12 else [f"{val_str}"],
                        textposition="inside" if pct > 20 else "outside",
                        textfont=dict(color="white", size=10, family="Inter"),
                        hovertemplate=(
                            f"<b>{lbl}</b><br>Valor: {val_str}<br>"
                            f"Mín fijo: {r_min:,.0f} | Máx posición: {r_max:,.0f}<br>"
                            f"Posición en rango: {pct:.0f}%<extra></extra>"
                        ),
                        width=0.55,
                    ))
                    # Línea punteada del promedio de POSICIÓN (por barra individual)
                    if lbl in PROM_POSICION:
                        prom_pct = (PROM_POSICION[lbl] - r_min) / (r_max - r_min) * 100 if r_max != r_min else 50
                        prom_pct = round(min(max(prom_pct, 0), 100), 1)
                        fig_b.add_shape(
                            type="line",
                            x0=prom_pct, x1=prom_pct,
                            y0=bar_data.index((lbl, val, clr)) - 0.4,
                            y1=bar_data.index((lbl, val, clr)) + 0.4,
                            xref="x", yref="y domain" if False else "paper",
                            line=dict(color="rgba(255,255,255,0.55)", width=2, dash="dot"),
                        )

                fig_b.add_vline(x=100, line=dict(color="rgba(255,255,255,0.20)", width=1, dash="dot"))

                fig_b.update_layout(
                    title=dict(
                        text=f"Variables locomotivas vs. rango posición {posicion}",
                        font=dict(color="#ffffff", size=11)
                    ),
                    barmode="overlay",
                    xaxis=dict(
                        range=[0, 108],
                        tickvals=[0, 25, 50, 75, 100],
                        ticktext=["Mín","25%","50%","75%","Máx"],
                        color="#94a3b8", tickfont=dict(size=9),
                        gridcolor="#1e3a5f", showgrid=True,
                    ),
                    yaxis=dict(color="#94a3b8", tickfont=dict(size=10), autorange="reversed"),
                    plot_bgcolor="#0d1a2e",
                    paper_bgcolor="#0d1a2e",
                    font=dict(color="#e8ecf4"),
                    margin=dict(l=120, r=20, t=50, b=35),
                    height=380,
                )
                st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.info("Se necesita columna RIVAL en GPS para los gráficos.")

# ==========================================================
# LESIONES — FIX 3: badge compacto para última lesión
# ==========================================================
st.markdown("<div class='section-title'>Disponibilidad y lesiones</div>", unsafe_allow_html=True)

les = lesiones[lesiones["JUGADOR"] == jugador].copy()
if "AÑO" in les.columns:
    les = les[les["AÑO"] == anio]
les = les.sort_values("FECHA", ascending=False) if "FECHA" in les.columns else les

# ── Clasificar cada lesión: resuelta vs en recuperación ───────────────
# "En recuperación" = tiene LESION cargada PERO DAY_OFF_DXT está vacío/NaN
EN_RECUPERACION = "⚕️ En recuperación - a determinar"

def clasificar_day_off(val):
    """Retorna el valor numérico si existe, o el texto de recuperación si está vacío."""
    if pd.isna(val) or str(val).strip() in ["", "nan", "None", "0", "0.0"]:
        return None   # vacío real
    try:
        n = float(val)
        return int(n) if n > 0 else None
    except Exception:
        return None

if "DAY_OFF_DXT" in les.columns:
    les["_day_num"]  = les["DAY_OFF_DXT"].apply(clasificar_day_off)
    les["_en_recup"] = les["_day_num"].isna() & les["LESION"].notna() & \
                       (les["LESION"].astype(str).str.strip() != "")
    les["DAY_OFF_DXT_DISPLAY"] = les.apply(
        lambda r: EN_RECUPERACION if r["_en_recup"] else
                  (str(int(r["_day_num"])) if r["_day_num"] is not None else "—"),
        axis=1
    )
    # Para suma solo tomar los numéricos
    dias_perdidos = int(les["_day_num"].fillna(0).sum())
else:
    les["_en_recup"] = False
    les["DAY_OFF_DXT_DISPLAY"] = "—"
    dias_perdidos = 0

# Detectar si la lesión más reciente está en recuperación
hay_lesion_activa = not les.empty and les.iloc[0]["_en_recup"]

# ── KPI en 3 columnas ─────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

# KPI en 3 columnas — HTML para control total de colores
if hay_lesion_activa:
    c1.markdown(f"""
<div style="background:rgba(13,26,46,.95);border:1px solid rgba(255,255,255,.10);
            border-radius:14px;padding:14px 16px;">
  <div style="font-size:11px;color:#93c5fd;font-weight:700;">🩺 Días perdidos</div>
  <div style="font-family:'Bebas Neue',sans-serif;font-size:32px;color:#fff;line-height:1.1;margin:4px 0;">{dias_perdidos}</div>
  <div style="font-size:12px;font-weight:700;color:#ff6b6b;">
    🔴 Nueva lesión en TTO
  </div>
</div>""", unsafe_allow_html=True)
else:
    c1.metric("🩺 Días perdidos", dias_perdidos)

c2.metric("⚠️ Lesiones", len(les))
c3.metric("📌 N° lesiones año", len(les))

# ── Badge última lesión ────────────────────────────────────────────────
if not les.empty:
    ultima_lesion_full = str(les["LESION"].iloc[0])
    badge_color = "rgba(255,107,107,.18)" if hay_lesion_activa else "rgba(37,99,235,.12)"
    badge_border = "rgba(255,107,107,.50)" if hay_lesion_activa else "rgba(37,99,235,.30)"
    badge_texto = "🔴 EN TRATAMIENTO" if hay_lesion_activa else "🩹 ÚLTIMA LESIÓN"
    st.markdown(f"""
<div style="margin:8px 0 12px 0;">
    <span style="font-size:9px;color:#94a3b8;font-weight:700;letter-spacing:2px;
                 text-transform:uppercase;">{badge_texto}</span><br>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:8px 16px;
                 border-radius:12px;background:{badge_color};border:1px solid {badge_border};
                 color:{'#fca5a5' if hay_lesion_activa else '#fca5a5'};
                 font-size:13px;font-weight:700;">
        {ultima_lesion_full}
        {'&nbsp;&nbsp;<span style="font-size:10px;background:rgba(255,107,107,.3);padding:2px 8px;border-radius:6px;font-weight:900;">EN RECUPERACIÓN</span>' if hay_lesion_activa else ''}
    </span>
</div>""", unsafe_allow_html=True)
else:
    ultima_lesion_full = "Sin lesiones"

# ── Tabla de lesiones — mismo estilo que tabla GPS ────────────────────
if not les.empty:
    cols_show = [c for c in ["FECHA", "LESION", "REGION", "DAY_OFF_DXT_DISPLAY"] if c in les.columns]
    tabla_les = les[cols_show].copy()
    if "FECHA" in tabla_les.columns:
        tabla_les["FECHA"] = tabla_les["FECHA"].dt.strftime("%d/%m/%Y")
    tabla_les = tabla_les.rename(columns={"DAY_OFF_DXT_DISPLAY": "DÍAS BAJA"})

    # Headers
    header_cells_les = "".join(
        f'<th style="text-align:{"left" if c in ["FECHA","LESION","REGION"] else "center"};'
        f'padding:9px 12px;color:#2563eb;font-weight:900;font-size:11px;'
        f'letter-spacing:1px;border-bottom:2px solid rgba(37,99,235,.40);'
        f'white-space:nowrap;background:rgba(37,99,235,.08);">{c}</th>'
        for c in tabla_les.columns
    )
    body_rows_les = ""
    for i, (_, row) in enumerate(tabla_les.iterrows()):
        es_recup = str(row.get("DÍAS BAJA","")) == EN_RECUPERACION or \
                   "recuperación" in str(row.get("DÍAS BAJA","")).lower()
        row_bg = "rgba(255,107,107,.06)" if es_recup else ("rgba(255,255,255,.02)" if i%2==0 else "transparent")
        cells = ""
        for col in tabla_les.columns:
            val = row[col]
            val_str = str(val) if pd.notna(val) else "—"
            align = "left" if col in ["FECHA","LESION","REGION"] else "center"
            extra = ""
            if col == "DÍAS BAJA" and es_recup:
                extra = ("color:#fbbf24;font-weight:700;font-style:italic;font-size:11px;")
            cells += f'<td style="padding:8px 12px;text-align:{align};{extra}font-size:13px;">{val_str}</td>'
        body_rows_les += f'<tr style="background:{row_bg};border-bottom:1px solid rgba(255,255,255,.05);">{cells}</tr>'

    st.markdown(f"""
<div style="overflow-x:auto;border-radius:14px;border:1px solid rgba(255,255,255,.09);
            box-shadow:0 4px 20px rgba(0,0,0,.25);margin-bottom:8px;">
<table style="width:100%;border-collapse:collapse;font-family:Inter,sans-serif;
              color:#e2e8f0;background:rgba(13,26,46,.96);">
  <thead><tr>{header_cells_les}</tr></thead>
  <tbody>{body_rows_les}</tbody>
</table>
</div>""", unsafe_allow_html=True)

# ==========================================================
# EVALUACIONES FÍSICAS — 6 mini tarjetas en una fila
# ==========================================================
st.markdown("<div class='section-title'>Evaluaciones físicas</div>", unsafe_allow_html=True)

# ── Cargar y limpiar ──────────────────────────────────────
cmj_j = cmj[cmj["JUGADOR"] == jugador].copy() if "JUGADOR" in cmj.columns else pd.DataFrame()
nord_j = nordico[nordico["JUGADOR"] == jugador].copy() if "JUGADOR" in nordico.columns else pd.DataFrame()

# Strip adicional (por si acaso) — sin warning de pandas
for _df in [cmj_j, nord_j]:
    _df.columns = _df.columns.str.strip()
    for _c in _df.select_dtypes(include=["object", "string"]).columns:
        _df[_c] = _df[_c].astype(str).str.strip().replace({"None": pd.NA, "nan": pd.NA})

if "AÑO" in cmj_j.columns:
    cmj_j = cmj_j[cmj_j["AÑO"] == anio]
if "AÑO" in nord_j.columns:
    nord_j = nord_j[nord_j["AÑO"] == anio]

# ── find_col: exact → case-insensitive → keyword parcial ──
def find_col(df, target, keywords=None):
    """Busca columna: exact → case-insensitive → keywords parciales."""
    if df.empty:
        return None
    cols = list(df.columns)
    t = target.strip()
    # 1) exact
    if t in cols:
        return t
    # 2) case-insensitive + strip
    tl = t.lower()
    for c in cols:
        if c.strip().lower() == tl:
            return c
    # 3) por keywords clave (todos deben estar presentes)
    if keywords:
        kws = [k.lower() for k in keywords]
        for c in cols:
            cl = c.lower()
            if all(k in cl for k in kws):
                return c
    return None

# Nombres EXACTOS según tu sheet (ya confirmados en la imagen)
#   "Jump Height (Imp-Mom) [cm]"
#   "Eccentric Peak Power / BM [W/kg]"   ← sheet dice "Eccentric" (con cc)
#   "RSI-modified [m/s]"
cmj_col   = find_col(cmj_j, "Jump Height (Imp-Mom) [cm]",         ["jump", "height", "imp"])
power_col = find_col(cmj_j, "Eccentric Peak Power / BM [W/kg]",   ["eccentric", "peak", "power"])
rsi_col   = find_col(cmj_j, "RSI-modified [m/s]",                  ["rsi"])

# Forzar conversión numérica en esas columnas
for _col in [cmj_col, power_col, rsi_col]:
    if _col and _col in cmj_j.columns:
        cmj_j[_col] = pd.to_numeric(cmj_j[_col], errors="coerce")

cmj_val   = val_num(cmj_j, cmj_col,   "max") if cmj_col   else None
power_val = val_num(cmj_j, power_col, "max") if power_col else None
rsi_val   = val_num(cmj_j, rsi_col,   "max") if rsi_col   else None

# ── Nórdico: separado por pierna ──────────────────────────
r_col = find_col(nord_j, "R Max Force (N)", ["r max", "force"])
l_col = find_col(nord_j, "L Max Force (N)", ["l max", "force"])

for _col in [r_col, l_col]:
    if _col and _col in nord_j.columns:
        nord_j[_col] = pd.to_numeric(nord_j[_col], errors="coerce")

r_force = val_num(nord_j, r_col, "max") if r_col else None
l_force = val_num(nord_j, l_col, "max") if l_col else None

def dif_pct(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or a == 0:
        return None
    return ((a - b) / a) * 100

es_zurdo = es_izq
dif_val = dif_pct(r_force, l_force)
der_class = "der-dom" if not es_zurdo else "lado-sec"
izq_class = "izq-dom" if es_zurdo     else "lado-sec"

def fmt(v, suf, dec=1):
    if v is None:
        return "Sin dato"
    try:
        if pd.isna(v):
            return "Sin dato"
    except Exception:
        pass
    return f"{v:.{dec}f} {suf}"

def pos_mean(df, col, keywords=None):
    c = find_col(df, col, keywords)
    if c is None or df.empty:
        return None
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    return s.mean() if not s.empty else None

cmj_pos  = cmj[cmj["POSICION"] == posicion].copy()    if "POSICION" in cmj.columns    else pd.DataFrame()
nord_pos = nordico[nordico["POSICION"] == posicion].copy() if "POSICION" in nordico.columns else pd.DataFrame()
for _df2 in [cmj_pos, nord_pos]:
    _df2.columns = _df2.columns.str.strip()

cmj_pos_mean   = pos_mean(cmj_pos, "Jump Height (Imp-Mom) [cm]",       ["jump","height","imp"])
power_pos_mean = pos_mean(cmj_pos, "Eccentric Peak Power / BM [W/kg]", ["eccentric","peak","power"])
rsi_pos_mean   = pos_mean(cmj_pos, "RSI-modified [m/s]",               ["rsi"])
r_pos_mean     = pos_mean(nord_pos, "R Max Force (N)", ["r max","force"])
l_pos_mean     = pos_mean(nord_pos, "L Max Force (N)", ["l max","force"])

def pct_vs_pos(val, ref):
    if val is None or ref is None or ref == 0:
        return None
    try:
        if pd.isna(val) or pd.isna(ref):
            return None
    except Exception:
        pass
    return ((val - ref) / ref) * 100

# Filtrar CMJ y nórdico por posición del jugador para obtener promedio
cmj_pos  = cmj[cmj["POSICION"] == posicion].copy()    if "POSICION" in cmj.columns    else pd.DataFrame()
nord_pos = nordico[nordico["POSICION"] == posicion].copy() if "POSICION" in nordico.columns else pd.DataFrame()
for _df2 in [cmj_pos, nord_pos]:
    _df2.columns = _df2.columns.str.strip()

def pos_mean(df, col, keywords=None):
    c = find_col(df, col, keywords)
    if c is None or df.empty:
        return None
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    return s.mean() if not s.empty else None

cmj_pos_mean   = pos_mean(cmj_pos, "Jump Height (Imp-Mom) [cm]",       ["jump","height","imp"])
power_pos_mean = pos_mean(cmj_pos, "Eccentric Peak Power / BM [W/kg]", ["eccentric","peak","power"])
rsi_pos_mean   = pos_mean(cmj_pos, "RSI-modified [m/s]",               ["rsi"])
r_pos_mean     = pos_mean(nord_pos, "R Max Force (N)", ["r max","force"])
l_pos_mean     = pos_mean(nord_pos, "L Max Force (N)", ["l max","force"])

def eval_card_html(icono, label, valor, unidad, prom_pos, dec=1, extra_class=""):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        val_txt    = "Sin dato"
        pct_block  = ""
        prom_html  = ""
        bg_color   = "rgba(255,255,255,0.04)"
        icon_color = "rgba(255,255,255,0.06)"
        pct_color  = "#475569"
    else:
        val_txt = f"{valor:.{dec}f} {unidad}"
        pct = pct_vs_pos(valor, prom_pos)
        if pct is not None:
            pct_color = "#10f2a0" if pct >= 0 else "#ff6b6b"
            signo     = "+" if pct >= 0 else ""
            bg_color  = "rgba(16,242,160,0.08)" if pct >= 0 else "rgba(255,107,107,0.08)"
            icon_color= "rgba(16,242,160,0.18)" if pct >= 0 else "rgba(255,107,107,0.18)"
            prom_txt  = f"{prom_pos:.{dec}f} {unidad}" if prom_pos is not None else "—"
            pct_block = f'<div style="font-size:20px;font-weight:900;color:{pct_color};line-height:1;">{signo}{pct:.1f}%</div>'
            prom_html = f'<div style="font-size:8px;color:#64748b;font-weight:700;margin-top:3px;letter-spacing:.8px;">PROM: {prom_txt}</div>'
        else:
            pct_block  = '<div style="font-size:9px;color:#475569;letter-spacing:1px;">SIN REF.</div>'
            prom_html  = ""
            bg_color   = "rgba(255,255,255,0.03)"
            icon_color = "rgba(255,255,255,0.06)"
            pct_color  = "#475569"

    border_extra = ""
    if "der-dom" in extra_class:
        border_extra = "border-color:rgba(37,99,235,.50);"
    elif "lado-sec" in extra_class:
        border_extra = "opacity:0.55;"

    return f"""<div style="position:relative;overflow:hidden;padding:11px 12px;border-radius:16px;
background:linear-gradient(145deg,rgba(13,26,46,.98),rgba(17,28,53,.92));
border:1px solid rgba(255,255,255,0.10);{border_extra}
box-shadow:0 4px 18px rgba(0,0,0,.22);min-height:110px;
display:flex;flex-direction:column;justify-content:space-between;">
  <div style="font-size:7.5px;color:#93c5fd;letter-spacing:1.5px;text-transform:uppercase;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{label}</div>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-top:4px;flex:1;">
    <div style="min-width:0;flex:1;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:20px;color:#fff;line-height:1.1;letter-spacing:.3px;">{val_txt}</div>
      <div style="margin-top:3px;">{pct_block}</div>
      <div>{prom_html}</div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                width:58px;height:58px;border-radius:14px;background:{icon_color};
                flex-shrink:0;margin-left:6px;">
      <span style="font-size:34px;line-height:1;">{icono}</span>
    </div>
  </div>
</div>"""

# ── 6 columnas ────────────────────────────────────────────────────────
e1, e2, e3, e4, e5, e6 = st.columns(6)
with e1:
    st.markdown(eval_card_html("🏋️","Mejor CMJ",       cmj_val,  "cm",   cmj_pos_mean),                         unsafe_allow_html=True)
with e2:
    st.markdown(eval_card_html("⚡","Exc. Power",      power_val,"W/kg", power_pos_mean),                       unsafe_allow_html=True)
with e3:
    st.markdown(eval_card_html("📈","RSI-m",           rsi_val,  "m/s",  rsi_pos_mean,   dec=2),                unsafe_allow_html=True)
with e4:
    st.markdown(eval_card_html("🦵","Fza Isquio Der",  r_force,  "N",    r_pos_mean,     dec=0, extra_class=der_class), unsafe_allow_html=True)
with e5:
    st.markdown(eval_card_html("🦵","Fza Isquio Izq",  l_force,  "N",    l_pos_mean,     dec=0, extra_class=izq_class), unsafe_allow_html=True)
with e6:
    st.markdown(eval_card_html("⚖️","Dif % Der/Izq",   dif_val,  "%",    None),                                 unsafe_allow_html=True)

# ── Debug compacto: siempre visible para admin, colapsado ─
with st.expander("🔍 Debug evaluaciones — expandir para verificar"):
    st.caption("**CMJ**")
    st.write({
        "cmj_col": cmj_col, "power_col": power_col, "rsi_col": rsi_col,
        "cmj_val": cmj_val, "power_val": power_val, "rsi_val": rsi_val,
        "filas": len(cmj_j),
    })
    if not cmj_j.empty:
        st.write("Columnas CMJ:", list(cmj_j.columns))
        st.dataframe(cmj_j[[c for c in [cmj_col, power_col, rsi_col] if c]].head(3))
    st.caption("**Nórdico**")
    st.write({"r_col": r_col, "l_col": l_col, "r_force": r_force, "l_force": l_force, "filas": len(nord_j)})

# ==========================================================
# PDF — FIX 4: exporta todo el reporte con diseño
# ==========================================================
st.markdown("<div class='section-title'>Exportación</div>", unsafe_allow_html=True)

# ── Generar reporte HTML descargable ──────────────────────────────────
def _fmt(v, suf="", dec=1):
    if v is None: return "Sin dato"
    try:
        if pd.isna(v): return "Sin dato"
    except Exception: pass
    return f"{v:.{dec}f} {suf}".strip()

def _delta_html(v, ref, suf="", dec=1):
    if v is None or ref is None: return ""
    try:
        if pd.isna(v) or pd.isna(ref) or ref == 0: return ""
    except Exception: return ""
    pct = (v - ref) / ref * 100
    c = "#10f2a0" if pct >= 0 else "#ff6b6b"
    s = "+" if pct >= 0 else ""
    return f'<span style="color:{c};font-weight:900;">{s}{pct:.1f}%</span> <span style="color:#64748b;font-size:10px;">vs prom. pos.</span>'

# Tarjetas GPS
gps_cards_html = ""
metricas_rep = [
    ("⏱️","MIN","MIN","min"), ("📏","Dist. Total","TOT DIST","m"),
    ("🏃","MTS/MIN","MTS/MIN","m/min"), ("🔥",">19 km/h","HSD","m"),
    ("⚡",">24 km/h","SPD","m"), ("🚀","V-MAX","V-MAX","km/h"),
]
for ico, tit, col, uni in metricas_rep:
    v = val_num(gps_jugador, col, "max") if col in gps_jugador.columns else None
    r = val_num(ref_pos, col, "mean") if col in ref_pos.columns else None
    v_txt = f"{v:,.0f} {uni}" if v is not None and not (isinstance(v,float) and pd.isna(v)) else "Sin dato"
    gps_cards_html += f"""
    <div style="background:#0d1a2e;border:1px solid rgba(37,99,235,.25);border-radius:14px;
                padding:12px 14px;flex:1;min-width:0;">
      <div style="font-size:8px;color:#93c5fd;letter-spacing:1.5px;text-transform:uppercase;font-weight:900;">{tit}</div>
      <div style="font-size:24px;color:#fff;font-weight:900;margin:4px 0;line-height:1;">{v_txt}</div>
      <div style="font-size:11px;margin-top:2px;">{_delta_html(v,r,uni)}</div>
      <div style="font-size:9px;color:#64748b;margin-top:2px;">PROM: {_fmt(r,uni)}</div>
    </div>"""

# Tabla partidos
tabla_rows_html = ""
for _, row in tabla.iterrows():
    tabla_rows_html += "<tr>" + "".join(
        f'<td style="padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.06);text-align:center;">{row[c]}</td>'
        for c in tabla.columns
    ) + "</tr>"

tabla_headers_html = "".join(
    f'<th style="padding:7px 10px;color:#2563eb;font-weight:900;font-size:11px;'
    f'letter-spacing:1px;text-align:center;border-bottom:2px solid rgba(37,99,235,.4);">{c}</th>'
    for c in tabla.columns
)

# Lesiones
les_rows_html = ""
cols_show_rep = [c for c in ["FECHA","LESION","REGION","DAY_OFF_DXT_DISPLAY"] if c in les.columns]
les_rep = les[cols_show_rep].copy()
if "FECHA" in les_rep.columns:
    les_rep["FECHA"] = les_rep["FECHA"].dt.strftime("%d/%m/%Y")
les_rep = les_rep.rename(columns={"DAY_OFF_DXT_DISPLAY":"DÍAS BAJA"})
for _, row in les_rep.iterrows():
    es_r = "recuperación" in str(row.get("DÍAS BAJA","")).lower()
    les_rows_html += "<tr>" + "".join(
        f'<td style="padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.06);'
        f'{"color:#fbbf24;font-style:italic;" if (c=="DÍAS BAJA" and es_r) else ""}'
        f'text-align:{"left" if c in ["LESION","REGION"] else "center"};">{v}</td>'
        for c, v in row.items()
    ) + "</tr>"

les_headers_html = "".join(
    f'<th style="padding:7px 10px;color:#2563eb;font-weight:900;font-size:11px;'
    f'letter-spacing:1px;text-align:center;border-bottom:2px solid rgba(37,99,235,.4);">{c}</th>'
    for c in les_rep.columns
)

# Evaluaciones físicas
eval_data = [
    ("🏋️","Mejor CMJ", cmj_val, "cm", cmj_pos_mean, 1),
    ("⚡","Exc. Power", power_val, "W/kg", power_pos_mean, 1),
    ("📈","RSI-m", rsi_val, "m/s", rsi_pos_mean, 2),
    ("🦵","Fza Isq. Der", r_force, "N", r_pos_mean, 0),
    ("🦵","Fza Isq. Izq", l_force, "N", l_pos_mean, 0),
    ("⚖️","Dif % Der/Izq", dif_val, "%", None, 1),
]
eval_cards_html = ""
for ico, lbl, v, uni, ref_v, d in eval_data:
    pct_txt = _delta_html(v, ref_v, uni, d) if ref_v else '<span style="color:#475569;font-size:10px;">SIN REF.</span>'
    prom_txt = f'<div style="font-size:9px;color:#64748b;margin-top:2px;">PROM: {_fmt(ref_v,uni,d)}</div>' if ref_v else ""
    eval_cards_html += f"""
    <div style="background:#0d1a2e;border:1px solid rgba(37,99,235,.25);border-radius:14px;
                padding:12px 14px;flex:1;min-width:0;">
      <div style="font-size:8px;color:#93c5fd;letter-spacing:1.5px;text-transform:uppercase;font-weight:900;">{lbl}</div>
      <div style="font-size:20px;color:#fff;font-weight:900;margin:4px 0;line-height:1;">{_fmt(v,uni,d)}</div>
      <div style="font-size:11px;margin-top:2px;">{pct_txt}</div>
      {prom_txt}
    </div>"""

escudo_b64_rep = img_to_base64(ESCUDO_PATH)
escudo_img_rep = f'<img src="data:image/png;base64,{escudo_b64_rep}" style="height:60px;object-fit:contain;">' if escudo_b64_rep else "🛡️"

foto_b64_rep = img_to_base64(foto_path) if foto_path else None
foto_img_rep = f'<img src="data:image/png;base64,{foto_b64_rep}" style="width:90px;height:90px;object-fit:cover;border-radius:14px;border:2px solid rgba(37,99,235,.5);">' if foto_b64_rep else '<div style="width:90px;height:90px;border-radius:14px;background:#111827;display:flex;align-items:center;justify-content:center;font-size:36px;">👤</div>'

html_reporte = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte {jugador} {anio} - Club A. Unión</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#07101f;color:#e8ecf4;font-family:'Inter',sans-serif;font-size:12px;}}
@media print{{
  *{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;}}
  .no-print{{display:none!important;}}
  @page{{size:A4 landscape;margin:10mm 12mm;}}
  body{{font-size:10px;}}
}}
.container{{max-width:1200px;margin:0 auto;padding:16px 20px;}}
.header{{display:flex;align-items:center;justify-content:space-between;
         border-bottom:3px solid #1e40af;padding-bottom:10px;margin-bottom:16px;}}
.club-title{{font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:4px;color:#fff;}}
.section-title{{font-size:14px;font-weight:900;color:#fff;margin:16px 0 8px 0;
                border-left:4px solid #2563eb;padding-left:8px;letter-spacing:.5px;}}
.player-card{{display:grid;grid-template-columns:100px 1fr 200px 90px;gap:14px;
              align-items:center;background:linear-gradient(135deg,rgba(13,26,46,.98),rgba(17,28,53,.95));
              border:1px solid rgba(255,255,255,.11);border-radius:18px;padding:16px 18px;margin-bottom:14px;}}
.player-name{{font-family:'Bebas Neue',sans-serif;font-size:42px;color:#fff;line-height:.95;}}
.player-sub{{color:#3b82f6;letter-spacing:3px;font-size:11px;text-transform:uppercase;font-weight:900;margin-bottom:6px;}}
.chip{{display:inline-block;padding:4px 9px;margin:3px 3px 0 0;border-radius:999px;
       background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);font-size:11px;font-weight:700;}}
.cards-row{{display:flex;gap:8px;margin-bottom:14px;}}
table{{width:100%;border-collapse:collapse;background:rgba(13,26,46,.96);
       border-radius:12px;overflow:hidden;margin-bottom:14px;}}
thead tr{{background:rgba(37,99,235,.10);}}
tbody tr:nth-child(even){{background:rgba(255,255,255,.02);}}
.print-btn{{display:block;width:100%;padding:12px;margin-bottom:14px;
            background:linear-gradient(135deg,#2563eb,#1e40af);color:#fff;
            border:none;border-radius:10px;font-size:15px;font-weight:900;
            cursor:pointer;letter-spacing:1px;}}
.footer{{text-align:center;color:#475569;font-size:10px;margin-top:16px;
         padding-top:10px;border-top:1px solid rgba(255,255,255,.08);}}
</style>
</head>
<body>
<div class="container">

  <!-- BOTÓN IMPRIMIR (solo visible en pantalla) -->
  <button class="print-btn no-print" onclick="window.print()">🖨️ &nbsp; GUARDAR COMO PDF (Ctrl+P)</button>
  <p class="no-print" style="text-align:center;color:#64748b;font-size:11px;margin-bottom:14px;">
    En el diálogo: <b>Destino → Guardar como PDF</b> · Activar <b>"Gráficos en segundo plano"</b>
  </p>

  <!-- ENCABEZADO -->
  <div class="header">
    <div>
      <div class="club-title">CLUB A. UNIÓN</div>
      <div style="color:#94a3b8;font-size:11px;">TABLERO RESUMEN INDIVIDUAL · Rendimiento Físico</div>
    </div>
    <div style="text-align:right;">
      {escudo_img_rep}
      <div style="color:#94a3b8;font-size:10px;margin-top:4px;">Generado: {date.today().strftime('%d/%m/%Y')}</div>
    </div>
  </div>

  <!-- JUGADOR -->
  <div class="player-card">
    <div>{foto_img_rep}</div>
    <div>
      <div class="player-sub">{nac_label} · {posicion}</div>
      <div class="player-name">{jugador}</div>
      <div style="margin-top:6px;">
        <span class="chip">🎂 {fecha_nac_formato}</span>
        <span class="chip">Edad: {edad}</span>
        <span class="chip">📏 {altura}</span>
        <span class="chip">⚽ {posicion}</span>
      </div>
      <div style="margin-top:6px;">
        <span style="padding:6px 14px;border-radius:12px;margin-right:8px;font-weight:800;font-size:12px;
                     {"background:linear-gradient(135deg,rgba(37,99,235,.5),rgba(30,64,175,.35));border:2px solid #2563eb;color:#fff;" if es_izq else "background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:rgba(255,255,255,.25);}"}">
          👟 IZQ</span>
        <span style="padding:6px 14px;border-radius:12px;font-weight:800;font-size:12px;
                     {"background:linear-gradient(135deg,rgba(37,99,235,.5),rgba(30,64,175,.35));border:2px solid #2563eb;color:#fff;" if es_der else "background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:rgba(255,255,255,.25);}"}">
          👟 DER</span>
      </div>
    </div>
    <div style="display:flex;align-items:center;justify-content:center;">{campo_html}</div>
    <div></div>
  </div>

  <!-- TARJETAS GPS -->
  <div class="section-title">Tarjetas resumen | Mejor valor vs promedio posición +70'</div>
  <div class="cards-row">{gps_cards_html}</div>

  <!-- TABLA PARTIDOS -->
  <div class="section-title">Últimos {n_partidos} partidos seleccionados</div>
  <table>
    <thead><tr>{tabla_headers_html}</tr></thead>
    <tbody>{tabla_rows_html}</tbody>
  </table>

  <!-- DISPONIBILIDAD -->
  <div class="section-title" style="page-break-before:always;">Disponibilidad y lesiones</div>
  <div style="display:flex;gap:10px;margin-bottom:10px;">
    <div style="flex:1;background:#0d1a2e;border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:12px;">
      <div style="font-size:10px;color:#93c5fd;font-weight:900;">🩺 DÍAS PERDIDOS</div>
      <div style="font-size:28px;color:#fff;font-weight:900;">{dias_perdidos}</div>
      {"<div style='color:#ff6b6b;font-weight:700;font-size:11px;'>🔴 Nueva lesión en TTO</div>" if hay_lesion_activa else ""}
    </div>
    <div style="flex:1;background:#0d1a2e;border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:12px;">
      <div style="font-size:10px;color:#93c5fd;font-weight:900;">⚠️ LESIONES</div>
      <div style="font-size:28px;color:#fff;font-weight:900;">{len(les)}</div>
    </div>
    <div style="flex:1;background:#0d1a2e;border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:12px;">
      <div style="font-size:10px;color:#93c5fd;font-weight:900;">📌 N° LESIONES AÑO</div>
      <div style="font-size:28px;color:#fff;font-weight:900;">{len(les)}</div>
    </div>
  </div>
  {"<div style='margin-bottom:8px;'><span style='font-size:9px;color:#94a3b8;font-weight:700;letter-spacing:2px;text-transform:uppercase;'>🔴 EN TRATAMIENTO</span><br><span style='padding:6px 14px;border-radius:10px;background:rgba(255,107,107,.15);border:1px solid rgba(255,107,107,.4);color:#fca5a5;font-size:13px;font-weight:700;display:inline-block;margin-top:4px;'>" + ultima_lesion_full + "</span></div>" if not les.empty else ""}
  <table>
    <thead><tr>{les_headers_html}</tr></thead>
    <tbody>{les_rows_html}</tbody>
  </table>

  <!-- EVALUACIONES FÍSICAS -->
  <div class="section-title">Evaluaciones físicas</div>
  <div class="cards-row">{eval_cards_html}</div>

  <!-- FOOTER -->
  <div class="footer">
    Documento generado el {date.today().strftime('%d/%m/%Y')} · CLUB A. UNIÓN · Área de Rendimiento Físico · Mag. Sebastián Villalba · Año {anio}
  </div>

</div>
</body>
</html>"""

html_bytes = html_reporte.encode("utf-8")
st.download_button(
    label="📄  Descargar Reporte (HTML → abrir → Ctrl+P → Guardar como PDF)",
    data=html_bytes,
    file_name=f"reporte_{jugador}_{anio}.html",
    mime="text/html",
    use_container_width=True,
)
st.caption("💡 Abrí el archivo descargado en Chrome → Ctrl+P → Destino: Guardar como PDF → Activar 'Gráficos en segundo plano'")