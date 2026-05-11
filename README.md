# 📊 Dashboard BI - Gestión de Tareas

Dashboard de Streamlit para que el equipo registre y analice tareas diarias. Protegido con contraseña.

## Instalación

```bash
pip install -r requirements.txt
```

## Configurar contraseña

1. Copia el archivo de ejemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Genera el hash SHA-256 de tu contraseña:
   ```bash
   python3 -c "import hashlib; print(hashlib.sha256('TuContraseña'.encode()).hexdigest())"
   ```
3. Pega el hash en `.streamlit/secrets.toml`:
   ```toml
   PASSWORD_HASH = "el-hash-generado-aqui"
   ```

> La contraseña por defecto es `Disresa2025`. Cámbiala antes de compartir el app.

## Ejecutar

```bash
streamlit run BI.py
```

Se abre en `http://localhost:8501`.

## Compartir en el equipo

**Opción 1 — Red local:**
```bash
streamlit run BI.py --server.address=0.0.0.0 --server.port=8501
```
El equipo entra desde `http://TU_IP:8501`.

**Opción 2 — Streamlit Community Cloud (gratis):**
Push a GitHub → conectas en [share.streamlit.io](https://share.streamlit.io).
En la configuración de la app agrega el secreto `PASSWORD_HASH` desde la interfaz web (no en el código).

## Estructura del CSV

`tasks.csv` se crea automáticamente. Columnas:
`id, fecha, usuario, tipo, marca, pais, descripcion, prioridad, estado, tiempo_min, creado_en`

## Notas

- `tasks.csv` y `.streamlit/secrets.toml` están en `.gitignore` y **nunca se suben a GitHub**.
- Si dos personas escriben al mismo tiempo puede haber conflictos. Para volumen alto considera migrar a SQLite.
- Backup: copia `tasks.csv` periódicamente.
