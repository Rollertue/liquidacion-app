import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA EN pages/admin.py ---
st.set_page_config(
    page_title="Panel Admin - Inventario", 
    page_icon="🔐", 
    layout="wide",
    initial_sidebar_state="expanded"  # <-- Agrega esta línea
)

# --- LOGIN DE SEGURIDAD ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD_ADMIN"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Eliminar contraseña de session_state por seguridad
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido")
        st.text_input("Introduce la contraseña de administrador", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Acceso Restringido")
        st.text_input("Introduce la contraseña de administrador", type="password", on_change=password_entered, key="password")
        st.error("❌ Contraseña incorrecta.")
        return False
    return True

# Si la contraseña no es correcta, frena la ejecución aquí
if check_password():

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
            return pd.DataFrame(columns=["titulo", "descripcion", "precio", "imagen_url", "imagen_url_2", "imagen_url_3", "estado"])

    df_productos = cargar_productos()

    st.title("🔐 Panel de Control de Inventario")
    st.write("Gestioná tus productos de manera segura.")
    st.write("---")
    
    # --- FORMULARIO 1: NUEVO PRODUCTO ---
    st.subheader("➕ Agregar Nuevo Producto")
    with st.form(key="nuevo_producto_form", clear_on_submit=True):
        nuevo_titulo = st.text_input("Título del Producto (Debe ser único)")
        nueva_desc = st.text_area("Descripción o detalles")
        nuevo_precio = st.number_input("Precio ($)", min_value=0, step=100)
        
        nueva_img1 = st.text_input("URL de la Imagen Principal (Foto 1)")
        nueva_img2 = st.text_input("URL de la Imagen Secundaria (Foto 2 - Opcional)")
        nueva_img3 = st.text_input("URL de la Imagen Secundaria (Foto 3 - Opcional)")
        
        nuevo_estado = st.selectbox("Estado inicial", ["Disponible", "Reservado", "Vendido"])
        btn_crear = st.form_submit_button("Guardar Producto")
        
        if btn_crear:
            if nuevo_titulo and nuevo_precio:
                try:
                    data_insert = {
                        "titulo": nuevo_titulo,
                        "descripcion": nueva_desc,
                        "precio": nuevo_precio,
                        "imagen_url": nueva_img1,
                        "imagen_url_2": nueva_img2 if nueva_img2 else None,
                        "imagen_url_3": nueva_img3 if nueva_img3 else None,
                        "estado": nuevo_estado
                    }
                    supabase.table("productos").insert(data_insert).execute()
                    st.success(f"🎉 '{nuevo_titulo}' agregado con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.error("El título y el precio son obligatorios.")

    st.write("---")
    
    # --- FORMULARIO 2: MODIFICAR EXISTENTES ---
    st.subheader("✏️ Editar o Cambiar Estado / Precio de un Producto")
    if df_productos.empty:
        st.info("No hay productos para modificar.")
    else:
        lista_titulos = df_productos["titulo"].tolist()
        prod_seleccionado = st.selectbox("Seleccioná el producto que querés modificar", lista_titulos)
        datos_prod = df_productos[df_productos["titulo"] == prod_seleccionado].iloc[0]
        
        with st.form(key="editar_producto_form"):
            st.info(f"Modificando: {prod_seleccionado}")
            edit_desc = st.text_area("Editar Descripción", value=datos_prod["descripcion"])
            edit_precio = st.number_input("Editar Precio ($)", min_value=0, step=100, value=int(datos_prod["precio"]))
            
            edit_img1 = st.text_input("Editar URL Imagen 1", value=str(datos_prod["imagen_url"]) if pd.notna(datos_prod["imagen_url"]) else "")
            edit_img2 = st.text_input("Editar URL Imagen 2", value=str(datos_prod["imagen_url_2"]) if ('imagen_url_2' in datos_prod and pd.notna(datos_prod["imagen_url_2"])) else "")
            edit_img3 = st.text_input("Editar URL Imagen 3", value=str(datos_prod["imagen_url_3"]) if ('imagen_url_3' in datos_prod and pd.notna(datos_prod["imagen_url_3"])) else "")
            
            edit_estado = st.selectbox(
                "Cambiar Estado de Publicación", 
                ["Disponible", "Reservado", "Vendido"],
                index=["Disponible", "Reservado", "Vendido"].index(datos_prod["estado"].strip().capitalize())
            )
            btn_actualizar = st.form_submit_button("Actualizar Cambios")
            
            if btn_actualizar:
                try:
                    data_update = {
                        "descripcion": edit_desc,
                        "precio": edit_precio,
                        "imagen_url": edit_img1,
                        "imagen_url_2": edit_img2 if edit_img2 else None,
                        "imagen_url_3": edit_img3 if edit_img3 else None,
                        "estado": edit_estado
                    }
                    supabase.table("productos").update(data_update).eq("titulo", prod_seleccionado).execute()
                    st.success(f"✅ '{prod_seleccionado}' actualizado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")
