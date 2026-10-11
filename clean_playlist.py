import urllib.request
import re
import json
import hashlib
import unicodedata
import os

DEFAULT_LOGO = "https://i.ibb.co/d4wr01bB/tv.webp"
RAW_BASE = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/"

# URLs de Pluto TV
PLUTO_URLS = {
    "Pluto TV México": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_mx.m3u",
    "Pluto TV Argentina": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_ar.m3u",
    "Pluto TV España": "https://raw.githubusercontent.com/BuddyChewChew/pluto/main/pluto_es.m3u"
}

# Nueva URL de Samsung TV Plus
SAMSUNG_URL = "https://raw.githubusercontent.com/BuddyChewChew/samsungtvplus/refs/heads/main/output/samsung_tvplus.m3u"

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

    # 1. Leer Canales Propios Locales
    if os.path.exists("propios.m3u"):
        print("Procesando canales propios...")
        with open("propios.m3u", "r", encoding="utf-8") as f:
            agregar_items(parse_m3u(f.readlines()))
    
    # 2. Leer Pluto TV
    for group_name, url in PLUTO_URLS.items():
        agregar_items(parse_m3u(fetch_lines(url), override_group=group_name))
        
    # 3. Leer Samsung TV Plus (Agrupado en una sola categoría)
    agregar_items(parse_m3u(fetch_lines(SAMSUNG_URL), override_group="Samsung TV Plus"))
        
    # 4. Leer Países Latam
    for code, country_name in LATAM_COUNTRIES.items():
        url = f"{RAW_BASE}{code}.m3u"
        agregar_items(parse_m3u(fetch_lines(url), override_group=country_name))
        
    catalogo_final = list(todas_las_categorias.values())
    
    # Guardamos el JSON para Kino
    with open("catalogo.json", "w", encoding="utf-8") as f:
        json.dump(catalogo_final, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] catalogo.json generado para Kino.")

    # Guardamos el M3U para tu celular
    with open("latam.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for categoria in catalogo_final:
            grupo = categoria["title"]
            for canal in categoria["items"]:
                f.write(f'#EXTINF:-1 tvg-id="{canal["id"]}" tvg-logo="{canal["logo"]}" group-title="{grupo}",{canal["title"]}\n')
                f.write(f'{canal["ref"]}\n')
    print(f"[OK] latam.m3u generado para tu celular.")

if __name__ == "__main__":
    main()