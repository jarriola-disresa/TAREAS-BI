"""
Dashboard BI - Gestión de Tareas Diarias
Disresa | Departamento de Business Intelligence
"""

import hashlib
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from pathlib import Path
import io

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BI Tasks | Disresa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth ──────────────────────────────────────────────────────────────────────
def _check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    st.markdown(
        "<h2 style='text-align:center;margin-top:80px'>🔐 Dashboard BI — Disresa</h2>",
        unsafe_allow_html=True,
    )
    col = st.columns([1, 1, 1])[1]
    with col:
        pwd = st.text_input("Contraseña", type="password", key="_pwd")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if hashlib.sha256(pwd.encode()).hexdigest() == st.secrets["PASSWORD_HASH"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    return False

if not _check_password():
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.2rem;}

.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-left: 4px solid var(--cc, #0D9DDB);
    margin-bottom: 4px;
}
.kpi-val  {font-size:1.6rem;font-weight:700;color:#1B3A6B;line-height:1.1;}
.kpi-lbl  {font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-top:4px;}
.kpi-delta{font-size:.76rem;margin-top:4px;}

.section-title {
    font-size:.83rem;font-weight:700;color:#1B3A6B;
    text-transform:uppercase;letter-spacing:.07em;
    border-bottom:2px solid #0D9DDB;padding-bottom:4px;margin-bottom:14px;
}

.alert-blocked {
    background:#FEF3C7;border-left:4px solid #F59E0B;
    border-radius:8px;padding:10px 14px;margin-bottom:6px;
    color:#92400E;font-size:.87rem;
}

.task-row {
    background:white;border-radius:10px;padding:12px 16px;
    box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:8px;
    border-left:4px solid var(--tc,#0D9DDB);
}

.badge-chema {background:#DBEAFE;color:#1D4ED8;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:700;}
.badge-jc    {background:#D1FAE5;color:#065F46;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:700;}

.stTabs [data-baseweb="tab-list"] {gap:4px;background:#F1F5F9;border-radius:10px;padding:4px;}
.stTabs [data-baseweb="tab"]      {border-radius:8px;padding:6px 14px;font-size:.86rem;}

div[data-testid="stForm"] {
    background: #F8FAFC;
    border-radius: 14px;
    padding: 24px;
    border: 1px solid #E2E8F0;
}
</style>
""", unsafe_allow_html=True)

# ── Paleta & layout charts ────────────────────────────────────────────────────
C_BLUE, C_NAVY, C_GREEN, C_AMBER, C_RED, C_PURPLE, C_GRAY = (
    "#0D9DDB", "#1B3A6B", "#00C49A", "#F59E0B", "#EF4444", "#8B5CF6", "#94A3B8"
)
PALETTE = [C_BLUE, C_GREEN, C_AMBER, C_RED, C_PURPLE, C_NAVY, "#F97316", C_GRAY]
CL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter,Arial,sans-serif", color="#334155", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
)
COLOR_ESTADO = {"Completada": C_GREEN, "En progreso": C_BLUE,
                "Pendiente": C_AMBER, "Bloqueada": C_RED}

# ── Catálogos ─────────────────────────────────────────────────────────────────
DATA_FILE   = Path("tasks.csv")
USUARIOS    = ["Chema", "JC"]
MARCAS      = ["Skechers","Cole Haan","New Era","Columbia",
               "Psycho Bunny","47 Brand","Fabletics","Multi-marca","N/A"]
PAISES      = ["GT","SV","HN","CR","PA","RD","Regional","N/A"]
TIPOS       = ["Reporte sell-through","Automatización Python","ETL / Airflow",
               "Reporte Excel","Presentación PPT","Email / Comunicación",
               "Data quality SAP","Análisis ad-hoc","Reunión","PBI","Otro"]
PRIORIDADES = ["🔴 Alta","🟡 Media","🟢 Baja"]
ESTADOS     = ["Pendiente","En progreso","Completada","Bloqueada"]
COLUMNAS    = ["id","fecha","fecha_limite","usuario","tipo","marca","pais","descripcion",
               "prioridad","estado","tiempo_min","tiempo_estimado_min","notas","creado_en"]

# ── Data layer ────────────────────────────────────────────────────────────────
def cargar_datos() -> pd.DataFrame:
    if not DATA_FILE.exists():
        pd.DataFrame(columns=COLUMNAS).to_csv(DATA_FILE, index=False, sep=";")
        return pd.DataFrame(columns=COLUMNAS)
    df = pd.read_csv(DATA_FILE, sep=";")
    for col, default in [("tiempo_estimado_min", 0), ("notas", ""), ("fecha_limite", None)]:
        if col not in df.columns:
            df[col] = default
    if not df.empty:
        df["fecha"]               = pd.to_datetime(df["fecha"]).dt.date
        df["fecha_limite"]        = pd.to_datetime(df["fecha_limite"], errors="coerce").dt.date
        df["tiempo_min"]          = pd.to_numeric(df["tiempo_min"],          errors="coerce").fillna(0).astype(int)
        df["tiempo_estimado_min"] = pd.to_numeric(df["tiempo_estimado_min"], errors="coerce").fillna(0).astype(int)
        df["notas"]               = df["notas"].fillna("")
    return df

def guardar_tarea(nueva: dict):
    df = cargar_datos()
    nueva["id"]        = int(df["id"].max()) + 1 if not df.empty else 1
    nueva["creado_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.concat([df, pd.DataFrame([nueva])], ignore_index=True).to_csv(DATA_FILE, index=False, sep=";")

def actualizar_tarea(task_id: int, campos: dict):
    df = cargar_datos()
    for k, v in campos.items():
        df.loc[df["id"] == task_id, k] = v
    df.to_csv(DATA_FILE, index=False, sep=";")

def eliminar_tarea(task_id: int):
    df = cargar_datos()
    df[df["id"] != task_id].to_csv(DATA_FILE, index=False, sep=";")

# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi(label, value, delta=None, color=C_BLUE):
    dhtml = ""
    if delta is not None:
        c = C_GREEN if delta >= 0 else C_RED
        arrow = "▲" if delta > 0 else "▼"
        dhtml = f"<div class='kpi-delta' style='color:{c}'>{arrow} {abs(delta):.0f}% vs sem. ant.</div>"
    st.markdown(f"""
    <div class='kpi-card' style='--cc:{color}'>
        <div class='kpi-val'>{value}</div>
        <div class='kpi-lbl'>{label}</div>
        {dhtml}
    </div>""", unsafe_allow_html=True)

def pct_delta(curr, prev):
    return round((curr - prev) / prev * 100) if prev else None

def semanas(df):
    hoy   = date.today()
    ini   = hoy - timedelta(days=hoy.weekday())
    ini_a = ini - timedelta(weeks=1)
    fin_a = ini - timedelta(days=1)
    return (df[(df["fecha"] >= ini)   & (df["fecha"] <= hoy)],
            df[(df["fecha"] >= ini_a) & (df["fecha"] <= fin_a)])

def color_prioridad(p):
    if "Alta"  in str(p): return C_RED
    if "Media" in str(p): return C_AMBER
    return C_GREEN

def sel_o_escribe(label, opciones, key, col=None):
    """Selectbox + campo libre opcional. Si el usuario escribe algo, tiene prioridad."""
    c = col or st
    val = c.selectbox(label, opciones, key=f"sel_{key}")
    txt = c.text_input("", placeholder="✏️ Otro — escribe aquí...",
                       key=f"txt_{key}", label_visibility="collapsed")
    return txt.strip() if txt.strip() else val

# ── Carga única de datos (se refresca completa en cada st.rerun) ──────────────
df_all = cargar_datos()

# ── SIDEBAR — métricas rápidas ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:8px 0 18px'>
        <div style='font-size:2rem'>📊</div>
        <div style='font-weight:700;color:#1B3A6B;font-size:1.05rem'>BI Tasks</div>
        <div style='color:#64748B;font-size:.74rem'>Disresa · {date.today().strftime("%d %b %Y")}</div>
    </div>""", unsafe_allow_html=True)

    if not df_all.empty:
        hoy_n  = len(df_all[df_all["fecha"] == date.today()])
        pend_n = (df_all["estado"] == "Pendiente").sum()
        prog_n = (df_all["estado"] == "En progreso").sum()
        bloq_n = (df_all["estado"] == "Bloqueada").sum()

        st.markdown("**Resumen rápido**")
        st.metric("Tareas hoy",  hoy_n)
        st.metric("En progreso", prog_n)
        st.metric("Pendientes",  pend_n)
        if bloq_n:
            st.metric("⚠️ Bloqueadas", bloq_n)

        st.divider()
        st.markdown("**Por usuario**")
        for u in USUARIOS:
            n = len(df_all[df_all["usuario"] == u])
            st.markdown(f"**{u}** — {n} tareas")

    st.divider()
    st.caption(f"📁 `tasks.csv`  ·  v2.0")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#1B3A6B;margin-bottom:0;font-size:1.75rem'>
    📊 Dashboard BI — Gestión de Tareas
</h1>
<p style='color:#64748B;margin-top:2px;font-size:.86rem'>
    Disresa · Departamento de Business Intelligence
</p>""", unsafe_allow_html=True)

# ── Alertas bloqueadas ────────────────────────────────────────────────────────
if not df_all.empty:
    bloq_df = df_all[df_all["estado"] == "Bloqueada"]
    if not bloq_df.empty:
        with st.expander(f"⚠️  {len(bloq_df)} tarea(s) BLOQUEADA(s) — requieren atención", expanded=True):
            for _, r in bloq_df.iterrows():
                badge = "badge-chema" if r["usuario"] == "Chema" else "badge-jc"
                nota  = f"<br><small>📌 {r['notas']}</small>" if r.get("notas") else ""
                st.markdown(f"""
                <div class='alert-blocked'>
                    <b>#{int(r['id'])}</b> · <span class='{badge}'>{r['usuario']}</span>
                    · {r['tipo']} · <b>{r['descripcion'][:80]}</b>{nota}
                </div>""", unsafe_allow_html=True)

st.divider()

# ── TABS ──────────────────────────────────────────────────────────────────────
t_new, t1, t2, t3, t4, t_gantt, t5, t6 = st.tabs([
    "➕ Nueva Tarea",
    "🏠 Overview", "📈 Análisis", "👥 Equipo",
    "🗓️ Actividad", "📅 Gantt", "📋 Registros", "⚙️ Gestionar"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — NUEVA TAREA
# ══════════════════════════════════════════════════════════════════════════════
with t_new:
    col_form, col_recientes = st.columns([3, 2], gap="large")

    with col_form:
        st.markdown("### Registrar nueva tarea")
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("form_nueva", clear_on_submit=True):
            desc = st.text_area("📝 Descripción *",
                                placeholder="¿Qué tarea vas a registrar? Ej: Reporte sell-through Skechers GT semana 20...",
                                height=100)

            r1a, r1b, r1c, r1d = st.columns(4)
            usuario  = r1a.selectbox("👤 Asignado a",  USUARIOS)
            prior    = r1b.selectbox("🚦 Prioridad",   PRIORIDADES, index=1)
            estado      = r1c.selectbox("📌 Estado",         ESTADOS)
            fecha_n     = r1d.date_input("📅 Inicio",        value=date.today())

            r2a, r2b, r2c, r2d = st.columns(4)
            tipo      = sel_o_escribe("🗂️ Tipo de tarea", TIPOS,   "tipo_n",  r2a)
            marca     = sel_o_escribe("👟 Marca",          MARCAS,  "marca_n", r2b)
            pais      = sel_o_escribe("🌎 País",           PAISES,  "pais_n",  r2c)
            fecha_lim = r2d.date_input("🏁 Fecha límite",  value=date.today() + timedelta(days=7))

            r3a, r3b, r3c = st.columns(3)
            t_real = r3a.number_input("⏱️ Tiempo real (min)",  min_value=0, value=0, step=15)
            t_est  = r3b.number_input("🎯 Estimado (min)",     min_value=0, value=0, step=15)
            notas  = r3c.text_input("🔗 Notas / link", placeholder="URL, observación...")

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "✅  Guardar tarea",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not desc.strip():
                st.error("La descripción no puede estar vacía.")
            else:
                guardar_tarea({
                    "fecha": fecha_n, "fecha_limite": fecha_lim,
                    "usuario": usuario, "tipo": tipo,
                    "marca": marca, "pais": pais, "descripcion": desc.strip(),
                    "prioridad": prior, "estado": estado,
                    "tiempo_min": int(t_real), "tiempo_estimado_min": int(t_est),
                    "notas": notas.strip(),
                })
                st.session_state["ultima_tarea"] = desc.strip()
                st.success(f"✅ Tarea guardada correctamente")
                st.rerun()

        if st.session_state.get("ultima_tarea"):
            st.info(f"Última tarea agregada: **{st.session_state['ultima_tarea']}**")

    # ── Tareas recientes ──────────────────────────────────────────────────────
    with col_recientes:
        st.markdown("### Tareas recientes")
        if df_all.empty:
            st.info("Aún no hay tareas. ¡Agrega la primera!")
        else:
            recientes = df_all.sort_values("creado_en", ascending=False).head(10)
            for _, r in recientes.iterrows():
                rid = int(r["id"])
                tc  = COLOR_ESTADO.get(r["estado"], C_GRAY)
                badge = "badge-chema" if r["usuario"] == "Chema" else "badge-jc"

                with st.expander(
                    f"#{rid} · {r['descripcion'][:48]}",
                    expanded=False,
                ):
                    # Info rápida
                    st.markdown(f"""
                    <div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px'>
                        <span class='{badge}'>{r["usuario"]}</span>
                        <span style='font-size:.75rem;color:{tc};font-weight:700'>● {r["estado"]}</span>
                        <span style='font-size:.75rem;color:{color_prioridad(r["prioridad"])};font-weight:700'>{r["prioridad"]}</span>
                        <span style='font-size:.75rem;color:#64748B'>{r["fecha"]} · {r["tipo"]}</span>
                    </div>""", unsafe_allow_html=True)

                    with st.form(f"rec_edit_{rid}"):
                        nd = st.text_area("Descripción", value=r["descripcion"],
                                          height=68, key=f"rd_{rid}")
                        ea, eb, ec = st.columns(3)
                        ne  = ea.selectbox("Estado",    ESTADOS,     index=ESTADOS.index(r["estado"])         if r["estado"]    in ESTADOS     else 0, key=f"re_{rid}")
                        npr = eb.selectbox("Prioridad", PRIORIDADES, index=PRIORIDADES.index(r["prioridad"])  if r["prioridad"] in PRIORIDADES else 1, key=f"rp_{rid}")
                        nu  = ec.selectbox("Asignado",  USUARIOS,    index=USUARIOS.index(r["usuario"])       if r["usuario"]   in USUARIOS    else 0, key=f"ru_{rid}")
                        ntr = st.number_input("Tiempo real (min)", min_value=0,
                                              value=int(r["tiempo_min"]), step=15, key=f"rt_{rid}")

                        ba, bb = st.columns(2)
                        guardar = ba.form_submit_button("💾 Guardar", use_container_width=True, type="primary")
                        borrar  = bb.form_submit_button("🗑️ Borrar",  use_container_width=True)

                    if guardar:
                        actualizar_tarea(rid, {"descripcion": nd.strip(), "estado": ne,
                                               "prioridad": npr, "usuario": nu,
                                               "tiempo_min": ntr})
                        st.rerun()
                    if borrar:
                        eliminar_tarea(rid)
                        st.rerun()

# ── Filtros globales (para los demás tabs) ────────────────────────────────────
if df_all.empty:
    for tab in [t1, t2, t3, t4, t5, t6]:
        with tab:
            st.info("No hay tareas registradas todavía. Ve a ➕ Nueva Tarea para agregar la primera.")
    st.stop()

with st.expander("🔍  Filtros globales", expanded=False):
    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    f_usr  = fc1.multiselect("Usuario", sorted(df_all["usuario"].unique()))
    f_tipo = fc2.multiselect("Tipo",    sorted(df_all["tipo"].unique()))
    f_marc = fc3.multiselect("Marca",   sorted(df_all["marca"].unique()))
    f_pais = fc4.multiselect("País",    sorted(df_all["pais"].unique()))
    f_est  = fc5.multiselect("Estado",  sorted(df_all["estado"].unique()))
    rango  = st.date_input("Rango de fechas",
                           value=(df_all["fecha"].min(), df_all["fecha"].max()),
                           min_value=df_all["fecha"].min(), max_value=df_all["fecha"].max())

df_f = df_all.copy()
if f_usr:  df_f = df_f[df_f["usuario"].isin(f_usr)]
if f_tipo: df_f = df_f[df_f["tipo"].isin(f_tipo)]
if f_marc: df_f = df_f[df_f["marca"].isin(f_marc)]
if f_pais: df_f = df_f[df_f["pais"].isin(f_pais)]
if f_est:  df_f = df_f[df_f["estado"].isin(f_est)]
if isinstance(rango, tuple) and len(rango) == 2:
    df_f = df_f[(df_f["fecha"] >= rango[0]) & (df_f["fecha"] <= rango[1])]

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with t1:
    sem, ant = semanas(df_f)
    total  = len(df_f);     tot_s = len(sem);                          tot_a = len(ant)
    comp   = (df_f["estado"] == "Completada").sum()
    comp_s = (sem["estado"]  == "Completada").sum() if not sem.empty else 0
    comp_a = (ant["estado"]  == "Completada").sum() if not ant.empty else 0
    pend   = (df_f["estado"] == "Pendiente").sum()
    bloq   = (df_f["estado"] == "Bloqueada").sum()
    horas  = df_f["tiempo_min"].sum() / 60
    tce    = df_f[(df_f["tiempo_estimado_min"] > 0) & (df_f["tiempo_min"] > 0)]
    efic   = round(tce["tiempo_estimado_min"].sum() / tce["tiempo_min"].sum() * 100) if not tce.empty else None

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: kpi("Total tareas",    total, pct_delta(tot_s, tot_a),  C_BLUE)
    with k2:
        pct_c = f"{comp/total*100:.0f}%" if total else "0%"
        kpi("Completadas", f"{comp} ({pct_c})", pct_delta(comp_s, comp_a), C_GREEN)
    with k3: kpi("Pendientes",      pend,  color=C_AMBER)
    with k4: kpi("Bloqueadas",      bloq,  color=C_RED)
    with k5: kpi("Horas invertidas", f"{horas:.1f}h", color=C_NAVY)
    with k6:
        if efic is not None:
            kpi("Eficiencia", f"{efic}%",
                color=C_GREEN if efic >= 90 else (C_AMBER if efic >= 70 else C_RED))
        else:
            kpi("Eficiencia", "N/D", color=C_GRAY)

    st.markdown("<br>", unsafe_allow_html=True)
    cw, ce2, ct = st.columns([1, 1, 2])

    with cw:
        st.markdown("<div class='section-title'>Carga activa</div>", unsafe_allow_html=True)
        activas = df_f[df_f["estado"].isin(["Pendiente","En progreso"])]
        carga   = activas.groupby("usuario").size().reindex(USUARIOS, fill_value=0)
        for u, n in carga.items():
            c_c = C_GREEN if n <= 3 else (C_AMBER if n <= 6 else C_RED)
            b_c = "🟢" if n <= 3 else ("🟡" if n <= 6 else "🔴")
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;align-items:center;
                        background:white;border-radius:8px;padding:10px 14px;
                        margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
                <span style='font-weight:600;color:#1B3A6B'>{u}</span>
                <span style='color:{c_c};font-weight:700'>{b_c} {n}</span>
            </div>""", unsafe_allow_html=True)

    with ce2:
        st.markdown("<div class='section-title'>Estimado vs Real</div>", unsafe_allow_html=True)
        if tce.empty:
            st.info("Sin datos de tiempo estimado aún.")
        else:
            eu  = tce.groupby("usuario").agg(est=("tiempo_estimado_min","sum"),
                                             real=("tiempo_min","sum")).reset_index()
            fig = go.Figure()
            fig.add_bar(x=eu["usuario"], y=eu["est"]/60,  name="Estimado", marker_color=C_BLUE)
            fig.add_bar(x=eu["usuario"], y=eu["real"]/60, name="Real",     marker_color=C_AMBER)
            fig.update_layout(**CL, barmode="group", height=200,
                              legend=dict(orientation="h", y=1.15))
            st.plotly_chart(fig, use_container_width=True)

    with ct:
        st.markdown("<div class='section-title'>Tendencia semanal</div>", unsafe_allow_html=True)
        df_tw = df_f.copy()
        df_tw["semana"] = pd.to_datetime(df_tw["fecha"]).dt.to_period("W").apply(lambda x: x.start_time.date())
        ps = df_tw.groupby(["semana","estado"]).size().reset_index(name="n")
        pv = ps.pivot(index="semana", columns="estado", values="n").fillna(0).reset_index()
        fig = go.Figure()
        for e in ESTADOS:
            if e in pv.columns:
                fig.add_scatter(x=pv["semana"], y=pv[e], name=e, mode="lines+markers",
                                line=dict(color=COLOR_ESTADO.get(e, C_GRAY), width=2))
        fig.update_layout(**CL, height=200, legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANÁLISIS
# ══════════════════════════════════════════════════════════════════════════════
with t2:
    ca2, cb2 = st.columns(2)
    with ca2:
        st.markdown("<div class='section-title'>Tareas por tipo</div>", unsafe_allow_html=True)
        pt = df_f.groupby("tipo").size().reset_index(name="n").sort_values("n")
        fig = px.bar(pt, x="n", y="tipo", orientation="h",
                     labels={"n":"Tareas","tipo":""}, color_discrete_sequence=[C_BLUE])
        fig.update_layout(**CL, height=340)
        st.plotly_chart(fig, use_container_width=True)

    with cb2:
        st.markdown("<div class='section-title'>Estado de tareas</div>", unsafe_allow_html=True)
        pe = df_f.groupby("estado").size().reset_index(name="n")
        fig = px.pie(pe, names="estado", values="n", hole=0.55,
                     color="estado", color_discrete_map=COLOR_ESTADO)
        fig.update_layout(**CL, height=340, legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig, use_container_width=True)

    cc2, cd2 = st.columns(2)
    with cc2:
        st.markdown("<div class='section-title'>Horas por marca</div>", unsafe_allow_html=True)
        hm = df_f.groupby("marca")["tiempo_min"].sum().reset_index()
        hm["horas"] = hm["tiempo_min"] / 60
        fig = px.bar(hm.sort_values("horas", ascending=False), x="marca", y="horas",
                     labels={"horas":"Horas","marca":""},
                     color="horas", color_continuous_scale=["#DBEAFE", C_NAVY])
        fig.update_layout(**CL, height=300, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with cd2:
        st.markdown("<div class='section-title'>Tareas por país</div>", unsafe_allow_html=True)
        pp = df_f.groupby("pais").size().reset_index(name="n").sort_values("n", ascending=False)
        fig = px.bar(pp, x="pais", y="n", labels={"n":"Tareas","pais":""},
                     color_discrete_sequence=[C_PURPLE])
        fig.update_layout(**CL, height=300)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-title'>Registradas vs completadas por día</div>", unsafe_allow_html=True)
    dias   = pd.date_range(pd.to_datetime(df_f["fecha"].min()),
                           pd.to_datetime(df_f["fecha"].max()), freq="D")
    df_td  = df_f.copy(); df_td["fecha_dt"] = pd.to_datetime(df_td["fecha"])
    reg    = df_td.groupby("fecha_dt").size().reindex(dias, fill_value=0)
    comp_d = df_td[df_td["estado"]=="Completada"].groupby("fecha_dt").size().reindex(dias, fill_value=0)
    fig    = go.Figure()
    fig.add_scatter(x=dias, y=reg.values, name="Registradas", mode="lines+markers",
                    line=dict(color=C_BLUE, width=2),
                    fill="tozeroy", fillcolor="rgba(13,157,219,0.12)")
    fig.add_scatter(x=dias, y=comp_d.values, name="Completadas", mode="lines+markers",
                    line=dict(color=C_GREEN, width=2))
    fig.update_layout(**CL, height=260, legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — EQUIPO
# ══════════════════════════════════════════════════════════════════════════════
with t3:
    col_ch, col_jc = st.columns(2)
    badges = {"Chema": ("badge-chema", C_BLUE), "JC": ("badge-jc", C_GREEN)}

    for u, col in zip(USUARIOS, [col_ch, col_jc]):
        dfu    = df_f[df_f["usuario"] == u]
        tot_u  = len(dfu)
        comp_u = (dfu["estado"] == "Completada").sum()
        pct_u  = f"{comp_u/tot_u*100:.0f}%" if tot_u else "0%"
        h_u    = dfu["tiempo_min"].sum() / 60
        badge_cls, badge_color = badges[u]

        with col:
            st.markdown(f"<h3><span class='{badge_cls}'>{u}</span></h3>",
                        unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1: kpi("Total",       tot_u,           color=badge_color)
            with m2: kpi("Completadas", pct_u,           color=C_GREEN)
            with m3: kpi("Horas",       f"{h_u:.1f}h",  color=C_NAVY)

            if not dfu.empty:
                pt_u = dfu.groupby("tipo").size().reset_index(name="n").sort_values("n")
                fig  = px.bar(pt_u, x="n", y="tipo", orientation="h",
                              labels={"n":"","tipo":""},
                              color_discrete_sequence=[badge_color])
                fig.update_layout(**CL, height=270, title="Por tipo")
                st.plotly_chart(fig, use_container_width=True)

                pe_u = dfu.groupby("estado").size().reset_index(name="n")
                fig  = px.pie(pe_u, names="estado", values="n", hole=0.5,
                              color="estado", color_discrete_map=COLOR_ESTADO)
                fig.update_layout(**CL, height=220, title="Estado")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin tareas con los filtros actuales.")

    st.divider()
    st.markdown("<div class='section-title'>Radar — Tipos de tarea por usuario</div>",
                unsafe_allow_html=True)
    fig = go.Figure()
    for u, color in zip(USUARIOS, [C_BLUE, C_GREEN]):
        dfu   = df_f[df_f["usuario"] == u]
        vals  = [len(dfu[dfu["tipo"] == t]) for t in TIPOS]
        theta = [t[:22] for t in TIPOS]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=theta + [theta[0]],
            fill="toself", name=u, line=dict(color=color),
            fillcolor="rgba(13,157,219,0.2)" if color == C_BLUE else "rgba(0,196,154,0.2)"
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, color="#94A3B8")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,Arial,sans-serif", color="#334155"),
        legend=dict(orientation="h", y=-0.1),
        height=420, margin=dict(l=60, r=60, t=40, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ACTIVIDAD
# ══════════════════════════════════════════════════════════════════════════════
with t4:
    DIAS_EN = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    DIAS_ES = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

    st.markdown("<div class='section-title'>Mapa de calor — Actividad semanal</div>",
                unsafe_allow_html=True)
    df_h = df_f.copy()
    df_h["fecha_dt"] = pd.to_datetime(df_h["fecha"])
    df_h["semana"]   = df_h["fecha_dt"].dt.strftime("W%W")
    df_h["dia"]      = df_h["fecha_dt"].dt.day_name()
    heat  = df_h.groupby(["semana","dia"]).size().reset_index(name="n")
    pivot = heat.pivot(index="dia", columns="semana", values="n").fillna(0)
    pivot = pivot.reindex(DIAS_EN, fill_value=0)
    fig   = px.imshow(pivot.values,
                      x=pivot.columns.tolist(),
                      y=DIAS_ES,
                      color_continuous_scale=["#EFF6FF", C_BLUE, C_NAVY],
                      labels=dict(x="Semana", y="Día", color="Tareas"),
                      text_auto=True)
    fig.update_layout(**CL, height=300)
    fig.update_traces(textfont_size=11)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-title'>Horas trabajadas por día de semana</div>",
                unsafe_allow_html=True)
    df_h["dia_n"]     = df_h["fecha_dt"].dt.dayofweek
    h_dia             = df_h.groupby(["dia","dia_n"])["tiempo_min"].sum().reset_index()
    h_dia["horas"]    = h_dia["tiempo_min"] / 60
    h_dia["dia_lbl"]  = h_dia["dia"].map(dict(zip(DIAS_EN, DIAS_ES)))
    h_dia             = h_dia.sort_values("dia_n")
    fig = px.bar(h_dia, x="dia_lbl", y="horas",
                 labels={"horas":"Horas","dia_lbl":""},
                 color="horas", color_continuous_scale=["#DBEAFE", C_NAVY])
    fig.update_layout(**CL, height=270, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB GANTT
# ══════════════════════════════════════════════════════════════════════════════
with t_gantt:
    if df_f.empty:
        st.info("No hay tareas con los filtros actuales.")
    else:
        # ── Controles ─────────────────────────────────────────────────────────
        gc1, gc2, gc3 = st.columns(3)
        g_color    = gc1.radio("Colorear por", ["Estado", "Usuario", "Prioridad"], horizontal=True)
        g_estados  = gc2.multiselect("Filtrar estados",  ESTADOS,  default=[])
        g_usuarios = gc3.multiselect("Filtrar usuarios", USUARIOS, default=[])

        # Todas las tareas — sin fecha_limite usan fecha+1 día como barra mínima
        df_g = df_f.copy()
        df_g["Start"]  = pd.to_datetime(df_g["fecha"])
        df_g["Finish"] = df_g.apply(
            lambda r: pd.to_datetime(r["fecha_limite"])
            if pd.notna(r["fecha_limite"]) and r["fecha_limite"] != r["fecha"]
            else pd.to_datetime(r["fecha"]) + pd.Timedelta(days=1),
            axis=1,
        )
        df_g["label"] = df_g.apply(
            lambda r: f"#{int(r['id'])}  {r['descripcion'][:45]}", axis=1
        )
        df_g["sin_limite"] = df_f["fecha_limite"].isna() | (df_f["fecha_limite"] == df_f["fecha"])

        # Filtros: vacío = mostrar todos
        if g_estados:
            df_g = df_g[df_g["estado"].isin(g_estados)]
        if g_usuarios:
            df_g = df_g[df_g["usuario"].isin(g_usuarios)]

        if df_g.empty:
            st.info("No hay tareas con esos filtros.")
        else:
            color_col = {"Estado": "estado", "Usuario": "usuario", "Prioridad": "prioridad"}[g_color]
            color_map = {
                "Chema": C_BLUE,      "JC": C_GREEN,
                "Completada": C_GREEN, "En progreso": C_BLUE,
                "Pendiente": C_AMBER,  "Bloqueada": C_RED,
                "🔴 Alta": C_RED,     "🟡 Media": C_AMBER, "🟢 Baja": C_GREEN,
            }

            fig = px.timeline(
                df_g.sort_values(["estado", "Start"]),
                x_start="Start", x_end="Finish",
                y="label",
                color=color_col,
                color_discrete_map=color_map,
                hover_data={"usuario": True, "tipo": True, "marca": True,
                            "estado": True, "prioridad": True,
                            "sin_limite": True, "label": False},
                labels={"label": "", "Start": "Inicio", "Finish": "Límite",
                        "sin_limite": "Sin fecha límite"},
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                **CL,
                height=max(380, len(df_g) * 36),
                legend=dict(orientation="h", y=1.04),
                xaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
            )
            hoy_str = str(date.today())
            fig.add_shape(type="line",
                          x0=hoy_str, x1=hoy_str, y0=0, y1=1,
                          xref="x", yref="paper",
                          line=dict(color=C_RED, width=1.5, dash="dash"))
            fig.add_annotation(x=hoy_str, y=1, xref="x", yref="paper",
                               text="Hoy", showarrow=False,
                               font=dict(color=C_RED, size=11),
                               yanchor="bottom")
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"⚪ Las tareas sin fecha límite se muestran como barra de 1 día. "
                       f"Agrégala en ⚙️ Gestionar para ver su duración real.")

            # ── Tareas vencidas ────────────────────────────────────────────────
            vencidas = df_g[
                (df_g["Finish"].dt.date < date.today()) &
                (df_g["estado"] != "Completada") &
                (~df_g["sin_limite"])
            ]
            if not vencidas.empty:
                st.markdown(
                    f"<div class='section-title' style='color:{C_RED}'>⚠️ {len(vencidas)} tarea(s) vencida(s)</div>",
                    unsafe_allow_html=True)
                for _, r in vencidas.iterrows():
                    badge  = "badge-chema" if r["usuario"] == "Chema" else "badge-jc"
                    dias_v = (date.today() - r["Finish"].dt.date if hasattr(r["Finish"], "dt") else (date.today() - r["Finish"].date())).days
                    st.markdown(f"""
                    <div class='alert-blocked'>
                        <b>#{int(r['id'])}</b> · <span class='{badge}'>{r['usuario']}</span>
                        · <b>{r['descripcion'][:70]}</b>
                        · <span style='color:{C_RED};font-weight:700'>Vencida hace {(date.today() - r["Finish"].date())} día(s)</span>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — REGISTROS
# ══════════════════════════════════════════════════════════════════════════════
with t5:
    busq     = st.text_input("🔍  Buscar",
                             placeholder="descripción, notas, marca...")
    df_tabla = df_f.copy()
    if busq:
        mask     = (df_tabla["descripcion"].str.contains(busq, case=False, na=False) |
                    df_tabla["notas"].str.contains(busq, case=False, na=False))
        df_tabla = df_tabla[mask]

    st.markdown(f"<div class='section-title'>{len(df_tabla)} registros</div>",
                unsafe_allow_html=True)

    def row_color(row):
        estado = str(row["estado"])
        if estado == "Completada":   bg = "#D1FAE5"  # verde
        elif estado == "En progreso": bg = "#FEF9C3"  # amarillo
        elif estado == "Bloqueada":   bg = "#FEE2E2"  # rojo
        else:                         bg = "#F8FAFC"  # gris claro (Pendiente)
        return [f"background-color:{bg}"] * len(row)

    styled = (df_tabla.sort_values("fecha", ascending=False)
              .drop(columns=["creado_en"])
              .style.apply(row_color, axis=1))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("⬇️ CSV", df_tabla.to_csv(index=False, sep=";").encode(),
                           "tareas.csv", "text/csv", use_container_width=True)
    with dl2:
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_tabla.to_excel(w, index=False, sheet_name="Tareas")
            st.download_button("⬇️ Excel", buf.getvalue(), "tareas.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except ImportError:
            st.caption("Para Excel: `pip install openpyxl`")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — GESTIONAR
# ══════════════════════════════════════════════════════════════════════════════
with t6:
    st.markdown("<div class='section-title'>Editar · Actualizar · Eliminar</div>",
                unsafe_allow_html=True)
    if df_f.empty:
        st.info("No hay tareas con los filtros actuales.")
    else:
        for _, row in df_f.sort_values("fecha", ascending=False).head(30).iterrows():
            rid   = int(row["id"])
            tc    = COLOR_ESTADO.get(row["estado"], C_GRAY)
            label = f"#{rid} · {row['fecha']} · {row['tipo']} — {row['descripcion'][:55]}"
            with st.expander(label):
                with st.form(f"edit_{rid}"):
                    ea, eb = st.columns(2)
                    with ea:
                        nf   = st.date_input("📅 Inicio",     value=pd.to_datetime(row["fecha"]).date(), key=f"f_{rid}")
                        nfl  = st.date_input("🏁 Fecha límite",
                                             value=pd.to_datetime(row["fecha_limite"]).date() if pd.notna(row["fecha_limite"]) else date.today() + timedelta(days=7),
                                             key=f"fl_{rid}")
                        nu   = st.selectbox("Asignado a",  USUARIOS,    index=USUARIOS.index(row["usuario"])       if row["usuario"]    in USUARIOS    else 0, key=f"u_{rid}")
                        nt   = sel_o_escribe("Tipo",  TIPOS,  f"t_{rid}",  ea)
                        ne   = st.selectbox("Estado", ESTADOS, index=ESTADOS.index(row["estado"]) if row["estado"] in ESTADOS else 0, key=f"e_{rid}")
                    with eb:
                        nm   = sel_o_escribe("Marca", MARCAS, f"m_{rid}", eb)
                        np_  = sel_o_escribe("País",  PAISES, f"p_{rid}", eb)
                        npr  = st.selectbox("Prioridad",   PRIORIDADES, index=PRIORIDADES.index(row["prioridad"])  if row["prioridad"]   in PRIORIDADES else 1, key=f"pr_{rid}")
                    nd  = st.text_area("Descripción", value=row["descripcion"], key=f"d_{rid}")
                    ec2, ed2 = st.columns(2)
                    ntr = ec2.number_input("Tiempo real (min)",  min_value=0, value=int(row["tiempo_min"]),          step=15, key=f"tr_{rid}")
                    nte = ed2.number_input("Estimado (min)",     min_value=0, value=int(row["tiempo_estimado_min"]), step=15, key=f"te_{rid}")
                    nno = st.text_input("Notas / link", value=str(row["notas"]) if row["notas"] else "", key=f"no_{rid}")
                    ba, bb = st.columns(2)
                    guardar = ba.form_submit_button("💾 Guardar", use_container_width=True, type="primary")
                    borrar  = bb.form_submit_button("🗑️ Eliminar", use_container_width=True)

                if guardar:
                    actualizar_tarea(rid, {
                        "fecha": nf, "fecha_limite": nfl,
                        "usuario": nu, "tipo": nt,
                        "marca": nm, "pais": np_, "descripcion": nd.strip(),
                        "prioridad": npr, "estado": ne,
                        "tiempo_min": ntr, "tiempo_estimado_min": nte,
                        "notas": nno.strip(),
                    })
                    st.success("✅ Actualizado")
                    st.rerun()
                if borrar:
                    eliminar_tarea(rid)
                    st.rerun()

        if len(df_f) > 30:
            st.caption(f"Mostrando 30 de {len(df_f)}. Usa filtros para acotar.")
