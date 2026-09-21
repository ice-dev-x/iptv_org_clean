import urllib.request
import re

RAW_BASE = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/"

# 1. LISTA DE PAÍSES (Aquí ya agregamos España y Estados Unidos)
LATAM_COUNTRIES = {
    "ar": "Argentina", "bo": "Bolivia", "br": "Brasil", "cl": "Chile", 
    "co": "Colombia", "cr": "Costa Rica", "cu": "Cuba", "do": "República Dominicana", 
    "ec": "Ecuador", "sv": "El Salvador", "gt": "Guatemala", "hn": "Honduras", 
    "mx": "México", "ni": "Nicaragua", "pa": "Panamá", "py": "Paraguay", 
    "pe": "Perú", "pr": "Puerto Rico", "uy": "Uruguay", "ve": "Venezuela",
    "es": "España",
    "us": "Estados Unidos"
}

# 2. TUS ENLACES PERSONALIZADOS
# Pega aquí tus enlaces funcionales usando el formato estándar M3U. 
# Como se procesan primero, siempre serán la opción principal en tu reproductor.
MIS_CANALES_PROPIOS = """
#EXTINF:-1 tvg-id="Curiquingue Tv" group-title="Ecuador",Curiquinge TV (Mi Link VIP)
https://stream.ovalcast.com:5443/LiveApp/streams/wIZDyk6GTPuIpifQ868504716815490.m3u8


#EXTINF:-1 tvg-id="RTU.ec" group-title="Ecuador",RTU
#EXTVLCOPT:http-referrer=https://canalrtu.tv/
#EXTVLCOPT:http-user-agent=Mozilla/5.0
https://video1.makrodigital.com/rtu/rtu/playlist.m3u8


"""

def get_custom_lines():
    # Extrae tus canales personalizados ignorando las líneas en blanco
    return [line.strip() for line in MIS_CANALES_PROPIOS.split('\n') if line.strip()]

def download_content(url):
    print(f"Descargando {url} ...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8').splitlines()

def process_playlist(lines, output_file):
    seen_ids = {}
    seen_names = {}
    new_lines = []
    
    for line in lines:
        if line.startswith("#EXTINF:"):
            parts = line.split(",", 1)
            if len(parts) == 2:
                prefix = parts[0]
                channel_name = parts[1].strip()
                
                # Garantizar tvg-id único
                match_id = re.search(r'tvg-id="([^"]+)"', prefix)
                if match_id:
                    original_id = match_id.group(1)
                    seen_ids[original_id] = seen_ids.get(original_id, 0) + 1
                    if seen_ids[original_id] > 1:
                        new_id = f"{original_id}_{seen_ids[original_id]}"
                        prefix = re.sub(r'tvg-id="([^"]+)"', f'tvg-id="{new_id}"', prefix)

                # Garantizar nombres únicos
                seen_names[channel_name] = seen_names.get(channel_name, 0) + 1
                if seen_names[channel_name] > 1:
                    new_name = f"{channel_name} (Opcion {seen_names[channel_name]})"
                else:
                    new_name = channel_name
                
                new_line = f"{prefix},{new_name}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
                
        # Solución para el bug de iMPlayer (reemplaza comas en el disfraz)
        elif line.startswith("#EXTVLCOPT:"):
            line_limpia = line.replace(",", ";")
            new_lines.append(line_limpia)
        else:
            new_lines.append(line)
            
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in new_lines:
            f.write(line + "\n")
            
    print(f"[OK] {output_file} guardado exitosamente.\n")

def main():
    print("--- PROCESANDO LISTA GLOBAL CON CATEGORÍAS ---")
    latam_lines = ["#EXTM3U"]
    
    # 1. INYECTAMOS TUS CANALES PROPIOS PRIMERO
    latam_lines.extend(get_custom_lines())
    
    # 2. DESCARGAMOS EL RESTO DE PAÍSES
    for country_code, country_name in LATAM_COUNTRIES.items():
        url = f"{RAW_BASE}{country_code}.m3u"
        try:
            lines = download_content(url)
            for line in lines:
                if line.strip().upper() == "#EXTM3U":
                    continue
                
                if line.startswith("#EXTINF:"):
                    if 'group-title=' in line:
                        line = re.sub(r'group-title="[^"]*"', f'group-title="{country_name}"', line)
                    else:
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            line = f'{parts[0]} group-title="{country_name}",{parts[1]}'
                            
                latam_lines.append(line)
        except urllib.error.HTTPError:
            pass 
        except Exception as e:
            print(f"  -> Error con {country_name}: {e}")
            
    process_playlist(latam_lines, "latam.m3u")
    
    print("--- PROCESANDO ECUADOR INDIVIDUAL ---")
    try:
        ec_lines = ["#EXTM3U"]
        # INYECTAMOS TUS CANALES PROPIOS TAMBIÉN EN LA LISTA INDIVIDUAL
        ec_lines.extend(get_custom_lines())
        
        url = f"{RAW_BASE}ec.m3u"
        lines = download_content(url)
        for line in lines:
            if line.strip().upper() == "#EXTM3U":
                continue
            if line.startswith("#EXTINF:"):
                if 'group-title=' in line:
                    line = re.sub(r'group-title="[^"]*"', 'group-title="Ecuador"', line)
                else:
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        line = f'{parts[0]} group-title="Ecuador",{parts[1]}'
            ec_lines.append(line)
        process_playlist(ec_lines, "ecuador.m3u")
    except Exception as e:
        print(f"Error procesando Ecuador: {e}")

if __name__ == "__main__":
    main()