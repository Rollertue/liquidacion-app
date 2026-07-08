import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_connection()

def cargar_productos():
    try:
        respuesta = supabase.table("productos").select("*").execute()
        if respuesta.data and len(respuesta.data) > 0:
            df = pd.DataFrame(respuesta.data)
            df.columns = df.columns.str.lower()
            return df
        return pd.DataFrame(columns=["titulo", "descripcion", "precio", "imagen_url", "imagen_url_2", "imagen_url_3", "estado"])
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame(columns=["titulo", "descripcion", "precio", "imagen_url", "imagen_url_2", "imagen_url_3", "estado"])

# --- FUNCIÓN QUE CONTIENE TODO EL CATÁLOGO PÚBLICO ---
def mostrar_catalogo():
    st.title("🍳 Gran Liquidación por Cierre de Casa Chowa")
    st.markdown("Consulta en tiempo real la disponibilidad de los artículos. Coordina la compra o envía una oferta directa por WhatsApp.")
    st.write("---")

    df_productos = cargar_productos()
    TELEFONO_VENTAS = st.secrets["TELEFONO_VENTAS"]

    if df_productos.empty:
        st.info("No hay productos cargados en el catálogo actualmente.")
    else:
        if "titulo" in df_productos.columns:
            df_productos = df_productos.sort_values(by="titulo")
        df_productos = df_productos.reset_index(drop=True)
        
        columnas = st.columns(3)
        
        for index, row in df_productos.iterrows():
            col = columnas[index % 3]
            with col:
                with st.container(border=True):
                    # Imagen Principal
                    url_img = row['imagen_url'] if pd.notna(row['imagen_url']) and row['imagen_url'] else "https://via.placeholder.com/300"
                    st.image(url_img, use_container_width=True)
                    
                    # Miniaturas secundarias
                    tiene_img2 = 'imagen_url_2' in row and pd.notna(row['imagen_url_2']) and row['imagen_url_2']
                    tiene_img3 = 'imagen_url_3' in row and pd.notna(row['imagen_url_3']) and row['imagen_url_3']
                    
                    if tiene_img2 or tiene_img3:
                        sub_cols = st.columns(3)
                        with sub_cols[0]:
                            st.image(url_img, caption="Foto 1", use_container_width=True)
                        if tiene_img2:
                            with sub_cols[1]:
                                st.image(row['imagen_url_2'], caption="Foto 2", use_container_width=True)
                        if tiene_img3:
                            with sub_cols[2]:
                                st.image(row['imagen_url_3'], caption="Foto 3", use_container_width=True)
                    
                    # Información del producto
                    st.subheader(row['titulo'])
                    st.markdown(f"### **${int(row['precio']):,}**")
                    st.write(row['descripcion'])
                    
                    estado = str(row['estado']).strip().capitalize()
                    if estado == "Disponible":
                        st.success("🟢 Disponible")
                    elif estado == "Reservado":
                        st.warning("🟡 Reservado")
                    else:
                        st.error("🔴 Vendido")
                    
                    es_vendido = estado == "Vendido"
                    es_reservado = estado == "Reservado"
                    
                    st.write("") 
                    
                    # Botón Consultar
                    msg_consulta = f"Hola, estoy interesado en: *{row['titulo']}*. ¿Sigue disponible?"
                    url_consulta = f"https://wa.me/{TELEFONO_VENTAS}?text={urllib.parse.quote(msg_consulta)}"
                    st.link_button("📱 Consultar Disponibilidad", url_consulta, disabled=es_vendido, use_container_width=True)
                    
                    # Botón Ofertar
                    if st.button("💰 Proponer una Oferta", key=f"btn_{row['titulo']}", disabled=(es_vendido or es_reservado), use_container_width=True):
                        st.session_state[f"oferta_activa_{row['titulo']}"] = True
                    
                    if st.session_state.get(f"oferta_activa_{row['titulo']}", False):
                        with st.form(key=f"form_{row['titulo']}", clear_on_submit=True):
                            nombre = st.text_input("Nombre Completo")
                            celular = st.text_input("Número de Contacto")
                            monto = st.number_input("Tu Propuesta Económica ($)", min_value=1, step=500)
                            
                            if st.form_submit_button("Confirmar Oferta"):
                                if nombre and celular and monto:
                                    msg_oferta = f"Hola, mi nombre es {nombre} (Cel: {celular}).\nQuiero ofertar por: *{row['titulo']}*.\nMi propuesta: *${monto:,.0f}*."
                                    url_oferta = f"https://wa.me/{TELEFONO_VENTAS}?text={urllib.parse.quote(msg_oferta)}"
                                    st.markdown(f"[👉 Presiona aquí para enviar por WhatsApp]({url_oferta})")
                                    st.session_state[f"oferta_activa_{row['titulo']}"] = False
                                else:
                                    st.error("Completa los campos requeridos.")

# --- CONTROL MANDATORIO DE NAVEGACIÓN ---
pagina_catalogo = st.Page(mostrar_catalogo, title="🛒 Catálogo Online", icon="🍳", default=True)
pagina_admin = st.Page("pages/admin.py", title="🔐 Panel de Administración", icon="🔐")

# Esto obliga a Streamlit a dibujar la barra lateral con las dos páginas
pg = st.navigation([pagina_catalogo, pagina_admin])
st.set_page_config(page_title="Liquidación Gastronómica", page_icon="🍳", layout="wide")
pg.run()
