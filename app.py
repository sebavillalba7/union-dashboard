
## IMPORTAR LIBRERIAS

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import numpy as np
import base64
import requests
from fpdf import FPDF
from dotenv import load_dotenv
import os

# EN ESTA PRIMERA LINEA CARGAMOS EL ARCHIVO QUE CONTIENE LA API PARA CONECTARNOS A LOS DATOS DE FUTBOL (https://www.api-football.com/) , QUE ESTA CONTENIDO EN LA CARPETA .env
load_dotenv()  # Esto carga las variables del archivo .env
API_KEY = os.getenv("API_KEY")
headers = {"x-apisports-key": API_KEY}


# ESTE PRIMER PASO ES PARA GENERAR LA PAGINA DE PDF QUE LUEGO SERA EXPORTADA
def exportar_partidos_pdf(df_partidos, jugador):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Resumen Físico Individual - {jugador}", ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Arial", "", 10)
    
    # Si hay datos, agregamos la tabla
    if not df_partidos.empty:
        # Encabezado
        col_widths = [24] * len(df_partidos.columns)
        for i, col in enumerate(df_partidos.columns):
            pdf.set_fill_color(12, 242, 255)
            pdf.cell(col_widths[i], 8, col, border=1, align='C', fill=True)
        pdf.ln()
        # Filas
        for _, row in df_partidos.iterrows():
            for i, val in enumerate(row):
                pdf.set_fill_color(25, 37, 59)
                pdf.cell(col_widths[i], 8, str(val), border=1, align='C', fill=False)
            pdf.ln()
    else:
        pdf.cell(0, 10, "No hay datos de partidos oficiales para los filtros aplicados.", ln=True, align="L")
    
    # Guardar PDF
    filename = f"resumen_partidos_{jugador.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# ======= CONFIGURACIÓN MARDOWN GENERAL, BOTON DE CERRAR SESION y LOGIN PARA QUE FUNCIONE PUBLICADO POR STREAMLIT CLOUD=======
st.markdown(
    """
    <style>
    /* Selectbox cerrado: fondo blanco, texto oscuro */
    div[data-baseweb="select"] > div {
        background-color: #fff !important;   /* Fondo blanco */
        color: #212529 !important;           /* Texto oscuro */
        font-weight: bold;
        border-radius: 8px !important;
    }

    /* Selectbox abierto (menú): fondo blanco, texto oscuro */
    div[data-baseweb="popover"] {
        background-color: #fff !important;
        color: #212529 !important;
        border-radius: 8px !important;
    }

    /* Opciones del menú: texto oscuro sobre fondo blanco */
    div[data-baseweb="option"] {
        background-color: #fff !important;
        color: #212529 !important;
        font-weight: bold;
    }
    /* Opción seleccionada (hover o activa) */
    div[data-baseweb="option"]:hover {
        background-color: #f0f0f0 !important;  /* Gris claro */
        color: #212529 !important;
    }
    div[data-baseweb="option"][aria-selected="true"] {
        background-color: #e0e0e0 !important;  /* Gris un poco más oscuro para la seleccionada */
        color: #212529 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    /* Mejora visibilidad del botón Cerrar Sesión en sidebar */
    button[kind="secondary"] {
        color: #212529 !important;           /* Texto oscuro */
        background-color: #fff !important;   /* Fondo blanco */
        border: 2px solid #0cf2ff !important;/* Borde celeste */
        border-radius: 10px !important;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: 0.2s;
    }
    button[kind="secondary"]:hover {
        background-color: #e0f7fa !important;/* Fondo celeste suave en hover */
        color: #212529 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    /* Campo de texto del login */
    input[type="text"], input[type="password"] {
        color: #212529 !important;              /* Texto oscuro */
        background-color: #fff !important;      /* Fondo blanco */
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid #0cf2ff !important;   /* Borde celeste, opcional */
        padding: 8px;
    }
    /* Placeholder del input (texto por defecto) */
    input[type="text"]::placeholder,
    input[type="password"]::placeholder {
        color: #888 !important;                 /* Gris medio */
        opacity: 1;
        font-weight: normal;
    }
    /* Botón de login */
    button[kind="primary"] {
        background-color: #0cf2ff !important;   /* Botón celeste */
        color: #102542 !important;              /* Texto azul oscuro */
        border-radius: 8px;
        font-weight: bold;
    }
    button[kind="primary"]:hover {
        background-color: #0ae0e0 !important;   /* Celeste más fuerte */
        color: #102542 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======= CONFIGURACIÓN GENERAL =======

st.set_page_config(page_title="Panel Deportivo", page_icon="🏃‍♂️", layout="wide")

# ======= ESTILOS PERSONALIZADOS CSS =======

custom_css = """
<style>
/* Fondo principal */
.stApp {
    background-color: #102542 !important;
}
/* Fondo Sidebar */
[data-testid="stSidebar"] {
    background-color: #f7f8fa;
}
.sidebar-content {
    background-color: #f7f8fa !important;
}


/* Logo centrado */
#logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 16px;
    margin-bottom: 16px;
}

/* Bienvenida centrada */
#bienvenido-container {
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Botón cerrar sesión */
#logout-container {
    display: flex;
    font-weight: bold;
    justify-content: center;
    align-items: center;
    margin-top: 80px;
}

/* Selectbox estilos */
.stSelectbox > div {
    color: #102542 !important;
    font-weight: bold;
}

/* Cambiar el color de todos los labels de los selectbox */
label, .stSelectbox label {
    color: #FFF !important;
    font-size: 1.15rem !important;
    font-weight: bold !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase;
}

/* Títulos de página */
.title-main {
    color: #0cf2ff;
    font-size: 3.3rem;
    font-weight: bold;
    text-align: center;
    letter-spacing: 1px;
}

/* Subtítulos */
.subtitle {
    color: #0cf2ff;
    font-size: 2.2rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 18px;
    letter-spacing: 0.5px;
}

/* Filtros */
.filter-label {
    color: #FFF !important;
    font-size: 1.1rem;
    font-weight: bold;
    letter-spacing: 1px;
}

.stDataFrame th, .stDataFrame td {
    color: #FFF !important;
}

/* Cards métricas */
.metric-card {
    background: #19253b;
    padding: 20px 8px;
    border-radius: 18px;
    margin: 8px;
    min-width: 120px;
    text-align: center;
    box-shadow: 0 3px 16px 0 rgba(12,242,255,0.1);
}
.metric-title {
    color: #0cf2ff;
    font-size: 1.1rem;
    font-weight: bold;
    text-align: center;
}
.metric-value {
    color: #FFF;
    font-size: 2.2rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 6px;
}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ======= INICIO DE SESION =======
credentials = {
    "usernames": {
        "admin": {
            "name": "Sebastián Villalba",
            "password": "$2b$12$Lu6KTSaOFEnoR5RDmZgvn.DpTve.NwyOoXK1y/pOWBWeLAonL.KaW",
            "role": "admin"
        }
    }
}
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="my_cookie",
    key="abcdef",
    cookie_expiry_days=1
)

# Mostrar logo centrado en login
st.markdown("""
    <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 1px;'>
        <img src='data:image/png;base64,{}' width='300'/>
    </div>
""".format(base64.b64encode(open("assets/logo.png", "rb").read()).decode()), unsafe_allow_html=True)

# DARLE FORMATO AL LA PAGINA DE INGRESO "LOGIN"
st.markdown("""
<style>
.stApp form > p:first-of-type {
    color: #fff !important;
    font-weight: bold !important;
    font-size: 2.2rem !important;
    text-align: center !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    margin-bottom: 2.2rem !important;
    margin-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

name, authentication_status, username = authenticator.login('INICIAR SESÓN', 'main')

if authentication_status is False:
    st.error('Usuario/Contraseña incorrectos')
elif authentication_status is None:
    st.warning('Por favor, ingresa usuario y contraseña')
elif authentication_status:
    # ==== SIDEBAR PERSONALIZADO ====
    with st.sidebar:
        st.markdown('<div id="logo-container">', unsafe_allow_html=True)
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
            st.markdown(
                f"<img src='data:image/png;base64,{encoded}' width='150' style='display: block; margin-left: auto; margin-right: auto;'/>",
                unsafe_allow_html=True
            )
        else:
            st.info("No se encontró el logo")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div id="bienvenido-container">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:#04d463;'>Bienvenido</h2>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:#04d463;'>{name}</h4>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        pagina = st.selectbox("Selecciona la página", ["🏃‍♂️ DATOS FISICOS", "⚽ DATOS FUTBOLISTICOS", "📈 RESUMEN"], key="page_selector")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<span style='color:#07cf48;font-weight:600;'>By Mag. Sebastián Villalba</span>", unsafe_allow_html=True)
        st.markdown('<div id="logout-container">', unsafe_allow_html=True)
        authenticator.logout('Cerrar Sesión', 'sidebar')
        st.markdown('</div>', unsafe_allow_html=True)

    # ================== PAGINA 1: DATOS FISICOS (USO DE BASE DE DATOS DESDE GOOGLE SHEET) =====================
    if pagina.startswith("🏃‍♂️"):
        st.markdown('<div class="title-main">🏃‍♂️ DATOS FISICOS</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Filtros avanzados</div>', unsafe_allow_html=True)

        # --- Cargar Google Sheet -- ## USO DE CACHE:Esto asegura que los datos no se descargan de nuevo cada vez que un usuario interactúa con la app, 
                                        ## mejorando la eficiencia y la velocidad.
        @st.cache_data(show_spinner="Conectando a Google Sheets...")
        def cargar_gsheet():
            url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS5rtNSfkU6OaYmPWb-OeGfV7xfuHce2G76mArU-6HfldXAUAF8fErz20Lo9FyR6Fb9bBQdQsHNwgw_/pub?gid=0&single=true&output=csv"
            df = pd.read_csv(url, dtype=str)
            # Corrige la fecha para d/m/Y
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
            return df

        df = cargar_gsheet()
        # --- Configuración de filtros avanzados ---
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        with col1:
            temporadas = df['TEMP'].dropna().unique().tolist()
            temp_filter = st.selectbox('TEMPORADA', options=['Todos'] + temporadas, key="temp_filter")
        with col2:
            fechas = df['FECHA'].dropna().unique().tolist()
            fecha_filter = st.selectbox('FECHA', options=['Todas'] + fechas, key="fecha_filter")
        with col3:
            entrenadores = df['ENT'].dropna().unique().tolist()
            ent_filter = st.selectbox('ENTRENADOR', options=['Todos'] + entrenadores, key="ent_filter")
        with col4:
            jugadores = df['JUGADOR'].dropna().unique().tolist()
            jugador_filter = st.selectbox('JUGADOR', options=['Todos'] + jugadores, key="jugador_filter")
        with col5:
            posiciones = df['POS'].dropna().unique().tolist()
            pos_filter = st.selectbox('POSICIÓN', options=['Todas'] + posiciones, key="pos_filter")
        with col6:
            sesion = df['SES'].dropna().unique().tolist()
            ses_filter = st.selectbox('SES/PARTIDO', options=['Todos'] + sesion, key="ses_filter")
        with col7:
            rivales = df['RIVAL'].dropna().unique().tolist()
            rival_filter = st.selectbox('RIVAL', options=['Todos'] + rivales, key="rival_filter")
        with col8:
            resultado = df['RES'].dropna().unique().tolist()
            res_filter = st.selectbox('RESULTADO', options=['Todos'] + resultado, key="res_filter")

        # --- FILTROS DINAMICOS ---#
        df_filt = df.copy()
        if temp_filter != "Todos":
            df_filt = df_filt[df_filt['TEMP'] == temp_filter]
        if fecha_filter != "Todas":
            df_filt = df_filt[df_filt['FECHA'] == fecha_filter]
        if ent_filter != "Todos":
            df_filt = df_filt[df_filt['ENT'] == ent_filter]
        if jugador_filter != "Todos":
            df_filt = df_filt[df_filt['JUGADOR'] == jugador_filter]
        if pos_filter != "Todas":
            df_filt = df_filt[df_filt['POS'] == pos_filter]
        if ses_filter != "Todos":
            df_filt = df_filt[df_filt['SES'] == ses_filter]
        if rival_filter != "Todos":
            df_filt = df_filt[df_filt['RIVAL'] == rival_filter]
        if res_filter != "Todos":
            df_filt = df_filt[df_filt['RES'] == res_filter]

        st.dataframe(df_filt, use_container_width=True)

        # ---- GRAFICO 1: PROMEDIO POR TEMPORADA  ----
        st.markdown('<div class="subtitle">Promedio físico por temporada (PARTIDOS)</div>', unsafe_allow_html=True)
        df_partidos = df[df['SES'] == 'PARTIDO'].copy()
        # Convierte los valores a float, corrige decimales con coma
        def safe_float(x):
            try:
                return float(str(x).replace(",", "."))
            except:
                return np.nan
        metrics = ['TOT DIST','MTS>19 KM/H','MTS > 24 KM/H']
        for m in metrics:
            df_partidos[m] = df_partidos[m].apply(safe_float)
        temp_stats = df_partidos.groupby('TEMP')[metrics].mean().reset_index()
        fig = px.bar(temp_stats, x="TEMP", y=metrics, barmode='group',
                     labels={"value":"Promedio", "variable":"Métrica"},
                     text_auto='.2f')
        fig.update_layout(
            plot_bgcolor='#152542',
            paper_bgcolor='#152542',
            font=dict(color='#0cf2ff', family='Roboto', size=16),
            xaxis_title="TEMPORADA",
            yaxis_title="Promedio",
            title=None,
            legend=dict(font=dict(color="white", size=16)),
        )
        for trace in fig.data:
            trace.marker.line.width = 2
            trace.marker.line.color = "#FFF"
        st.plotly_chart(fig, use_container_width=True)

    # ================== PAGINA 2: DATOS FUTBOLISTICOS (USO DE API) =====================
    elif pagina.startswith("⚽"):
        st.markdown('<div class="title-main">⚽ DATOS FUTBOLISTICOS</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Estadísticas actualizadas vía API de fútbol argentino.</div>', unsafe_allow_html=True)
        # Filtros:
        # TEMP, FECHA, JUGADOR
        TEAM_ID_UNION_SF = 441

        def get_jugadores_union(team_id, temporadas):
            jugadores_total = []
            api_error = ""
            for season in temporadas:
                url = f"https://v3.football.api-sports.io/players?team={team_id}&season={season}"
                response = requests.get(url, headers=headers)
                try:
                    data = response.json()
                    if "errors" in data and data["errors"]:
                        api_error = str(data["errors"])
                        continue
                    for item in data["response"]:
                        jugador = {
                            "Nombre": item["player"]["name"],
                            "Edad": item["player"]["age"],
                            "Posición": item["statistics"][0]["games"]["position"],
                            "Temporada": season,
                            "Partidos": item["statistics"][0]["games"]["appearences"],
                            "Titular": item["statistics"][0]["games"]["lineups"],
                            "Goles": item["statistics"][0]["goals"]["total"],
                            "Asistencias": item["statistics"][0]["goals"]["assists"],
                            "Minutos": item["statistics"][0]["games"]["minutes"],
                        }
                        jugadores_total.append(jugador)
                except Exception as ex:
                    api_error = str(ex)
            return pd.DataFrame(jugadores_total), api_error

        temporadas = ['2021','2022','2023']
        df_jugadores, api_error = get_jugadores_union(TEAM_ID_UNION_SF, temporadas)
        temp_opts = df_jugadores['Temporada'].dropna().unique().tolist() if not df_jugadores.empty else []
        jugador_opts = df_jugadores['Nombre'].dropna().unique().tolist() if not df_jugadores.empty else []
        fecha_opts = []
        col1, col2, col3 = st.columns(3)
        with col1:
            temp_api = st.selectbox('TEMPORADA', options=['Todos']+temp_opts, key="temp_api")
        with col2:
            jugador_api = st.selectbox('JUGADOR', options=['Todos']+jugador_opts, key="jugador_api")
        with col3:
            st.markdown("")  # Espacio

        df_api_filt = df_jugadores.copy()
        if temp_api != "Todos":
            df_api_filt = df_api_filt[df_api_filt['Temporada'] == temp_api]
        if jugador_api != "Todos":
            df_api_filt = df_api_filt[df_api_filt['Nombre'] == jugador_api]

        if api_error:
            st.error(f"Error de la API: {api_error}")
        elif not df_api_filt.empty:
            st.dataframe(df_api_filt, use_container_width=True)
        else:
            st.warning("No se encontraron datos de jugadores (puede ser por límite de API, error de clave o temporada sin datos).")

    # ================== PAGINA 3: RESUMEN INDIVIDUAL =====================
    elif pagina.startswith("📈"):
        st.markdown('<div class="title-main">📈 RESUMEN FISICO INDIVIDUAL</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Filtros</div>', unsafe_allow_html=True)
        # --- Filtros: TEMP, FECHA, JUGADOR, RIVAL ---
        @st.cache_data(show_spinner="Conectando a Google Sheets...")
        def cargar_gsheet():
            url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS5rtNSfkU6OaYmPWb-OeGfV7xfuHce2G76mArU-6HfldXAUAF8fErz20Lo9FyR6Fb9bBQdQsHNwgw_/pub?gid=0&single=true&output=csv"
            df = pd.read_csv(url, dtype=str)
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
            return df

        df = cargar_gsheet()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            temp_opts = df['TEMP'].dropna().unique().tolist()
            temp_f = st.selectbox('TEMPORADA', options=['Todos'] + temp_opts, key="resum_temp")
        with col2:
            fecha_opts = df['FECHA'].dropna().unique().tolist()
            fecha_f = st.selectbox('FECHA', options=['Todas'] + fecha_opts, key="resum_fecha")
        with col3:
            jugador_opts = df['JUGADOR'].dropna().unique().tolist()
            jugador_f = st.selectbox('JUGADOR', options=jugador_opts, key="resum_jug")
        with col4:
            rival_opts = df['RIVAL'].dropna().unique().tolist()
            rival_f = st.selectbox('RIVAL', options=['Todos'] + rival_opts, key="resum_riv")

        df_filt = df.copy()
        if temp_f != "Todos":
            df_filt = df_filt[df_filt['TEMP'] == temp_f]
        if fecha_f != "Todas":
            df_filt = df_filt[df_filt['FECHA'] == fecha_f]
        if jugador_f:
            df_filt = df_filt[df_filt['JUGADOR'] == jugador_f]
        if rival_f != "Todos":
            df_filt = df_filt[df_filt['RIVAL'] == rival_f]

        # -------- TARJETAS DE  PROMEDIO DE PARTIDOS ------------
        st.markdown('<div class="subtitle">PROMEDIOS PARTIDOS OFICIALES</div>', unsafe_allow_html=True)
        metricas = [
            ("MIN", "MIN"), ("TOT DIST", "TOT DIST"), ("MTS/MIN", "MTS/MIN"),
            ("MTS 16-19 KM/H", "MTS 16-19 KM/H"), ("MTS 19-24 KM/H", "MTS 19-24 KM/H"),
            ("MTS > 24 KM/H", "MTS > 24 KM/H"), ("#SP24", "#SP24"),
            ("MTS>19 KM/H", "MTS>19 KM/H"), ("ACEL", "ACEL"), ("DES", "DES")
        ]
        df_partidos = df_filt[df_filt['SES'] == 'PARTIDO'].copy()
        def tofloat(x):
            try:
                return float(str(x).replace(",", "."))
            except:
                return np.nan
        for m, col in metricas:
            if col in df_partidos.columns:
                df_partidos[col] = df_partidos[col].apply(tofloat)
        
        card_cols_1 = st.columns(5)
        card_cols_2 = st.columns(5)
        for i in range(5):
            m, col = metricas[i]
            valor = df_partidos[col].mean() if col in df_partidos.columns and not df_partidos.empty else 0
            card_cols_1[i].markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">{m}</div>
                    <div class="metric-value">{valor:,.2f}</div>
                </div>
                """, unsafe_allow_html=True
            )
        for i in range(5, 10):
            m, col = metricas[i]
            valor = df_partidos[col].mean() if col in df_partidos.columns and not df_partidos.empty else 0
            card_cols_2[i-5].markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">{m}</div>
                    <div class="metric-value">{valor:,.2f}</div>
                </div>
                """, unsafe_allow_html=True
            )

        # --------- DATOS DE PARTIDOS ---------
        st.markdown('<div class="subtitle" style="text-align:left;">Detalle de partidos</div>', unsafe_allow_html=True)
        if not df_partidos.empty:
            st.dataframe(df_partidos, use_container_width=True)
        else:
            st.info("No hay datos de partidos oficiales para los filtros aplicados.")

        # --------- GRAFICA: MINUTOS JUGADOS CON CADA ENTRENADOR ---------
        st.markdown('<div class="subtitle" style="text-align:left;">MINUTOS JUGADOS POR ENTRENADOR</div>', unsafe_allow_html=True)
        # Todos los minutos del jugador filtrado por entrenador
        if jugador_f:
            df_jugador_all = df[df['JUGADOR'] == jugador_f].copy()
            df_jugador_all['MIN'] = df_jugador_all['MIN'].apply(tofloat)
            minutos_ent = df_jugador_all.groupby('ENT')['MIN'].sum().reset_index()
            fig = px.bar(
                minutos_ent, x="ENT", y="MIN", text_auto=True,
                labels={"ENT": "Entrenador", "MIN": "Minutos"},
                color="MIN", color_continuous_scale="blues"
            )
            fig.update_traces(marker_line_color='#FFF', marker_line_width=2, textfont=dict(color="white", size=15))
            fig.update_layout(
                plot_bgcolor='#152542',
                paper_bgcolor='#152542',
                font=dict(color='#0cf2ff', family='Roboto', size=16),
                xaxis_title="Entrenador",
                yaxis_title="Minutos jugados",
                legend=dict(font=dict(color="white", size=16)),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # --------- EXPORTAR A PDF ---------
        if not df_partidos.empty:
            pdf_path = None
            if st.button("⬇️ Exportar resumen a PDF"):
                with st.spinner("Generando PDF..."):
                    pdf_path = exportar_partidos_pdf(df_partidos, jugador_f)
                if pdf_path:
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Descargar PDF",
                            data=pdf_file,
                            file_name=f"resumen_partidos_{jugador_f}.pdf",
                            mime="application/pdf"
                        )
    # ============ FOOTER ============
    st.markdown(
        """
        <hr style="border: 1px solid #0cf2ff;">
        <center>
            <small style="color:#04d463;">
                App desarrollada por <b>Mag. Sebastián Villalba</b> | Powered by Streamlit & API Sports
            </small>
        </center>
        """, unsafe_allow_html=True
    )
