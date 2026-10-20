import urllib.request
import re
import json
import hashlib
import unicodedata
import os

DEFAULT_LOGO = "https://i.ibb.co/kszxTgHm/B74-D2-F54-1693-4-DB5-AB5-F-80-AA15987-B7-A.png"
RAW_BASE = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/"

# ==========================================
# TUS CANALES PROPIOS (INTEGRADOS)
# ==========================================
MIS_CANALES_PROPIOS = """
#EXTINF:-1 tvg-id="DragonBall_24/7_1" tvg-name="DB/Z" tvg-logo="https://www.vertvcable.com/wp-content/uploads/2026/07/dagonballz.jpg" group-title="24/7 y más (Experimental)",Dragon Ball/DBZ 24/7
https://183.bozztv.com/giatv/giatv-dball/dball/playlist.m3u8

#EXTINF:-1 tvg-id="simpsons_1" tvg-name="simpsons" tvg-logo="" group-title="24/7 y más (Experimental)",Los Simpsons 24/7
https://live20.bozztv.com/akamaissh101/ssh101/simplat/playlist.m3u8

#EXTINF:-1 tvg-id="simpsons_2" tvg-name="simpsons" tvg-logo="" group-title="24/7 y más (Experimental)",Los Simpsons 24/7 (Op.2)
https://lbgo.bozztv.com/ssh101/ssh101/simptestnews/playlist.m3u8

#EXTINF:-1 tvg-id="caricaturas_1" tvg-name="caricaturas" tvg-logo="" group-title="24/7 y más (Experimental)",Caricaturas 24/7
https://lbgo.bozztv.com/ssh101/ssh101/tvwxfxxgo/playlist.m3u8

#EXTINF:-1 tvg-id="chavo_1" tvg-name="Chavo8" tvg-logo="" group-title="24/7 y más (Experimental)",Chavo del 8 24/7  
https://live20.bozztv.com/giatvplayout7/giatv-211465/playlist.m3u8

#EXTINF:-1 tvg-id="chespirito_1" tvg-name="Chespirito" tvg-logo="https://static.wikia.nocookie.net/logopedia/images/9/93/Chespirito_Cut_1617889980592.png" group-title="24/7 y más (Experimental)",Chespirito 24/7  
https://live20.bozztv.com/giatvplayout7/giatv-211111/playlist.m3u8

#EXTINF:-1 tvg-id="Locomotion_1" tvg-name="locomotion" tvg-logo="https://ibb.co/8gBHbjMs" group-title="24/7 y más (Experimental)",Locomotion
http://146.19.49.197:81/live/loco_hi/index.m3u8

#EXTINF:-1 tvg-id="magickids" tvg-name="Magic Kids" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/d/d6/Logomagic96.png" group-title="24/7 y más (Experimental)",Magic Kids
https://kiiroilabs.ddns.net/magickids/stream/stream.m3u8

#EXTINF:-1 tvg-id="Espn_1" tvg-name="ESPN" tvg-logo="http://cdn.iconscout.com/icon/free/png-512/free-espn-logo-icon-svg-download-png-461787.png" group-title="Deportes",ESPN
http://190.61.101.11:7050/play/a09k/index.m3u8?hls

#EXTINF:-1 tvg-id="Espn2" tvg-name="ESPN_2" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/ESPN2_logo.svg/960px-ESPN2_logo.svg.png" group-title="Deportes",ESPN 2
http://190.61.101.11:7050/play/a05c/index.m3u8?hls
"""

# URLs de Pluto TV
PLUTO_URLS = {
    "Pluto TV México": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_mx.m3u",
    "Pluto TV Argentina": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_ar.m3u",
    "Pluto TV España": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_es.m3u"
}

# Nueva URL de Samsung TV Plus
#SAMSUNG_URL = "https://raw.githubusercontent.com/BuddyChewChew/samsungtvplus/refs/heads/main/output/samsung_tvplus.m3u"

LATAM_COUNTRIES = {
    "ar": "Argentina", "bo": "Bolivia", "br": "Brasil", "cl": "Chile", 
    "co": "Colombia", "cr": "Costa Rica", "cu": "Cuba", "do": "República Dominicana", 
    "ec": "Ecuador", "sv": "El Salvador", "gt": "Guatemala", "hn": "Honduras", 
    "mx": "México", "ni": "Nicaragua", "pa": "Panamá", "py": "Paraguay", 
    "pe": "Perú", "pr": "Puerto Rico", "uy": "Uruguay", "ve": "Venezuela",
    "es": "España", "us": "Estados Unidos"#, "pt": "Portugal", "it": "Italia"
}

def normalize_id(text):
    text = unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9]', '-', text)

def fetch_lines(url):
    print(f"Descargando {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"  -> Error: {e}")
        return []

def parse_m3u(lines, override_group=None):
    items = []
    current_item = None
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith("#EXTINF:"):
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            group_match = re.search(r'group-title="([^"]+)"', line)
            name = line.split(',')[-1].strip() or "Canal Desconocido"
            
            logo = logo_match.group(1) if logo_match else ""
            if not logo or logo.strip() == "": 
                logo = DEFAULT_LOGO
                
            group = override_group if override_group else (group_match.group(1) if group_match else "Otros")
            
            current_item = {
                "title": name,
                "kind": "live",
                "logo": logo,
                "_groupName": group
            }
        elif line.startswith("http") and current_item:
            current_item["ref"] = line
            current_item["id"] = "ch-" + hashlib.sha1(line.encode('utf-8')).hexdigest()[:16]
            items.append(current_item)
            current_item = None
            
    return items

def main():
    todas_las_categorias = {}
    
    def agregar_items(items):
        for item in items:
            group_name = item.pop("_groupName")
            group_id = normalize_id(group_name)
            
            if group_id not in todas_las_categorias:
                todas_las_categorias[group_id] = {
                    "id": group_id,
                    "title": group_name,
                    "items": []
                }
            todas_las_categorias[group_id]["items"].append(item)

    # 1. Leer Canales Propios desde la variable integrada
    print("Procesando canales propios integrados...")
    lineas_propios = MIS_CANALES_PROPIOS.strip().split('\n')
    agregar_items(parse_m3u(lineas_propios))
    
    # 2. Leer Pluto TV
    for group_name, url in PLUTO_URLS.items():
        agregar_items(parse_m3u(fetch_lines(url), override_group=group_name))
        
    # 3. Leer Samsung TV Plus (Agrupado en una sola categoría)
    ##agregar_items(parse_m3u(fetch_lines(SAMSUNG_URL), override_group="Samsung TV Plus"))
        
    # 4. Leer Países Latam
    for code, country_name in LATAM_COUNTRIES.items():
        url = f"{RAW_BASE}{code}.m3u"
        agregar_items(parse_m3u(fetch_lines(url), override_group=country_name))
        
    catalogo_final = list(todas_las_categorias.values())
    
    # 1. Guardamos el JSON para Kino
    with open("catalogo.json", "w", encoding="utf-8") as f:
        json.dump(catalogo_final, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] catalogo.json generado para Kino.")

    # 2. Guardamos el M3U completo para tu celular
    with open("latam.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for categoria in catalogo_final:
            grupo = categoria["title"]
            for canal in categoria["items"]:
                f.write(f'#EXTINF:-1 tvg-id="{canal["id"]}" tvg-logo="{canal["logo"]}" group-title="{grupo}",{canal["title"]}\n')
                f.write(f'{canal["ref"]}\n')
    print(f"[OK] latam.m3u generado para tu celular.")

    # 3. Guardamos el M3U exclusivo de Ecuador
    with open("ecuador.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for categoria in catalogo_final:
            # Filtramos solo la categoría que se llame "Ecuador"
            if categoria["title"] == "Ecuador":
                grupo = categoria["title"]
                for canal in categoria["items"]:
                    f.write(f'#EXTINF:-1 tvg-id="{canal["id"]}" tvg-logo="{canal["logo"]}" group-title="{grupo}",{canal["title"]}\n')
                    f.write(f'{canal["ref"]}\n')
    print(f"[OK] ecuador.m3u generado exclusivo.")

if __name__ == "__main__":
    main()