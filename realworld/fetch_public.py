"""Fetch the pre-registered public documents (PREREG_REDTEAM.md S3). usage: python3 -I realworld/fetch_public.py (run from the idea folder). Writes realworld/raw/{arxiv,wiki}/ and realworld/MANIFEST_fetch.tsv."""
import os, re, json, time, random, hashlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET
H = os.path.dirname(os.path.abspath(__file__)); UA = {"User-Agent": "research-fetch/1.0 (public-document pilot; polite, 1 req/3s)"}
def get(u, binary=True):
    for i in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60); b = r.read(); return b
        except Exception as e: last = e; time.sleep(60 if '429' in str(e) else 5)
    raise last
rows = []
def save(kind, name, url, b):
    d = os.path.join(H, "raw", kind); os.makedirs(d, exist_ok=True); p = os.path.join(d, name); open(p, "wb").write(b)
    rows.append((kind, name, url, hashlib.sha256(b).hexdigest(), len(b), time.strftime("%F")))
CATS = ["cs.CL", "cs.CV", "math.NT", "physics.optics", "q-bio.NC", "stat.ML"]
ns = {"a": "http://www.w3.org/2005/Atom"}
for cat in CATS:
    q = urllib.parse.urlencode({"search_query": "cat:%s AND submittedDate:[202601010000 TO 202601312359]" % cat, "sortBy": "submittedDate", "sortOrder": "ascending", "max_results": 10})
    x = ET.fromstring(get("https://export.arxiv.org/api/query?" + q)); time.sleep(3)
    for e in x.findall("a:entry", ns):
        aid = e.find("a:id", ns).text.rsplit("/abs/", 1)[1]; u = "https://arxiv.org/pdf/" + aid
        fn = os.path.join(H, "raw", "arxiv", aid.replace("/", "_") + ".pdf")
        if os.path.exists(fn): b = open(fn, "rb").read(); rows.append(("arxiv", os.path.basename(fn), u, hashlib.sha256(b).hexdigest(), len(b), "2026-11-24")); continue
        try: save("arxiv", aid.replace("/", "_") + ".pdf", u, get(u))
        except Exception as ex: print("FAIL", u, ex)
        time.sleep(3)
# Wikipedia: deviation D1 from the prereg text (Vital-articles list not used): 40 deterministic prefixes -> first main-namespace non-redirect article at/after the prefix
rng = random.Random(20261125); import string; seen = set()
while len([r for r in rows if r[0] == "wiki"]) < 40:
    pre = "".join(rng.choice(string.ascii_uppercase) for _ in range(3))
    j = json.loads(get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "allpages", "apfrom": pre, "aplimit": 1, "apfilterredir": "nonredirects", "format": "json"}), True))
    if not j["query"]["allpages"]: continue
    t = j["query"]["allpages"][0]["title"]
    if t in seen: continue
    seen.add(t)
    fn = os.path.join(H, "raw", "wiki", re.sub(r"[^A-Za-z0-9]+", "_", t)[:80] + ".html")
    if os.path.exists(fn): b = open(fn, "rb").read(); rows.append(("wiki", os.path.basename(fn), "https://en.wikipedia.org/api/rest_v1/page/html/" + urllib.parse.quote(t.replace(" ", "_"), safe=""), hashlib.sha256(b).hexdigest(), len(b), "2026-11-24")); continue
    try: save("wiki", re.sub(r"[^A-Za-z0-9]+", "_", t)[:80] + ".html", "https://en.wikipedia.org/api/rest_v1/page/html/" + urllib.parse.quote(t.replace(" ", "_"), safe=""), get("https://en.wikipedia.org/api/rest_v1/page/html/" + urllib.parse.quote(t.replace(" ", "_"), safe="")))
    except Exception as ex: print("FAIL", t, ex)
    time.sleep(2)
with open(os.path.join(H, "MANIFEST_fetch.tsv"), "w") as f:
    f.write("kind\tfile\turl\tsha256\tbytes\tfetched\n"); [f.write("\t".join(map(str, r)) + "\n") for r in rows]
print(len(rows), "files")
