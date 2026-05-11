"""
Dashboard BI - Gestión de Tareas Diarias
Disresa | Multi-usuario | Backend CSV
"""

import hashlib
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from pathlib import Path
import os

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="BI Tasks | Disresa",
    page_icon="📊",
    layout="wide",
)

# ============================================================
# AUTENTICACIÓN
# ============================================================
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
            entered_hash = hashlib.sha256(pwd.encode()).hexdigest()
            if entered_hash == st.secrets["PASSWORD_HASH"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    return False

if not _check_password():
    st.stop()

DATA_FILE = Path("tasks.csv")

USUARIOS = ["Chema", "Hugo", "Otro..."]
MARCAS = ["Skechers", "Cole Haan", "New Era", "Columbia",
          "Psycho Bunny", "47 Brand", "Fabletics", "Multi-marca", "N/A"]
PAISES = ["GT", "SV", "HN", "CR", "PA", "RD", "Regional", "N/A"]
TIPOS_TAREA = [
    "Reporte sell-through", "Automatización Python", "ETL / Airflow",
    "Reporte Excel", "Presentación PPT", "Email / Comunicación",
    "Data quality SAP", "Análisis ad-hoc", "Reunión", "Otro"
]
PRIORIDADES = ["🔴 Alta", "🟡 Media", "🟢 Baja"]
ESTADOS = ["Pendiente", "En progreso", "Completada", "Bloqueada"]

COLUMNAS = [
    "id", "fecha", "usuario", "tipo", "marca", "pais",
    "descripcion", "prioridad", "estado", "tiempo_min",
    "creado_en"
]

# ============================================================
# DATA LAYER
# ============================================================
def cargar_datos() -> pd.DataFrame:
    if not DATA_FILE.exists():
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_csv(DATA_FILE, index=False)
        return df
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    return df

def guardar_tarea(nueva: dict):
    df = cargar_datos()
    nueva["id"] = int(df["id"].max()) + 1 if not df.empty else 1
    nueva["creado_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def actualizar_estado(task_id: int, nuevo_estado: str):
    df = cargar_datos()
    df.loc[df["id"] == task_id, "estado"] = nuevo_estado
    df.to_csv(DATA_FILE, index=False)

def eliminar_tarea(task_id: int):
    df = cargar_datos()
    df = df[df["id"] != task_id]
    df.to_csv(DATA_FILE, index=False)

# ============================================================
# SIDEBAR - INGRESO DE TAREAS
# ============================================================
with st.sidebar:
    st.header("➕ Nueva tarea")

    with st.form("form_tarea", clear_on_submit=True):
        fecha = st.date_input("Fecha", value=date.today())
        usuario = st.selectbox("Asignado a", USUARIOS)
        tipo = st.selectbox("Tipo de tarea", TIPOS_TAREA)
        col_a, col_b = st.columns(2)
        with col_a:
            marca = st.selectbox("Marca", MARCAS)
        with col_b:
            pais = st.selectbox("País", PAISES)
        descripcion = st.text_area("Descripción", placeholder="Breve detalle...")
        col_c, col_d = st.columns(2)
        with col_c:
            prioridad = st.selectbox("Prioridad", PRIORIDADES, index=1)
        with col_d:
            estado = st.selectbox("Estado", ESTADOS)
        tiempo_min = st.number_input("Tiempo invertido (min)", min_value=0, value=0, step=15)

        submitted = st.form_submit_button("Guardar tarea", use_container_width=True, type="primary")

        if submitted:
            if not descripcion.strip():
                st.error("La descripción no puede estar vacía.")
            else:
                guardar_tarea({
                    "fecha": fecha,
                    "usuario": usuario,
                    "tipo": tipo,
                    "marca": marca,
                    "pais": pais,
                    "descripcion": descripcion.strip(),
                    "prioridad": prioridad,
                    "estado": estado,
                    "tiempo_min": int(tiempo_min),
                })
                st.success("✅ Tarea guardada")
                st.rerun()

    st.divider()
    st.caption(f"📁 Datos en: `{DATA_FILE.resolve()}`")

# ============================================================
# MAIN
# ============================================================
st.title("📊 Dashboard BI - Gestión de Tareas")
st.caption("Disresa | Tracking diario del equipo")

df = cargar_datos()

if df.empty:
    st.info("No hay tareas registradas todavía. Agrega la primera desde el panel lateral 👈")
    st.stop()

# ----- FILTROS -----
st.subheader("🔍 Filtros")
f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    f_usuario = st.multiselect("Usuario", sorted(df["usuario"].unique()))
with f2:
    f_tipo = st.multiselect("Tipo", sorted(df["tipo"].unique()))
with f3:
    f_marca = st.multiselect("Marca", sorted(df["marca"].unique()))
with f4:
    f_pais = st.multiselect("País", sorted(df["pais"].unique()))
with f5:
    f_estado = st.multiselect("Estado", sorted(df["estado"].unique()))

f6, f7 = st.columns(2)
with f6:
    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()
    rango = st.date_input("Rango de fechas", value=(fecha_min, fecha_max),
                          min_value=fecha_min, max_value=fecha_max)

# Aplicar filtros
df_f = df.copy()
if f_usuario: df_f = df_f[df_f["usuario"].isin(f_usuario)]
if f_tipo:    df_f = df_f[df_f["tipo"].isin(f_tipo)]
if f_marca:   df_f = df_f[df_f["marca"].isin(f_marca)]
if f_pais:    df_f = df_f[df_f["pais"].isin(f_pais)]
if f_estado:  df_f = df_f[df_f["estado"].isin(f_estado)]
if isinstance(rango, tuple) and len(rango) == 2:
    df_f = df_f[(df_f["fecha"] >= rango[0]) & (df_f["fecha"] <= rango[1])]

st.divider()

# ----- KPIs -----
k1, k2, k3, k4, k5 = st.columns(5)
total = len(df_f)
completadas = (df_f["estado"] == "Completada").sum()
pendientes = (df_f["estado"] == "Pendiente").sum()
bloqueadas = (df_f["estado"] == "Bloqueada").sum()
horas = df_f["tiempo_min"].sum() / 60

k1.metric("Total tareas", total)
k2.metric("Completadas", completadas, f"{(completadas/total*100):.0f}%" if total else "0%")
k3.metric("Pendientes", pendientes)
k4.metric("Bloqueadas", bloqueadas)
k5.metric("Horas invertidas", f"{horas:.1f}")

st.divider()

# ----- TABS -----
tab_resumen, tab_tabla, tab_gestionar = st.tabs(["📈 Resumen", "📋 Tabla", "⚙️ Gestionar"])

with tab_resumen:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Tareas por tipo**")
        por_tipo = df_f.groupby("tipo").size().reset_index(name="count").sort_values("count", ascending=True)
        fig = px.bar(por_tipo, x="count", y="tipo", orientation="h",
                     labels={"count": "Cantidad", "tipo": ""}, height=350)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Estado de tareas**")
        por_estado = df_f.groupby("estado").size().reset_index(name="count")
        fig = px.pie(por_estado, names="estado", values="count", hole=0.5, height=350)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown("**Tareas por marca**")
        por_marca = df_f.groupby("marca").size().reset_index(name="count").sort_values("count", ascending=False)
        fig = px.bar(por_marca, x="marca", y="count",
                     labels={"count": "Cantidad", "marca": ""}, height=350)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.markdown("**Horas por usuario**")
        horas_user = df_f.groupby("usuario")["tiempo_min"].sum().reset_index()
        horas_user["horas"] = horas_user["tiempo_min"] / 60
        fig = px.bar(horas_user, x="usuario", y="horas",
                     labels={"horas": "Horas", "usuario": ""}, height=350)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Tendencia diaria de tareas**")
    por_dia = df_f.groupby("fecha").size().reset_index(name="count")
    fig = px.line(por_dia, x="fecha", y="count", markers=True,
                  labels={"count": "Tareas", "fecha": ""}, height=300)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with tab_tabla:
    st.markdown(f"**{len(df_f)} tareas** (según filtros)")
    st.dataframe(
        df_f.sort_values("fecha", ascending=False).drop(columns=["creado_en"]),
        use_container_width=True,
        hide_index=True,
    )
    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV filtrado", csv, "tareas_filtradas.csv", "text/csv")

with tab_gestionar:
    st.markdown("**Actualizar estado o eliminar tareas**")
    if df_f.empty:
        st.info("No hay tareas con los filtros actuales.")
    else:
        for _, row in df_f.sort_values("fecha", ascending=False).head(20).iterrows():
            with st.expander(f"#{row['id']} | {row['fecha']} | {row['tipo']} - {row['descripcion'][:60]}"):
                cA, cB, cC, cD = st.columns([2, 2, 2, 1])
                cA.write(f"**Usuario:** {row['usuario']}")
                cA.write(f"**Marca/País:** {row['marca']} / {row['pais']}")
                cB.write(f"**Prioridad:** {row['prioridad']}")
                cB.write(f"**Tiempo:** {row['tiempo_min']} min")
                nuevo_estado = cC.selectbox(
                    "Estado", ESTADOS,
                    index=ESTADOS.index(row["estado"]),
                    key=f"est_{row['id']}"
                )
                if cC.button("Actualizar", key=f"upd_{row['id']}"):
                    actualizar_estado(int(row["id"]), nuevo_estado)
                    st.success("Actualizado")
                    st.rerun()
                if cD.button("🗑️", key=f"del_{row['id']}"):
                    eliminar_tarea(int(row["id"]))
                    st.rerun()
        if len(df_f) > 20:
            st.caption(f"Mostrando 20 de {len(df_f)}. Usa filtros para acotar.")
