import xml.etree.ElementTree as ET

def normalize(input_svg, output_svg, src_img_path=None, canvas_w=1180, canvas_h=1180, margin=100):
    """
    Ajusta y centra el SVG generado dentro de un lienzo con dimensiones 
    y márgenes personalizados.
    """
    tree = ET.parse(input_svg)
    root = tree.getroot()
    
    # Obtener el viewBox original
    viewbox = root.get('viewBox')
    if viewbox:
        _, _, orig_w, orig_h = map(float, viewbox.split())
    else:
        orig_w = float(root.get('width', canvas_w))
        orig_h = float(root.get('height', canvas_h))
        
    # Calcular área útil disponible descontando los márgenes
    usable_w = canvas_w - (2 * margin)
    usable_h = canvas_h - (2 * margin)
    
    # Calcular el factor de escala manteniendo la relación de aspecto
    scale = min(usable_w / orig_w, usable_h / orig_h)
    
    scaled_w = orig_w * scale
    scaled_h = orig_h * scale
    
    # Calcular desfase para centrar el gráfico en el nuevo lienzo
    tx = margin + (usable_w - scaled_w) / 2.0
    ty = margin + (usable_h - scaled_h) / 2.0
    
    # Crear nuevo elemento raíz SVG con el tamaño exacto solicitado
    svg_ns = "http://www.w3.org/2000/svg"
    new_root = ET.Element('svg', {
        'xmlns': svg_ns,
        'width': str(canvas_w),
        'height': str(canvas_h),
        'viewBox': f"0 0 {canvas_w} {canvas_h}"
    })
    
    # Crear grupo contenedor con la transformación aplicada
    g = ET.SubElement(new_root, 'g', {
        'transform': f"translate({tx:.2f}, {ty:.2f}) scale({scale:.4f})"
    })
    
    # Copiar todos los elementos del SVG original dentro del grupo
    for child in root:
        g.append(child)
        
    new_tree = ET.ElementTree(new_root)
    new_tree.write(output_svg, encoding='utf-8', xml_declaration=True)