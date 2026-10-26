#!/usr/bin/env python3
"""Fetch new items from the digest sources.

Usage: fetch.py <sources.tsv> <seen.json> <days> > items.json

Prints {"items": [...], "errors": [...]}: items not in seen.json and (when dated) newer than <days>.
A source that fails goes into "errors"; the rest still run.
"""
import html, json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime

UA = {"User-Agent": "Mozilla/5.0"}
SUMMARY_MAX = 400


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()[:SUMMARY_MAX]


def ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        try:
            return parsedate_to_datetime(s).timestamp()
        except (TypeError, ValueError):
            return None


def feed(name, url):
    root = ET.fromstring(get(url))
    out = []
    for e in root.iter():
        tag = e.tag.split("}")[-1]
        if tag not in ("entry", "item"):
            continue
        f = {c.tag.split("}")[-1]: c for c in e}
        link = f.get("link")
        href = (link.get("href") or link.text) if link is not None else ""
        body = next((f[k].text for k in ("summary", "description", "content", "group") if k in f and f[k].text), "")
        if "group" in f:  # YouTube: media:group/media:description
            body = next((c.text for c in f["group"] if c.tag.endswith("description")), "") or ""
        date = next((f[k].text for k in ("published", "pubDate", "updated") if k in f), None)
        out.append({"source": name, "title": text(f["title"].text if "title" in f else ""),
                    "url": (href or "").strip(), "date": date, "ts": ts(date), "summary": text(body)})
    return out


def trending(name, url):
    page = get(url)
    out = []
    for art in page.split('<article class="Box-row">')[1:]:
        m = re.search(r'<h2 class="h3 lh-condensed">\s*<a[^>]*href="/([^"]+)"', art)
        if not m:
            continue
        desc = re.search(r'<p class="col-9[^"]*">(.*?)</p>', art, re.S)
        stars = re.search(r"([\d,]+) stars this week", art)
        out.append({"source": name, "title": m.group(1), "url": "https://github.com/" + m.group(1),
                    "date": None, "ts": None,
                    "summary": text(desc.group(1) if desc else "") + (f" ({stars.group(1)} stars this week)" if stars else "")})
    return out


def hn(name, url, since):
    q = urllib.parse.urlencode({"tags": "story", "hitsPerPage": 100,
                                "numericFilters": f"points>150,created_at_i>{int(since)}"})
    hits = json.loads(get(f"{url}?{q}"))["hits"]
    return [{"source": name, "title": h["title"], "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
             "date": h["created_at"], "ts": h["created_at_i"], "summary": f"{h['points']} points, {h['num_comments']} comments"}
            for h in hits]


def main():
    sources, seen_path, days = sys.argv[1], sys.argv[2], float(sys.argv[3])
    seen = set(json.load(open(seen_path)))
    since = time.time() - days * 86400
    items, errors = [], []
    for line in open(sources):
        if not line.strip() or line.startswith("#"):
            continue
        kind, name, url = line.rstrip("\n").split("\t")
        try:
            if kind == "rss":
                got = feed(name, url)
            elif kind == "youtube":
                got = feed(name, f"https://www.youtube.com/feeds/videos.xml?channel_id={url}")
            elif kind == "trending":
                got = trending(name, url)
            elif kind == "hn":
                got = hn(name, url, since)
            else:
                raise ValueError(f"unknown kind {kind}")
        except Exception as e:  # one broken source must not sink the run
            errors.append(f"{name}: {e}")
            continue
        items += [i for i in got if i["url"] and i["url"] not in seen and (i["ts"] is None or i["ts"] >= since)]
    for i in items:
        del i["ts"]
    json.dump({"items": items, "errors": errors}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
