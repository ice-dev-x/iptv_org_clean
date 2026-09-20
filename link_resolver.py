import urllib.request
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def get_rtu_stream():
    """Extrae el stream de RTU desde su página oficial en vivo"""
    url = "https://canalrtu.tv/envivo/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': HEADERS['User-Agent'], 'Referer': url})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Buscar enlaces .m3u8 de MakroDigital o Nimble en el código
            match = re.search(r'https?://video1\.makrodigital\.com/[^"\']+\.m3u8[^"\']*', html)
            if match:
                return match.group(0)
    except Exception as e:
        print(f"[RTU] Error: {e}")
    return None

def get_teleamazonas_stream():
    """Extrae el stream de Teleamazonas"""
    url = "https://www.teleamazonas.com/en-vivo/"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Busca cualquier coincidencia de archivo .m3u8 en la página
            match = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html)
            if match:
                return match.group(0)
    except Exception as e:
        print(f"[Teleamazonas] Error: {e}")
    return None

def main():
    resolved_channels = {}
    
    print("--- RESOLVIENDO CANALES DINÁMICOS ---")
    
    rtu = get_rtu_stream()
    if rtu:
        print(f"✓ RTU resuelto: {rtu}")
        resolved_channels["RTU"] = rtu
    else:
        print("✗ No se pudo resolver RTU")
        
    teleamazonas = get_teleamazonas_stream()
    if teleamazonas:
        print(f"✓ Teleamazonas resuelto: {teleamazonas}")
        resolved_channels["Teleamazonas"] = teleamazonas

    # Guarda los enlaces encontrados en un archivo temporal JSON
    with open("resolved_streams.json", "w", encoding="utf-8") as f:
        json.dump(resolved_channels, f, indent=4)

if __name__ == "__main__":
    main()