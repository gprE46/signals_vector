import os
from tracer import trace_svg
from normalize import normalize

def batch_process(input_folder, output_folder, canvas=1180, margin=100):
    os.makedirs(output_folder, exist_ok=True)
    
    # Comprobar si hay imágenes en la carpeta de origen
    if not os.path.exists(input_folder) or not os.listdir(input_folder):
        print(f"Aviso: Mete las imágenes que quieras procesar en la carpeta '{input_folder}'")
        return

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        src = os.path.join(input_folder, filename)
        raw = f'temp_raw_{filename}.svg'
        out = os.path.join(output_folder, filename.rsplit('.', 1)[0] + '.svg')
        
        try:
            trace_svg(src, raw)
            normalize(raw, out, src, canvas, margin)
            print(f'✓ Procesado: {filename} -> {out}')
        except Exception as e:
            print(f'✗ Error con {filename}: {e}')
        finally:
            if os.path.exists(raw):
                os.remove(raw)

if __name__ == '__main__':
    # Crea automáticamente las carpetas si no existen para que no dé error
    os.makedirs('./origen', exist_ok=True)
    os.makedirs('./vectores', exist_ok=True)
    
    # Ejecuta el proceso por lotes
    print("Iniciando procesado por lotes...")
    batch_process('./origen', './vectores')