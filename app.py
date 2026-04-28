import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="SA Construcción Iglesia", page_icon="⛪", layout="wide")

CARPETA_DATOS = "datos_iglesia"
CARPETA_IMAGENES = f"{CARPETA_DATOS}/facturas"
ARCHIVO_DB = f"{CARPETA_DATOS}/datos.db"

if not os.path.exists(CARPETA_DATOS):
    os.makedirs(CARPETA_DATOS)
if not os.path.exists(CARPETA_IMAGENES):
    os.makedirs(CARPETA_IMAGENES)

def init_db():
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS donaciones
                 (id INTEGER PRIMARY KEY, fecha TEXT, donante TEXT, monto REAL, metodo TEXT, notas TEXT, imagen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gastos
                 (id INTEGER PRIMARY KEY, fecha TEXT, descripcion TEXT, categoria TEXT, monto REAL, proveedor TEXT, imagen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS etapas
                 (id INTEGER PRIMARY KEY, nombre TEXT, descripcion TEXT, presupuesto REAL, 
                  avance INTEGER DEFAULT 0, estado TEXT DEFAULT 'pendiente', fecha_inicio TEXT, fecha_fin TEXT)''')
    
    # Agregar columnas si no existen (para bases de datos existentes)
    try:
        c.execute("ALTER TABLE donaciones ADD COLUMN imagen TEXT")
    except:
        pass
    try:
        c.execute("ALTER TABLE gastos ADD COLUMN imagen TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()

def get_etapas():
    conn = sqlite3.connect(ARCHIVO_DB)
    df = pd.read_sql_query("SELECT * FROM etapas ORDER BY id", conn)
    conn.close()
    return df

def agregar_etapa(nombre, descripcion, presupuesto, fecha_inicio, fecha_fin):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("INSERT INTO etapas (nombre, descripcion, presupuesto, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?)",
              (nombre, descripcion, presupuesto, fecha_inicio, fecha_fin))
    conn.commit()
    conn.close()

def actualizar_avance(etapa_id, avance):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    estado = 'completado' if avance == 100 else 'en_progreso' if avance > 0 else 'pendiente'
    c.execute("UPDATE etapas SET avance = ?, estado = ? WHERE id = ?", (avance, estado, etapa_id))
    conn.commit()
    conn.close()

def actualizar_donacion(id_val, fecha, donante, monto, metodo, notas):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("UPDATE donaciones SET fecha = ?, donante = ?, monto = ?, metodo = ?, notas = ? WHERE id = ?",
              (fecha, donante, monto, metodo, notas, id_val))
    conn.commit()
    conn.close()

def actualizar_gasto(id_val, fecha, descripcion, categoria, monto, proveedor):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("UPDATE gastos SET fecha = ?, descripcion = ?, categoria = ?, monto = ?, proveedor = ? WHERE id = ?",
              (fecha, descripcion, categoria, monto, proveedor, id_val))
    conn.commit()
    conn.close()

def actualizar_etapa(id_val, nombre, descripcion, presupuesto, fecha_inicio, fecha_fin):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("UPDATE etapas SET nombre = ?, descripcion = ?, presupuesto = ?, fecha_inicio = ?, fecha_fin = ? WHERE id = ?",
              (nombre, descripcion, presupuesto, fecha_inicio, fecha_fin, id_val))
    conn.commit()
    conn.close()

def eliminar_etapa(etapa_id):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("DELETE FROM etapas WHERE id = ?", (etapa_id,))
    conn.commit()
    conn.close()

def get_donaciones():
    conn = sqlite3.connect(ARCHIVO_DB)
    df = pd.read_sql_query("SELECT * FROM donaciones ORDER BY fecha DESC", conn)
    conn.close()
    return df

def get_gastos():
    conn = sqlite3.connect(ARCHIVO_DB)
    df = pd.read_sql_query("SELECT * FROM gastos ORDER BY fecha DESC", conn)
    conn.close()
    return df

def agregar_donacion(fecha, donante, monto, metodo, notas, imagen=None):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("INSERT INTO donaciones (fecha, donante, monto, metodo, notas, imagen) VALUES (?, ?, ?, ?, ?, ?)",
              (fecha, donante, monto, metodo, notas, imagen))
    conn.commit()
    conn.close()
    return c.lastrowid

def guardar_imagen(uploaded_file, prefijo):
    if uploaded_file is not None and uploaded_file.name:
        ext = uploaded_file.name.split('.')[-1]
        nombre_archivo = f"{prefijo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        ruta = os.path.join(CARPETA_IMAGENES, nombre_archivo)
        with open(ruta, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return nombre_archivo
    return None

def eliminar_imagen(nombre_archivo):
    if nombre_archivo:
        ruta = os.path.join(CARPETA_IMAGENES, nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)

def agregar_gasto(fecha, descripcion, categoria, monto, proveedor, imagen=None):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute("INSERT INTO gastos (fecha, descripcion, categoria, monto, proveedor, imagen) VALUES (?, ?, ?, ?, ?, ?)",
              (fecha, descripcion, categoria, monto, proveedor, imagen))
    conn.commit()
    conn.close()
    return c.lastrowid

def eliminar_registro(tabla, id_val):
    conn = sqlite3.connect(ARCHIVO_DB)
    c = conn.cursor()
    c.execute(f"DELETE FROM {tabla} WHERE id = ?", (id_val,))
    conn.commit()
    conn.close()

def generar_pdf():
    donativos = get_donaciones()
    gastos = get_gastos()
    
    total_donaciones = donativos['monto'].sum() if not donativos.empty else 0
    total_gastos = gastos['monto'].sum() if not gastos.empty else 0
    saldo = total_donaciones - total_gastos
    
    nombre_archivo = f"{CARPETA_DATOS}/reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()
    
    elementos.append(Paragraph("Reporte de Construcción - Iglesia", estilos['Title']))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))
    elementos.append(Paragraph(" ", estilos['Normal']))
    
    elementos.append(Paragraph("RESUMEN FINANCIERO", estilos['Heading2']))
    datos_resumen = [
        ["Total Donaciones", f"${total_donaciones:,.2f}"],
        ["Total Gastos", f"${total_gastos:,.2f}"],
        ["SALDO", f"${saldo:,.2f}"]
    ]
    tabla_resumen = Table(datos_resumen, colWidths=[200, 150])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.green),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOLD', (0, -1), (-1, -1), True),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Paragraph(" ", estilos['Normal']))
    
    if not donativos.empty:
        elementos.append(Paragraph("DONACIONES", estilos['Heading2']))
        df_don = donativos[['fecha', 'donante', 'monto', 'metodo', 'notas']].copy()
        df_don.columns = ['Fecha', 'Donante', 'Monto', 'Método', 'Notas']
        data_don = [list(df_don.columns)] + df_don.values.tolist()
        tabla_don = Table(data_don)
        tabla_don.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabla_don)
        elementos.append(Paragraph(" ", estilos['Normal']))
    
    if not gastos.empty:
        elementos.append(Paragraph("GASTOS", estilos['Heading2']))
        df_gas = gastos[['fecha', 'descripcion', 'categoria', 'monto', 'proveedor']].copy()
        df_gas.columns = ['Fecha', 'Descripción', 'Categoría', 'Monto', 'Proveedor']
        data_gas = [list(df_gas.columns)] + df_gas.values.tolist()
        tabla_gas = Table(data_gas)
        tabla_gas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#922b21')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabla_gas)
    
    doc.build(elementos)
    return nombre_archivo

st.markdown("""
<style>
    /* Colores modernos */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #06b6d4;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
    }
    
    /* Fondo principal mejorado */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        background-attachment: fixed;
    }
    
    /* Glassmorphism - Efecto vidrio líquido */
    .glass {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Glassmorphism fuerte */
    .glass-strong {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* Botones modernos con glass */
    .stButton>button {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.8) 0%, rgba(139, 92, 246, 0.8) 100%);
        color: white;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5);
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    }
    
    /* Título principal con glow */
    .titulo-principal {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
        text-shadow: 0 0 40px rgba(99, 102, 241, 0.5);
    }
    
    /* Cards con glassmorphism */
    .stMetric {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Sidebar con glass */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Inputs con glass */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        border-radius: 12px;
        border: 2px solid rgba(99, 102, 241, 0.3);
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: white;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.3);
    }
    
    /* Expander con glass */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        color: white;
    }
    
    /* DataFrames con glass */
    [data-testid="stDataFrame"] {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Divider personalizado */
    .stDivider {
        border-color: rgba(99, 102, 241, 0.3);
    }
    
    /* Efecto de partículas flotantes */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="titulo-principal">⛪ SA Construcción Iglesia</p>', unsafe_allow_html=True)

init_db()

# Detectar modo de solo visualización desde URL
query_params = st.query_params
modo_solo_lectura = query_params.get("view") == "true"

if modo_solo_lectura:
    st.markdown("""
    <div style="background: rgba(99, 102, 241, 0.2); padding: 10px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        👁️ <b>Modo Solo Visualización</b> - Los datos son de solo lectura
    </div>
    """, unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menú", ["Dashboard", "Donaciones", "Gastos", "Proyecto", "Descargar PDF"])

# Generar enlace para compartir (solo lectura)
st.sidebar.divider()
st.sidebar.subheader("🔗 Compartir")
url_solo_lectura = f"{st.query_params.get('server_url', 'http://localhost:8501')}?view=true"
st.sidebar.code(url_solo_lectura, language=None)
st.sidebar.caption("Copia este enlace para compartir en modo solo visualización")

if menu == "Dashboard":
    donativos = get_donaciones()
    gastos = get_gastos()
    
    total_donaciones = donativos['monto'].sum() if not donativos.empty else 0
    total_gastos = gastos['monto'].sum() if not gastos.empty else 0
    saldo = total_donaciones - total_gastos
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Donaciones", f"${total_donaciones:,.2f}", "💚")
    with col2:
        st.metric("Total Gastos", f"${total_gastos:,.2f}", "🔴", delta_color="inverse")
    with col3:
        st.metric("SALDO", f"${saldo:,.2f}", delta=f"${saldo:,.2f}")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📊 Ingresos vs Egresos")
        if not donativos.empty or not gastos.empty:
            df_grafico = pd.DataFrame({
                'Tipo': ['Ingresos', 'Egresos'],
                'Monto': [total_donaciones, total_gastos]
            })
            fig = px.pie(df_grafico, values='Monto', names='Tipo', 
                        color=['#10b981', '#ef4444'],
                        hole=0.4, title="📊 Distribución General")
            fig.update_traces(textinfo='percent+label', textfont=dict(size=14, color='white'))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title=dict(font=dict(size=18, color='white'))
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos registrados aún")
    
    with c2:
        st.subheader("📈 Evolución Financiera")
        if not donativos.empty or not gastos.empty:
            df_linea = pd.DataFrame()
            if not donativos.empty:
                donativos['tipo'] = 'Ingreso'
                donativos['acumulado'] = donativos['monto'].cumsum()
                df_linea = donativos[['fecha', 'acumulado', 'tipo']].copy()
            if not gastos.empty:
                gastos['tipo'] = 'Gasto'
                gastos['acumulado_neg'] = -gastos['monto'].cumsum()
                if df_linea.empty:
                    df_linea = gastos[['fecha', 'acumulado_neg', 'tipo']].copy()
                else:
                    df_linea = pd.concat([df_linea, gastos[['fecha', 'acumulado_neg', 'tipo']]])
            
            if not df_linea.empty:
                df_linea = df_linea.sort_values('fecha')
                fig2 = px.line(df_linea, x='fecha', y='acumulado' if 'acumulado' in str(df_linea.columns) else 'acumulado_neg', 
                              markers=True, title="💹 Acumulado en el Tiempo")
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white')),
                    title=dict(font=dict(size=18, color='white'))
                )
                fig2.update_traces(line=dict(color='#6366f1', width=3))
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos registrados aún")
    
    if not gastos.empty:
        st.divider()
        st.subheader("🏗️ Gastos por Categoría")
        cat_gastos = gastos.groupby('categoria')['monto'].sum().reset_index()
        fig3 = px.bar(cat_gastos, x='categoria', y='monto', 
                     color='monto', color_continuous_scale='Viridis',
                     title="📊 Gastos por Categoría")
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white')),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white')),
            title=dict(font=dict(size=18, color='white'))
        )
        st.plotly_chart(fig3, use_container_width=True)

elif menu == "Donaciones":
    st.header("💚 Registro de Donaciones")
    
    if not modo_solo_lectura:
        with st.form("form_donacion"):
            c1, c2 = st.columns(2)
            with c1:
                fecha = st.date_input("Fecha", datetime.now())
                donante = st.text_input("Nombre del Donante")
                imagen = st.file_uploader("📎 Subir Factura/Comprobante", type=['png', 'jpg', 'jpeg', 'pdf'])
            with c2:
                monto = st.number_input("Monto ($)", min_value=0.0, step=100.0)
                metodo = st.selectbox("Método", ["Efectivo", "Transferencia", "Cheque", "Otro"])
            notas = st.text_area("Notas (opcional)")
            enviado = st.form_submit_button("Registrar Donación")
            
            if enviado and donante and monto > 0:
                nombre_imagen = guardar_imagen(imagen, f"donacion_{donante.replace(' ', '_')}")
                agregar_donacion(fecha.strftime("%Y-%m-%d"), donante, monto, metodo, notas, nombre_imagen)
                st.success("✅ Donación registrada!")
                st.rerun()
    else:
        st.info("👁️ En modo solo visualización no puedes registrar nuevas donaciones")
    
    st.divider()
    st.subheader("📋 Historial de Donaciones")
    donativos = get_donaciones()
    if not donativos.empty:
        for i, row in donativos.iterrows():
            with st.expander(f"📥 {row['fecha']} - {row['donante']} - ${row['monto']:,.2f}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Método:** {row['metodo']}")
                    st.write(f"**Notas:** {row['notas'] if row['notas'] else 'Sin notas'}")
                    if row.get('imagen'):
                        ruta_img = os.path.join(CARPETA_IMAGENES, row['imagen'])
                        if os.path.exists(ruta_img):
                            st.image(ruta_img, caption="Factura/Comprobante", width=300)
                with col2:
                    col3, col4 = st.columns(2)
                    with col3:
                        if not modo_solo_lectura and st.button("✏️", key=f"edit_don_{row['id']}", help="Editar"):
                            st.session_state[f'editando_donacion_{row["id"]}'] = True
                    with col4:
                        if not modo_solo_lectura and st.button("🗑️", key=f"del_don_{row['id']}"):
                            if row.get('imagen'):
                                eliminar_imagen(row['imagen'])
                            eliminar_registro("donaciones", row['id'])
                            st.rerun()
                
                # Formulario de edición
                if st.session_state.get(f'editando_donacion_{row["id"]}', False):
                    st.divider()
                    with st.form(f"form_edit_don_{row['id']}"):
                        st.write("✏️ **Editar Donación**")
                        c1, c2 = st.columns(2)
                        with c1:
                            fecha_edit = st.date_input("Fecha", datetime.strptime(row['fecha'], '%Y-%m-%d'), key=f"fecha_don_{row['id']}")
                            donante_edit = st.text_input("Donante", row['donante'], key=f"donante_don_{row['id']}")
                        with c2:
                            monto_edit = st.number_input("Monto ($)", min_value=0.0, value=float(row['monto']), step=100.0, key=f"monto_don_{row['id']}")
                            metodo_edit = st.selectbox("Método", ["Efectivo", "Transferencia", "Cheque", "Otro"], 
                                                       index=["Efectivo", "Transferencia", "Cheque", "Otro"].index(row['metodo']) if row['metodo'] in ["Efectivo", "Transferencia", "Cheque", "Otro"] else 0,
                                                       key=f"metodo_don_{row['id']}")
                        notas_edit = st.text_area("Notas", row['notas'] if row['notas'] else '', key=f"notas_don_{row['id']}")
                        
                        c3, c4 = st.columns(2)
                        with c3:
                            guardar = st.form_submit_button("💾 Guardar")
                        with c4:
                            cancelar = st.form_submit_button("❌ Cancelar")
                        
                        if guardar:
                            actualizar_donacion(row['id'], fecha_edit.strftime("%Y-%m-%d"), donante_edit, monto_edit, metodo_edit, notas_edit)
                            st.success("✅ Donación actualizada!")
                            st.session_state[f'editando_donacion_{row["id"]}'] = False
                            st.rerun()
                        if cancelar:
                            st.session_state[f'editando_donacion_{row["id"]}'] = False
                            st.rerun()
    else:
        st.info("No hay donaciones registradas")

elif menu == "Gastos":
    st.header("🔴 Registro de Gastos")
    
    if not modo_solo_lectura:
        with st.form("form_gasto"):
            c1, c2 = st.columns(2)
            with c1:
                fecha = st.date_input("Fecha", datetime.now())
                descripcion = st.text_input("Descripción")
                imagen = st.file_uploader("📎 Subir Factura/Comprobante", type=['png', 'jpg', 'jpeg', 'pdf'])
            with c2:
                categoria = st.selectbox("Categoría", ["Materiales", "Mano de Obra", "Herramientas", "Transporte", "Permisos", "Otros"])
                monto = st.number_input("Monto ($)", min_value=0.0, step=100.0)
            proveedor = st.text_input("Proveedor (opcional)")
            enviado = st.form_submit_button("Registrar Gasto")
            
            if enviado and descripcion and monto > 0:
                nombre_imagen = guardar_imagen(imagen, f"gasto_{descripcion.replace(' ', '_')}")
                agregar_gasto(fecha.strftime("%Y-%m-%d"), descripcion, categoria, monto, proveedor, nombre_imagen)
                st.success("✅ Gasto registrado!")
                st.rerun()
    else:
        st.info("👁️ En modo solo visualización no puedes registrar nuevos gastos")
    
    st.divider()
    st.subheader("📋 Historial de Gastos")
    gastos = get_gastos()
    if not gastos.empty:
        for i, row in gastos.iterrows():
            with st.expander(f"📤 {row['fecha']} - {row['descripcion']} - ${row['monto']:,.2f}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Categoría:** {row['categoria']}")
                    st.write(f"**Proveedor:** {row['proveedor'] if row['proveedor'] else 'No especificado'}")
                    if row.get('imagen'):
                        ruta_img = os.path.join(CARPETA_IMAGENES, row['imagen'])
                        if os.path.exists(ruta_img):
                            st.image(ruta_img, caption="Factura/Comprobante", width=300)
                with col2:
                    col3, col4 = st.columns(2)
                    with col3:
                        if not modo_solo_lectura and st.button("✏️", key=f"edit_gas_{row['id']}", help="Editar"):
                            st.session_state[f'editando_gasto_{row["id"]}'] = True
                    with col4:
                        if not modo_solo_lectura and st.button("🗑️", key=f"del_gas_{row['id']}"):
                            if row.get('imagen'):
                                eliminar_imagen(row['imagen'])
                            eliminar_registro("gastos", row['id'])
                            st.rerun()
                
                # Formulario de edición
                if st.session_state.get(f'editando_gasto_{row["id"]}', False):
                    st.divider()
                    with st.form(f"form_edit_gas_{row['id']}"):
                        st.write("✏️ **Editar Gasto**")
                        c1, c2 = st.columns(2)
                        categorias = ["Materiales", "Mano de Obra", "Herramientas", "Transporte", "Permisos", "Otros"]
                        with c1:
                            fecha_edit = st.date_input("Fecha", datetime.strptime(row['fecha'], '%Y-%m-%d'), key=f"fecha_gas_{row['id']}")
                            descripcion_edit = st.text_input("Descripción", row['descripcion'], key=f"desc_gas_{row['id']}")
                            categoria_edit = st.selectbox("Categoría", categorias, 
                                                          index=categorias.index(row['categoria']) if row['categoria'] in categorias else 0,
                                                          key=f"cat_gas_{row['id']}")
                        with c2:
                            monto_edit = st.number_input("Monto ($)", min_value=0.0, value=float(row['monto']), step=100.0, key=f"monto_gas_{row['id']}")
                            proveedor_edit = st.text_input("Proveedor", row['proveedor'] if row['proveedor'] else '', key=f"prov_gas_{row['id']}")
                        
                        c3, c4 = st.columns(2)
                        with c3:
                            guardar = st.form_submit_button("💾 Guardar")
                        with c4:
                            cancelar = st.form_submit_button("❌ Cancelar")
                        
                        if guardar:
                            actualizar_gasto(row['id'], fecha_edit.strftime("%Y-%m-%d"), descripcion_edit, categoria_edit, monto_edit, proveedor_edit)
                            st.success("✅ Gasto actualizado!")
                            st.session_state[f'editando_gasto_{row["id"]}'] = False
                            st.rerun()
                        if cancelar:
                            st.session_state[f'editando_gasto_{row["id"]}'] = False
                            st.rerun()
    else:
        st.info("No hay gastos registrados")

elif menu == "Proyecto":
    st.header("🏗️ Seguimiento del Proyecto")
    st.write("Administra las etapas de construcción de la iglesia")
    
    # Agregar nueva etapa
    if not modo_solo_lectura:
        with st.expander("➕ Agregar Nueva Etapa"):
            with st.form("form_etapa"):
                c1, c2 = st.columns(2)
                with c1:
                    nombre_etapa = st.text_input("Nombre de la Etapa")
                    presupuesto = st.number_input("Presupuesto ($)", min_value=0.0, step=100.0)
                with c2:
                    descripcion = st.text_area("Descripción")
                    fecha_inicio = st.date_input("Fecha de Inicio", datetime.now())
                
                fecha_fin = st.date_input("Fecha de Fin Estimada", datetime.now())
                
                if st.form_submit_button("➕ Agregar Etapa"):
                    if nombre_etapa and presupuesto > 0:
                        agregar_etapa(nombre_etapa, descripcion, presupuesto, str(fecha_inicio), str(fecha_fin))
                        st.success("✅ Etapa agregada correctamente")
                        st.rerun()
                    else:
                        st.error("⚠️ Ingresa el nombre y presupuesto de la etapa")
    else:
        st.info("👁️ En modo solo visualización no puedes agregar nuevas etapas")
    
    st.divider()
    
    # Mostrar etapas
    etapas = get_etapas()
    
    if not etapas.empty:
        # Resumen de progreso
        total_presupuesto = etapas['presupuesto'].sum()
        promedio_avance = etapas['avance'].mean()
        etapas_completadas = len(etapas[etapas['estado'] == 'completado'])
        etapas_en_progreso = len(etapas[etapas['estado'] == 'en_progreso'])
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Etapas", len(etapas))
        with c2:
            st.metric("Presupuesto Total", f"${total_presupuesto:,.2f}")
        with c3:
            st.metric("Completadas", etapas_completadas, f"{etapas_completadas}/{len(etapas)}")
        with c4:
            st.metric("Avance Promedio", f"{promedio_avance:.1f}%")
        
        st.divider()
        
        # Barra de progreso general
        st.subheader("📊 Progreso General del Proyecto")
        st.progress(int(promedio_avance), text=f"Avance total: {promedio_avance:.1f}%")
        
        st.divider()
        
        # Listado de etapas
        st.subheader("📋 Etapas del Proyecto")
        
        for i, row in etapas.iterrows():
            # Color según estado
            if row['estado'] == 'completado':
                color_emoji = "✅"
                color_bar = "#10b981"
            elif row['estado'] == 'en_progreso':
                color_emoji = "🔄"
                color_bar = "#6366f1"
            else:
                color_emoji = "⏳"
                color_bar = "#64748b"
            
            with st.expander(f"{color_emoji} {row['nombre']} - {row['avance']}%"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Descripción:** {row['descripcion'] if row['descripcion'] else 'Sin descripción'}")
                    st.write(f"**Presupuesto:** ${row['presupuesto']:,.2f}")
                    st.write(f"**Fecha inicio:** {row['fecha_inicio']}")
                    st.write(f"**Fecha fin estimada:** {row['fecha_fin']}")
                    st.progress(row['avance'] / 100, text=f"Avance: {row['avance']}%")
                with c2:
                    col3, col4 = st.columns(2)
                    with col3:
                        if not modo_solo_lectura and st.button("✏️", key=f"edit_etapa_{row['id']}", help="Editar"):
                            st.session_state[f'editando_etapa_{row["id"]}'] = True
                    with col4:
                        if not modo_solo_lectura and st.button("🗑️", key=f"del_etapa_{row['id']}"):
                            eliminar_etapa(row['id'])
                            st.rerun()
                
                # Slider para actualizar avance (solo si no es solo lectura)
                if modo_solo_lectura:
                    st.write(f"**Avance:** {row['avance']}%")
                else:
                    nuevo_avance = st.slider(f"Avance %", 0, 100, row['avance'], key=f"avance_{row['id']}")
                    if nuevo_avance != row['avance']:
                        actualizar_avance(row['id'], nuevo_avance)
                        st.rerun()
                
                # Formulario de edición
                if st.session_state.get(f'editando_etapa_{row["id"]}', False):
                    st.divider()
                    with st.form(f"form_edit_etapa_{row['id']}"):
                        st.write("✏️ **Editar Etapa**")
                        c1, c2 = st.columns(2)
                        with c1:
                            nombre_edit = st.text_input("Nombre", row['nombre'], key=f"nom_etapa_{row['id']}")
                            presupuesto_edit = st.number_input("Presupuesto ($)", min_value=0.0, value=float(row['presupuesto']), step=100.0, key=f"pres_etapa_{row['id']}")
                        with c2:
                            descripcion_edit = st.text_area("Descripción", row['descripcion'] if row['descripcion'] else '', key=f"desc_etapa_{row['id']}")
                        
                        c3, c4 = st.columns(2)
                        with c3:
                            fecha_inicio_edit = st.date_input("Fecha de Inicio", datetime.strptime(row['fecha_inicio'], '%Y-%m-%d') if row['fecha_inicio'] else datetime.now(), key=f"ini_etapa_{row['id']}")
                        with c4:
                            fecha_fin_edit = st.date_input("Fecha de Fin", datetime.strptime(row['fecha_fin'], '%Y-%m-%d') if row['fecha_fin'] else datetime.now(), key=f"fin_etapa_{row['id']}")
                        
                        c5, c6 = st.columns(2)
                        with c5:
                            guardar = st.form_submit_button("💾 Guardar")
                        with c6:
                            cancelar = st.form_submit_button("❌ Cancelar")
                        
                        if guardar:
                            actualizar_etapa(row['id'], nombre_edit, descripcion_edit, presupuesto_edit, 
                                          str(fecha_inicio_edit), str(fecha_fin_edit))
                            st.success("✅ Etapa actualizada!")
                            st.session_state[f'editando_etapa_{row["id"]}'] = False
                            st.rerun()
                        if cancelar:
                            st.session_state[f'editando_etapa_{row["id"]}'] = False
                            st.rerun()
        
        # Gráfico de progreso por etapa
        st.divider()
        st.subheader("📈 Distribución del Presupuesto por Etapa")
        
        if not etapas.empty:
            fig_etapas = px.bar(etapas, x='nombre', y='presupuesto', 
                               color='avance', color_continuous_scale='Viridis',
                               title="Presupuesto por Etapa")
            fig_etapas.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white')),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='white'))
            )
            st.plotly_chart(fig_etapas, use_container_width=True)
    else:
        st.info("No hay etapas registradas. Agrega la primera etapa del proyecto.")

elif menu == "Descargar PDF":
    st.header("📄 Generar Reporte PDF")
    
    st.write("Genera un reporte completo con todos los datos registrados para compartilhar con los hermanos.")
    
    donativos = get_donaciones()
    gastos = get_gastos()
    
    total_donaciones = donativos['monto'].sum() if not donativos.empty else 0
    total_gastos = gastos['monto'].sum() if not gastos.empty else 0
    saldo = total_donaciones - total_gastos
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Donaciones", f"${total_donaciones:,.2f}")
    with col2:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    with col3:
        st.metric("SALDO", f"${saldo:,.2f}")
    
    st.divider()
    
    if modo_solo_lectura:
        st.info("👁️ En modo solo visualización no puedes generar PDFs")
    elif st.button("📥GENERAR Y DESCARGAR PDF"):
        archivo = generar_pdf()
        st.success(f"✅ Reporte generado: {archivo}")
        with open(archivo, "rb") as pdf:
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf,
                file_name=f"reporte_iglesia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

st.markdown("---")
st.caption("📅 SA Construcción Iglesia | Para compartir en red local: `streamlit run app.py --server.address 0.0.0.0`")