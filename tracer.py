import os
import cv2
import numpy as np
from PIL import Image
import vtracer

def process_traffic_sign(input_path):
    """
    Procesador optimizado específicamente para señales de tráfico:
    - Mantiene bordes ultra-nítidos entre colores primarios (Rojo/Amarillo/Blanco).
    - Aplasta reflejos de pantalla y sombras sobre siluetas negras (coches/símbolos/texto).
    """
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        raise ValueError("No se pudo cargar la imagen")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 1. Filtro bilateral suave: Elimina ruido de sensor/pantalla sin desdibujar bordes
    smooth = cv2.bilateralFilter(img_rgb, d=7, sigmaColor=25, sigmaSpace=25)

    # 2. Cuantización K-Means estricta (4 colores: Fondo, Rojo, Amarillo, Negro)
    img_lab = cv2.cvtColor(smooth, cv2.COLOR_RGB2LAB)
    pixels = img_lab.reshape((-1, 3)).astype(np.float32)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
    k = 4
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # 3. Localizar el cluster del tono oscuro/negro
    darkest_cluster_idx = np.argmin(centers[:, 0])
    
    centers_uint8 = np.uint8(centers)
    quantized_lab = centers_uint8[labels.flatten()].reshape(img_lab.shape)
    quantized_rgb = cv2.cvtColor(quantized_lab, cv2.COLOR_LAB2RGB)

    # 4. Máscara morfológica: Sella reflejos internos dentro de coches o textos
    dark_mask = (labels.flatten() == darkest_cluster_idx).reshape(img_lab.shape[:2]).astype(np.uint8) * 255
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed_dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel)

    # Asignar negro sólido a toda la máscara sellada
    dark_color_rgb = cv2.cvtColor(np.uint8([[centers_uint8[darkest_cluster_idx]]]), cv2.COLOR_LAB2RGB)[0][0]
    quantized_rgb[closed_dark_mask == 255] = dark_color_rgb

    # 5. Limpieza de píxeles huérfanos en fronteras
    cleaned_rgb = cv2.medianBlur(quantized_rgb, 3)

    return Image.fromarray(cleaned_rgb)


def trace_svg(input_path, output_path):
    clean_pil_img = process_traffic_sign(input_path)
    
    temp_clean_path = input_path + "_sign_clean.png"
    clean_pil_img.save(temp_clean_path)
    
    # Vectorización ajustada a geometrías de señalización
    vtracer.convert_image_to_svg_py(
        temp_clean_path,
        output_path,
        colormode='color',
        color_precision=4,
        layer_difference=32,     # Evita capas intermedias o sombras fantasma
        hierarchical='stacked',
        mode='spline',
        filter_speckle=4,        # Elimina motas sin comerse el texto "TP-31"
        corner_threshold=45,     # Esquinas limpias en el triángulo
        length_threshold=4.0,    # Curvas uniformes en los coches
        splice_threshold=40
    )
    
    if os.path.exists(temp_clean_path):
        os.remove(temp_clean_path)