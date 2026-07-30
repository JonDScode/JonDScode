"""Genera stats.svg y top-langs.svg para el README de perfil.

Sin servicios de terceros: consulta la API de GitHub y renderiza SVGs propios
con el branding del portafolio (fondo #0a0a0f, cian #6ee7f7, violeta #a78bfa).
Los ejecuta la Action stats.yml (diaria) y commitea el resultado.

Uso local:  GITHUB_TOKEN=$(gh auth token) python scripts/gen_stats.py
"""
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

USER = "JonDScode"
ROOT = Path(__file__).resolve().parent.parent

BG, BORDER, TITLE, TEXT, MUTED, ACCENT2 = (
    "#0a0a0f", "#1f2937", "#6ee7f7", "#f0f0f5", "#9ca3af", "#a78bfa",
)

LANG_COLORS = {
    "Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#563d7c", "Java": "#b07219",
}


def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch() -> dict:
    user = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]
    langs = Counter()
    for r in own:
        for lang, size in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[lang] += size
    return {
        "followers": user["followers"],
        "repos": len(own),
        "stars": sum(r["stargazers_count"] for r in repos),
        "forks": sum(r["forks_count"] for r in own),
        "langs": langs,
    }


def stats_svg(d: dict) -> str:
    rows = [
        ("Repos propios", d["repos"]),
        ("Stars", d["stars"]),
        ("Followers", d["followers"]),
        ("Forks recibidos", d["forks"]),
    ]
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 62 + i * 26
        lines.append(f'<text x="24" y="{y}" fill="{MUTED}" font-size="13">{label}</text>')
        lines.append(
            f'<text x="266" y="{y}" fill="{TEXT}" font-size="13" font-weight="600" text-anchor="end">{value}</text>'
        )
    return f'''<svg width="290" height="180" viewBox="0 0 290 180" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI', Ubuntu, sans-serif">
  <rect x="0.5" y="0.5" width="289" height="179" rx="6" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="32" fill="{TITLE}" font-size="14" font-weight="600" font-family="'Cascadia Code', 'Courier New', monospace">// github_stats</text>
  {chr(10).join(lines)}
</svg>
'''


def langs_svg(d: dict) -> str:
    top = d["langs"].most_common(6)
    total = sum(v for _, v in top) or 1
    bar_w, bar_x, bar_y = 342, 24, 48
    x = bar_x
    segments, legend = [], []
    for i, (lang, size) in enumerate(top):
        w = size / total * bar_w
        color = LANG_COLORS.get(lang, ACCENT2)
        segments.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w, 2):.1f}" height="10" fill="{color}"/>')
        x += w
        col, row = i % 2, i // 2
        lx, ly = bar_x + col * 171, 84 + row * 24
        pct = size / total * 100
        legend.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>')
        legend.append(
            f'<text x="{lx + 16}" y="{ly}" fill="{TEXT}" font-size="12">{lang} '
            f'<tspan fill="{MUTED}">{pct:.1f}%</tspan></text>'
        )
    return f'''<svg width="390" height="180" viewBox="0 0 390 180" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI', Ubuntu, sans-serif">
  <rect x="0.5" y="0.5" width="389" height="179" rx="6" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="32" fill="{TITLE}" font-size="14" font-weight="600" font-family="'Cascadia Code', 'Courier New', monospace">// lenguajes</text>
  <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>
  <g clip-path="url(#bar)">{''.join(segments)}</g>
  {chr(10).join(legend)}
</svg>
'''


def main() -> None:
    d = fetch()
    (ROOT / "stats.svg").write_text(stats_svg(d), encoding="utf-8")
    (ROOT / "top-langs.svg").write_text(langs_svg(d), encoding="utf-8")
    print(f"OK: repos={d['repos']} stars={d['stars']} followers={d['followers']} "
          f"langs={[l for l, _ in d['langs'].most_common(6)]}")


if __name__ == "__main__":
    main()
