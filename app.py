# app.py — Evaluación Cognitiva en Streamlit (export HTML + config)
# Autor: ChatGPT (para Dante)
# Requisitos: streamlit  (sin pandas, sin micropip)
# Ejecutar:  streamlit run app.py

import sys
import csv
import io
import base64
import random
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from datetime import datetime, date

import streamlit as st

st.set_page_config(page_title="Evaluación Cognitiva", page_icon="🧠", layout="wide")
st.title("🧠 Evaluación Cognitiva — Prototipo Clínico")
st.caption("Prototipo educativo. No reemplaza una evaluación médica profesional.")

# ------------------------------------------------------------
# UTILIDADES BÁSICAS
# ------------------------------------------------------------

def normalize_list(txt: str) -> List[str]:
    return [t.strip().lower() for t in txt.split(",") if t.strip()]


def count_matches(user_words: List[str], target_words: List[str]) -> int:
    target = [w.lower() for w in target_words]
    return sum(1 for w in user_words if w in target)


def file_to_base64(uploaded_file) -> Optional[str]:
    if not uploaded_file:
        return None
    data = uploaded_file.read()
    return base64.b64encode(data).decode("utf-8")


# ------------------------------------------------------------
# BANCO DE PALABRAS (DEFAULT)
# ------------------------------------------------------------
DEFAULT_WORD_BANK = [
    ["manzana", "llave", "libro", "perro", "puente"],
    ["café", "planta", "reloj", "silla", "calle"],
    ["azul", "ventana", "lápiz", "camisa", "nube"],
]

if "target_words" not in st.session_state:
    st.session_state.target_words = random.choice(DEFAULT_WORD_BANK)
    st.session_state.registered_words = False
    st.session_state.registration_time = None


# ------------------------------------------------------------
# CONFIGURACIÓN (Sidebar)
# ------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    st.subheader("Paciente")
    id_paciente = st.text_input("ID/Historia Clínica")
    nombre = st.text_input("Nombre")
    fecha_eval = st.date_input("Fecha", value=date.today())

    st.divider()
    st.subheader("Parámetros de prueba")

    # Palabras objetivo
    st.markdown("**Palabras para memoria** (5 sugeridas por defecto)")
    custom_words_txt = st.text_input(
        "Palabras personalizadas (separe por coma)",
        placeholder="p.ej.: sol, mapa, tren, vaso, árbol",
    )
    colw1, colw2 = st.columns([1,1])
    with colw1:
        use_custom_words = st.checkbox("Usar palabras personalizadas", value=False)
    with colw2:
        if st.button("Aplicar palabras"):
            if use_custom_words and custom_words_txt.strip():
                st.session_state.target_words = normalize_list(custom_words_txt)
                st.session_state.registered_words = False
            else:
                st.session_state.target_words = random.choice(DEFAULT_WORD_BANK)
                st.session_state.registered_words = False

    st.caption("Palabras activas:")
    st.code(", ".join(st.session_state.target_words))

    st.markdown("**Fluidez (animales)**")
    animals_per_point = st.number_input("Animales por punto", min_value=1, max_value=10, value=5, step=1)
    max_fluency_points = st.number_input("Puntos máximos fluidez", min_value=1, max_value=10, value=4, step=1)

    st.markdown("**Umbrales de interpretación**")
    high_threshold = st.slider("% Alto rendimiento (≥)", min_value=50, max_value=100, value=90, step=1)
    mid_threshold = st.slider("% Leve compromiso (≥)", min_value=50, max_value=99, value=75, step=1)
    if mid_threshold >= high_threshold:
        st.warning("Sugerencia: ponga el umbral 'Leve' por debajo del 'Alto'.")

    st.markdown("**Puntajes máximos por dominio** (total sugerido: 46)")
    colm1, colm2 = st.columns(2)
    with colm1:
        max_ori = st.number_input("Orientación", 1, 20, 10)
        max_aten = st.number_input("Atención", 1, 20, 10)
        max_mem_inm = st.number_input("Memoria inmediata", 1, 10, 5)
        max_len = st.number_input("Lenguaje/Ejecutivo", 1, 20, 8)
    with colm2:
        max_viso = st.number_input("Visoconstrucción", 1, 10, 5)
        max_mem_dif = st.number_input("Memoria diferida", 1, 10, 3)
        max_abs = st.number_input("Abstracción", 1, 10, 4)

    MAXIMOS = {
        "Orientación": int(max_ori),
        "Atención": int(max_aten),
        "Memoria inmediata": int(max_mem_inm),
        "Lenguaje/Ejecutivo": int(max_len),
        "Visoconstrucción": int(max_viso),
        "Memoria diferida": int(max_mem_dif),
        "Abstracción": int(max_abs),
    }
    sum_max = sum(MAXIMOS.values())
    st.info(f"Total máximo actual: {sum_max}")

    st.divider()
    st.subheader("Reporte")
    logo_file = st.file_uploader("Logo (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=False)
    sig_nombre = st.text_input("Nombre y Apellido (firma)")
    sig_rol = st.text_input("Cargo/Profesión")
    sig_matricula = st.text_input("Matrícula (opcional)")

    st.divider()
    run_tests = st.checkbox("Ejecutar auto‑tests de scoring")
    st.caption("Los tests validan la lógica de puntajes sin paquetes externos.")


# ------------------------------------------------------------
# DOMINIOS (orden de render)
# ------------------------------------------------------------
DOMINIOS = [
    "Orientación",
    "Atención",
    "Memoria inmediata",
    "Lenguaje/Ejecutivo",
    "Visoconstrucción",
    "Memoria diferida",
    "Abstracción",
]

# Contenedor de respuestas
respuestas: Dict[str, Any] = {}

# ----- ORIENTACIÓN -----
with st.expander("Orientación", expanded=True):
    st.markdown("**Tiempo y lugar**")
    hoy = date.today()
    respuestas["ori_anio"] = st.number_input("Año actual", step=1, value=hoy.year)
    respuestas["ori_mes"] = st.selectbox("Mes actual", list(range(1, 13)), index=hoy.month - 1)
    respuestas["ori_dia"] = st.number_input("Día del mes", step=1, value=hoy.day)
    respuestas["ori_ciudad"] = st.text_input("Ciudad/Localidad")
    respuestas["ori_lugar"] = st.text_input("Lugar/Institución (p. ej., hospital, domicilio)")

# ----- ATENCIÓN -----
with st.expander("Atención", expanded=True):
    st.markdown("**Cálculo y series**")
    st.caption("Indique cinco resultados de restar 7 desde 100 (separados por coma). Ej.: 93,86,79,72,65")
    respuestas["aten_s7"] = st.text_input("Resta de 7 en 7 desde 100 (5 valores)")
    respuestas["aten_inversa"] = st.text_input("Deletree al revés la palabra 'casa' (ej.: 'asac')")

# ----- MEMORIA INMEDIATA -----
with st.expander("Memoria inmediata", expanded=True):
    st.markdown("**Registro y retención inmediata**")
    st.info("Lea las siguientes palabras y pídale al evaluado que las repita: ")
    st.subheader(", ".join(st.session_state.target_words))
    if st.button("Registrar palabras escuchadas ahora"):
        st.session_state.registered_words = True
        st.session_state.registration_time = datetime.now()
        st.success(
            "Palabras registradas. Continúe con el resto de la evaluación y recuerde pedirlas nuevamente al final."
        )
    respuestas["mem_inmediata"] = st.text_input("Anote las palabras que repitió (separadas por coma)")

# ----- LENGUAJE / EJECUTIVO -----
with st.expander("Lenguaje/Ejecutivo", expanded=True):
    st.markdown("**Fluidez y órdenes**")
    respuestas["len_animales"] = st.number_input("Cantidad de animales nombrados en 60 segundos", min_value=0, step=1)
    respuestas["len_frase"] = st.text_input("Escriba una frase con sujeto y predicado")
    st.caption("Órdenes de 3 pasos: Tome esta hoja, dóblela por la mitad y colóquela en la mesa.")
    respuestas["len_orden_ok"] = st.checkbox("Ejecutó correctamente los 3 pasos")

# ----- VISOCONSTRUCCIÓN -----
with st.expander("Visoconstrucción", expanded=True):
    st.markdown("**Copia de figuras y praxis**")
    respuestas["viso_copia_ok"] = st.checkbox(
        "Copia adecuada de dos pentágonos superpuestos / figura geométrica"
    )
    respuestas["viso_gestos_ok"] = st.checkbox(
        "Realizó gestos por imitación (p. ej., encender una vela) correctamente"
    )

# ----- MEMORIA DIFERIDA -----
with st.expander("Memoria diferida", expanded=True):
    st.markdown("**Recuerdo de las mismas palabras al final**")
    respuestas["mem_diferida"] = st.text_input("Recuerde las palabras iniciales (separadas por coma)")

# ----- ABSTRACCIÓN -----
with st.expander("Abstracción", expanded=True):
    st.markdown("**Semejanzas / Diferencias**")
    respuestas["abs_barco_auto"] = st.text_input("¿En qué se parecen un barco y un coche?")
    respuestas["abs_uva_manzana"] = st.text_input("¿En qué se parecen una uva y una manzana?")


# ------------------------------------------------------------
# SCORING
# ------------------------------------------------------------

def score_orientacion(r: Dict[str, Any]) -> int:
    pts = 0
    hoy = date.today()
    if int(r.get("ori_anio", 0)) == hoy.year:
        pts += 2
    if int(r.get("ori_mes", 0)) == hoy.month:
        pts += 2
    if int(r.get("ori_dia", 0)) == hoy.day:
        pts += 2
    if str(r.get("ori_ciudad", "")).strip():
        pts += 2
    if str(r.get("ori_lugar", "")).strip():
        pts += 2
    return min(pts, MAXIMOS["Orientación"])


def score_atencion(r: Dict[str, Any]) -> int:
    pts = 0
    try:
        valores = [int(x) for x in normalize_list(str(r.get("aten_s7", "")))]
        esperado = [93, 86, 79, 72, 65]
        aciertos = sum(1 for i, v in enumerate(valores[:5]) if v == esperado[i])
        pts += min(aciertos, 5)
    except Exception:
        pass
    if str(r.get("aten_inversa", "")).strip().lower() == "asac":
        pts += 5
    return min(pts, MAXIMOS["Atención"])


def score_memoria_inmediata(r: Dict[str, Any]) -> int:
    if not st.session_state.registered_words:
        return 0
    user_words = normalize_list(str(r.get("mem_inmediata", "")))
    aciertos = count_matches(user_words, st.session_state.target_words)
    return min(aciertos, MAXIMOS["Memoria inmediata"])  # 1 punto por palabra


def score_lenguaje(r: Dict[str, Any]) -> int:
    pts = 0
    try:
        n = int(r.get("len_animales", 0))
        pts += min(n // int(animals_per_point), int(max_fluency_points))
    except Exception:
        pass
    frase = str(r.get("len_frase", "")).strip()
    if len(frase.split()) >= 4:
        pts += 2
    if bool(r.get("len_orden_ok", False)):
        pts += 2
    return min(pts, MAXIMOS["Lenguaje/Ejecutivo"])


def score_viso(r: Dict[str, Any]) -> int:
    pts = 0
    if bool(r.get("viso_copia_ok", False)):
        pts += 3
    if bool(r.get("viso_gestos_ok", False)):
        pts += 2
    return min(pts, MAXIMOS["Visoconstrucción"])


def score_memoria_diferida(r: Dict[str, Any]) -> int:
    user_words = normalize_list(str(r.get("mem_diferida", "")))
    aciertos = count_matches(user_words, st.session_state.target_words)
    return min(aciertos, MAXIMOS["Memoria diferida"])  # 1 punto por palabra


def score_abstraccion(r: Dict[str, Any]) -> int:
    pts = 0
    barco_auto = str(r.get("abs_barco_auto", "")).lower()
    if any(k in barco_auto for k in ["transporte", "vehículo", "vehiculo", "mover", "desplazarse"]):
        pts += 2
    uva_manzana = str(r.get("abs_uva_manzana", "")).lower()
    if any(k in uva_manzana for k in ["fruta", "alimento", "comer"]):
        pts += 2
    return min(pts, MAXIMOS["Abstracción"])


# ------------------------------------------------------------
# EXPORT: CSV + HTML IMPRIMIBLE
# ------------------------------------------------------------

def build_results_dict(subtotales: Dict[str,int], maximos: Dict[str,int], total: int, porcentaje: float) -> Dict[str, Any]:
    return {
        "id_paciente": id_paciente,
        "nombre": nombre,
        "fecha": str(fecha_eval),
        **{f"{k}_puntaje": v for k, v in subtotales.items()},
        "total": total,
        "max_total": sum(maximos.values()),
        "porcentaje": round(porcentaje, 2),
    }


def results_to_csv(results: Dict[str, Any]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(results.keys()))
    writer.writeheader()
    writer.writerow(results)
    return buf.getvalue().encode("utf-8")


def render_html_report(
    subtotales: Dict[str,int],
    maximos: Dict[str,int],
    total: int,
    porcentaje: float,
    logo_b64: Optional[str],
    sig_nombre: str,
    sig_rol: str,
    sig_matricula: str,
) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:64px;" />' if logo_b64 else ""
    rows_html = "".join(
        f"<tr><td>{dom}</td><td>{subtotales.get(dom,0)}</td><td>{maximos.get(dom,0)}</td></tr>" for dom in DOMINIOS
    )
    firma_html = """
      <div style='margin-top:40px;'>
        <div style='border-top:1px solid #333; width:320px;'></div>
        <div><strong>{sig_nombre}</strong></div>
        <div>{sig_rol}</div>
        <div>{sig_matricula}</div>
      </div>
    """.format(sig_nombre=sig_nombre or "", sig_rol=sig_rol or "", sig_matricula=sig_matricula or "")

    html = f"""
<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'/>
<title>Evaluación Cognitiva — Informe</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; }}
  header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }}
  h1 {{ font-size: 20px; margin: 0; }}
  .meta {{ color:#555; font-size: 12px; }}
  table {{ width:100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ border:1px solid #ccc; padding:8px; text-align:left; }}
  th {{ background:#f5f5f5; }}
  .totals {{ margin-top:16px; font-weight:bold; }}
  .footer {{ margin-top:48px; font-size:12px; color:#666; }}
</style>
</head>
<body>
  <header>
    <div>{logo_html}</div>
    <div>
      <h1>Evaluación Cognitiva — Informe</h1>
      <div class='meta'>Generado: {today_str}</div>
    </div>
  </header>

  <section>
    <p><strong>Paciente:</strong> {nombre} — <strong>ID/HC:</strong> {id_paciente} — <strong>Fecha evaluación:</strong> {fecha_eval}</p>
  </section>

  <table>
    <thead><tr><th>Dominio</th><th>Puntaje</th><th>Máximo</th></tr></thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <div class='totals'>Total: {total} / {sum(maximos.values())} — {porcentaje:.2f}%</div>

  {firma_html}

  <div class='footer'>
    <p>Herramienta educativa. No reemplaza evaluación médica profesional.</p>
  </div>
</body>
</html>
"""
    return html


# ------------------------------------------------------------
# CÁLCULO, REPORTE Y DESCARGAS
# ------------------------------------------------------------

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Calcular puntajes"):
        subtotales = {
            "Orientación": score_orientacion(respuestas),
            "Atención": score_atencion(respuestas),
            "Memoria inmediata": score_memoria_inmediata(respuestas),
            "Lenguaje/Ejecutivo": score_lenguaje(respuestas),
            "Visoconstrucción": score_viso(respuestas),
            "Memoria diferida": score_memoria_diferida(respuestas),
            "Abstracción": score_abstraccion(respuestas),
        }
        total = sum(subtotales.values())
        max_total = sum(MAXIMOS.values())
        porcentaje = (total / max_total) * 100 if max_total else 0

        st.success(f"Puntaje total: {total} / {max_total}")
        st.write("**Detalle por dominio:**")
        rows = [{"Dominio": d, "Puntaje": subtotales[d], "Máximo": MAXIMOS[d]} for d in DOMINIOS]
        st.table(rows)

        # Interpretación con umbrales configurables
        if porcentaje >= high_threshold:
            interp = "Dentro de parámetros esperados (alto rendimiento)."
        elif porcentaje >= mid_threshold:
            interp = "Leve compromiso o rendimiento limítrofe."
        else:
            interp = "Sugerente de compromiso cognitivo, evaluar clínicamente."
        st.info(f"Interpretación: {interp}")

        # CSV
        results = build_results_dict(subtotales, MAXIMOS, total, porcentaje)
        csv_bytes = results_to_csv(results)
        st.download_button(
            "Descargar resultados (CSV)",
            data=csv_bytes,
            file_name="evaluacion_cognitiva.csv",
            mime="text/csv",
        )

        # HTML imprimible (logo + firma)
        logo_b64 = file_to_base64(logo_file)
        html = render_html_report(
            subtotales,
            MAXIMOS,
            total,
            porcentaje,
            logo_b64,
            sig_nombre,
            sig_rol,
            sig_matricula,
        )
        st.download_button(
            "Descargar informe (HTML)",
            data=html.encode("utf-8"),
            file_name=f"informe_evaluacion_{(nombre or 'paciente').replace(' ', '_')}.html",
            mime="text/html",
        )

with col2:
    st.markdown("### Buenas prácticas de aplicación")
    st.markdown(
        """
        - Realizar la evaluación en ambiente tranquilo, sin interrupciones.
        - Leer consignas textuales y registrar literalmente las respuestas.
        - No dar feedback de correcto/incorrecto hasta finalizar.
        - Complementar con historia clínica y, de ser necesario, derivar a especialista.
        """
    )

st.divider()

# ------------------------------------------------------------
# AUTO‑TESTS (unit tests ligeros dentro de la app)
# ------------------------------------------------------------

def run_self_tests(MAXIMOS_local: Dict[str,int]):
    """Ejecuta casos de prueba sobre las funciones de scoring. Muestra PASS/FAIL."""
    results = []

    # Preparación de estado para pruebas de memoria
    st.session_state.target_words = ["manzana", "llave", "libro", "perro", "puente"]

    # 1) Orientación — todo correcto
    hoy = date.today()
    r1 = {
        "ori_anio": hoy.year,
        "ori_mes": hoy.month,
        "ori_dia": hoy.day,
        "ori_ciudad": "Córdoba",
        "ori_lugar": "Hospital",
    }
    exp1 = MAXIMOS_local["Orientación"]
    results.append(("Orientación full", score_orientacion(r1), exp1))

    # 2) Atención — serie + inversa correctas
    r2 = {"aten_s7": "93,86,79,72,65", "aten_inversa": "asac"}
    exp2 = MAXIMOS_local["Atención"]
    results.append(("Atención full", score_atencion(r2), exp2))

    # 3) Memoria inmediata — 5/5 (capado por máximo)
    st.session_state.registered_words = True
    r3 = {"mem_inmediata": ",".join(st.session_state.target_words)}
    exp3 = MAXIMOS_local["Memoria inmediata"]
    results.append(("Memoria inmediata full", score_memoria_inmediata(r3), exp3))

    # 4) Lenguaje/Ejecutivo — 20 animales (depende de animals_per_point y max_fluency_points) + frase + orden
    r4 = {"len_animales": animals_per_point * max_fluency_points, "len_frase": "El paciente escribe una oración completa", "len_orden_ok": True}
    exp4 = min( max_fluency_points + 2 + 2, MAXIMOS_local["Lenguaje/Ejecutivo"] )
    results.append(("Lenguaje/Ejecutivo full-ish", score_lenguaje(r4), exp4))

    # 5) Visoconstrucción — ambos OK
    r5 = {"viso_copia_ok": True, "viso_gestos_ok": True}
    exp5 = MAXIMOS_local["Visoconstrucción"]
    results.append(("Visoconstrucción full", score_viso(r5), exp5))

    # 6) Memoria diferida — palabras completas (capado por máximo)
    r6 = {"mem_diferida": ",".join(st.session_state.target_words)}
    exp6 = MAXIMOS_local["Memoria diferida"]
    results.append(("Memoria diferida full", score_memoria_diferida(r6), exp6))

    # 7) Abstracción — con palabras clave
    r7 = {"abs_barco_auto": "Ambos son medios de transporte", "abs_uva_manzana": "Ambas son fruta"}
    exp7 = MAXIMOS_local["Abstracción"]
    results.append(("Abstracción full", score_abstraccion(r7), exp7))

    total_cases = len(results)
    passes = sum(1 for name, got, exp in results if got == exp)
    st.subheader("Resultados de auto‑tests")
    st.write(f"{passes}/{total_cases} casos OK")
    table_rows = [{"Caso": name, "Obtenido": got, "Esperado": exp, "Estado": "PASS" if got == exp else "FAIL"} for (name, got, exp) in results]
    st.table(table_rows)

if run_tests:
    run_self_tests(MAXIMOS)

st.caption("© 2025 — Prototipo educativo para entrenamiento.")


# ==============================================
# requirements.txt
# ==============================================
# Coloque este contenido en un archivo independiente llamado requirements.txt
# streamlit==1.37.0

# ==============================================
# .gitignore
# ==============================================
# Coloque este contenido en un archivo independiente llamado .gitignore
# .venv/
# __pycache__/
# *.pyc
# .DS_Store

# ==============================================
# README.md
# ==============================================
# Coloque este contenido en un archivo independiente llamado README.md
#
# # Evaluación Cognitiva — Streamlit
#
# Prototipo educativo para administración de una evaluación cognitiva con puntajes por dominio, exportación a CSV/HTML y parámetros configurables.
#
# ## Requisitos
# - Python 3.9+
# - Streamlit
#
# ## Instalación
# ```bash
# python -m venv .venv
# # Windows
# .venv\Scripts\activate
# # macOS/Linux
# source .venv/bin/activate
# pip install -r requirements.txt
# ```
#
# ## Ejecutar
# ```bash
# streamlit run app.py
# ```
#
# ## Configuración
# - Sidebar: palabras de memoria, umbrales de interpretación, puntajes máximos por dominio, parámetros de fluidez.
# - Suba un logo y complete los campos de firma para el reporte HTML imprimible.
#
# ## Despliegue en Streamlit Cloud
# 1. Suba este repo a GitHub.
# 2. En Streamlit Community Cloud, cree una app apuntando a `app.py`.
# 3. Asegúrese de incluir `requirements.txt` (con `streamlit`).
#
# ## Notas
# - Este prototipo no reemplaza evaluaciones médicas profesionales.
