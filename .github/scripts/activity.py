"""Render assets/activity.svg: weekly contributions over the last 12 months."""
import json, os, sys, urllib.request
from datetime import date

USER = "rexhinokovaci"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def render(cal):
    weeks = [(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
             for w in cal["weeks"] if w["contributionDays"]]
    W, H, L, R, T, B = 840, 260, 48, 24, 56, 36
    pw, ph = W - L - R, H - T - B
    top = max(max(v for _, v in weeks), 1)
    step = 10 ** (len(str(top)) - 1)
    top = ((top + step - 1) // step) * step
    xs = [L + i * pw / (len(weeks) - 1) for i in range(len(weeks))]
    ys = [T + ph - v / top * ph for _, v in weeks]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"M{L},{T+ph} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys)) + f" L{xs[-1]:.1f},{T+ph} Z"
    grid = "".join(
        f"<line x1='{L}' x2='{W-R}' y1='{T+ph-f*ph:.1f}' y2='{T+ph-f*ph:.1f}' stroke='#8b949e' stroke-opacity='0.15'/>"
        f"<text x='{L-8}' y='{T+ph-f*ph+4:.1f}' font-size='11' text-anchor='end' fill='#8b949e'>{int(top*f)}</text>"
        for f in (0, 0.5, 1))
    months, seen = "", set()
    for (d, _), x in zip(weeks, xs):
        m = date.fromisoformat(d).strftime("%b")
        if date.fromisoformat(d).day <= 7 and m not in seen:
            seen.add(m)
            months += f"<text x='{x:.1f}' y='{H-12}' font-size='11' text-anchor='middle' fill='#8b949e'>{m}</text>"
    peak = max(range(len(weeks)), key=lambda i: weeks[i][1])
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}' font-family='-apple-system,Segoe UI,Helvetica,Arial,sans-serif'>
<defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#F38020' stop-opacity='0.35'/><stop offset='1' stop-color='#F38020' stop-opacity='0'/></linearGradient></defs>
<rect x='0.5' y='0.5' width='{W-1}' height='{H-1}' rx='10' fill='none' stroke='#8b949e' stroke-opacity='0.3'/>
<text x='28' y='34' font-size='15' font-weight='600' fill='#F38020'>Contributions, last 12 months</text>
<text x='{W-28}' y='34' font-size='12' text-anchor='end' fill='#8b949e'>{cal['totalContributions']:,} total · includes private repos · updated {date.today():%d %b %Y}</text>
{grid}{months}
<path d='{area}' fill='url(#g)'/>
<polyline points='{line}' fill='none' stroke='#F38020' stroke-width='2' stroke-linejoin='round'/>
<circle cx='{xs[peak]:.1f}' cy='{ys[peak]:.1f}' r='4' fill='#F38020'/>
<text x='{xs[peak]-8:.1f}' y='{ys[peak]+4:.1f}' font-size='11' text-anchor='end' fill='#8b949e'>{weeks[peak][1]} in a week</text>
</svg>
"""

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "activity.svg")
    with open(out, "w") as f:
        f.write(render(fetch()))
