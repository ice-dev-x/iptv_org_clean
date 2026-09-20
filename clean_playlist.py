import re
import urllib.request

PLAYLISTS = {
    "ecuador.m3u": "https://iptv-org.github.io/iptv/countries/ec.m3u",
    "latam.m3u": "https://iptv-org.github.io/iptv/regions/latam.m3u"
}

def clean_m3u(source_url: str, output_path: str):
    req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        content = response.read().decode("utf-8")

    lines = content.splitlines()
    seen_ids = set()
    processed_lines = []

    for line in lines:
        if line.startswith("#EXTINF:"):
            match = re.search(r'tvg-id="([^"]+)"', line)
            if match:
                tvg_id = match.group(1)
                if tvg_id in seen_ids:
                    line = re.sub(r'tvg-id="[^"]+"', 'tvg-id=""', line)
                elif tvg_id:
                    seen_ids.add(tvg_id)
        processed_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(processed_lines))
    print(f"[OK] Guardado correctamente en: {output_path}")

if __name__ == "__main__":
    for filename, url in PLAYLISTS.items():
        clean_m3u(url, filename)