import streamlit as st
from tracer import trace_svg
from normalize import normalize
import os
import uuid
import zipfile
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Vectorizador Pro", page_icon="⚡", layout="centered")
st.markdown("# ⚡ Vectorizador Pro")
st.write("Sube tus imágenes para convertirlas a SVG limpio con procesado inteligente.")

# --- SECCIÓN DE CONFIGURACIÓN DE RESOLUCIÓN Y MEDIDAS ---
with st.expander("📐 Ajustes de Lienzo y Exportación", expanded=False):
    preset = st.selectbox(
        "Tamaño del lienzo de salida",
        [
            "1180 x 1180 (Assets / 3D)",
            "1080 x 1080 (Cuadrado Estándar)",
            "1920 x 1080 (Full HD Horizontal)",
            "512 x 512 (Textura / Icono)",
            "Personalizado"
        ]
    )
    
    col_w, col_h, col_m = st.columns(3)
    
    if preset == "1180 x 1180 (Assets / 3D)":
        canvas_w, canvas_h = 1180, 1180
    elif preset == "1080 x 1080 (Cuadrado Estándar)":
        canvas_w, canvas_h = 1080, 1080
    elif preset == "1920 x 1080 (Full HD Horizontal)":
        canvas_w, canvas_h = 1920, 1080
    elif preset == "512 x 512 (Textura / Icono)":
        canvas_w, canvas_h = 512, 512
    else:  # Personalizado
        with col_w:
            canvas_w = st.number_input("Ancho (px)", min_value=100, max_value=8192, value=1180, step=10)
        with col_h:
            canvas_h = st.number_input("Alto (px)", min_value=100, max_value=8192, value=1180, step=10)

    # Margen interno
    with col_m if preset != "Personalizado" else st.container():
        margin = st.slider("Margen interior (px)", min_value=0, max_value=300, value=100, step=5)

files = st.file_uploader("Selecciona una o varias imágenes", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

custom_name = ""
if files and len(files) == 1:
    custom_name = st.text_input("Nombre del SVG (Opcional)", placeholder="Dejar vacío para usar el nombre original")

if files and st.button("⚡ Vectorizar Automáticamente", type="primary"):
    with st.spinner("Procesando vectorización y ajustando dimensiones del lienzo..."):
        
        # CASO 1: Un solo archivo
        if len(files) == 1:
            f = files[0]
            uid = uuid.uuid4().hex
            src = f'tmp_{uid}.png'
            raw_svg = f'raw_{uid}.svg'
            out_svg = f'out_{uid}.svg'
            
            name_input = custom_name.strip()
            final_name = (name_input if name_input.lower().endswith('.svg') else f"{name_input}.svg") if name_input else f"{f.name.rsplit('.', 1)[0]}.svg"
                
            try:
                img = Image.open(f).convert('RGBA')
                bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                bg.paste(img, (0, 0), img)
                bg.convert('RGB').save(src, 'PNG')

                trace_svg(src, raw_svg)
                normalize(raw_svg, out_svg, src, canvas_w=canvas_w, canvas_h=canvas_h, margin=margin)
                
                with open(out_svg, "rb") as file:
                    st.session_state['download_bytes'] = file.read()
                
                st.session_state['download_filename'] = final_name
                st.session_state['download_mime'] = "image/svg+xml"
                st.success(f"¡Vectorización completada! Generado a {canvas_w}x{canvas_h} px.")
                
            except Exception as e:
                st.error(f"Error durante el proceso: {e}")
            finally:
                for tmp in [src, raw_svg, out_svg]:
                    if os.path.exists(tmp): os.remove(tmp)

        # CASO 2: Procesamiento por lotes (ZIP)
        else:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in files:
                    uid = uuid.uuid4().hex
                    src = f'tmp_{uid}.png'
                    raw_svg = f'raw_{uid}.svg'
                    out_svg = f'out_{uid}.svg'
                    file_svg_name = f"{f.name.rsplit('.', 1)[0]}.svg"
                    
                    try:
                        img = Image.open(f).convert('RGBA')
                        bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                        bg.paste(img, (0, 0), img)
                        bg.convert('RGB').save(src, 'PNG')

                        trace_svg(src, raw_svg)
                        normalize(raw_svg, out_svg, src, canvas_w=canvas_w, canvas_h=canvas_h, margin=margin)
                        zipf.write(out_svg, arcname=file_svg_name)
                    except Exception as e:
                        print(f"Error en archivo {f.name}: {e}")
                    finally:
                        for tmp in [src, raw_svg, out_svg]:
                            if os.path.exists(tmp): os.remove(tmp)
            
            st.session_state['download_bytes'] = zip_buffer.getvalue()
            st.session_state['download_filename'] = "lote_vectores.zip"
            st.session_state['download_mime'] = "application/zip"
            st.success("¡Lote completado!")

if 'download_bytes' in st.session_state and st.session_state['download_bytes']:
    st.download_button(
        label="📥 Descargar Resultado SVG",
        data=st.session_state['download_bytes'],
        file_name=st.session_state['download_filename'],
        mime=st.session_state['download_mime'],
        type="primary"
    )