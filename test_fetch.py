"""Run: python3 test_fetch.py. Checks feed parsing and the seen/age filter without network."""
import io, json, sys, tempfile, time, os
from contextlib import redirect_stdout
import fetch

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>New</title><link href="https://a/new"/><published>{now}</published><summary>&lt;b&gt;hi&lt;/b&gt;</summary></entry>
<entry><title>Seen</title><link href="https://a/seen"/><published>{now}</published></entry>
<entry><title>Old</title><link href="https://a/old"/><published>2001-01-01T00:00:00Z</published></entry>
</feed>""".format(now=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

d = tempfile.mkdtemp()
sources, seen = os.path.join(d, "sources.tsv"), os.path.join(d, "seen.json")
with open(sources, "w") as f:
    f.write("rss\tTest\thttps://a/feed\nrss\tBroken\thttps://b/feed\n")
with open(seen, "w") as f:
    json.dump(["https://a/seen"], f)

fetch.get = lambda url: ATOM if url.startswith("https://a") else (_ for _ in ()).throw(OSError("down"))
sys.argv = ["fetch.py", sources, seen, "3"]
buf = io.StringIO()
with redirect_stdout(buf):
    fetch.main()
out = json.loads(buf.getvalue())

assert [i["url"] for i in out["items"]] == ["https://a/new"], out
assert out["items"][0]["summary"] == "hi"
assert out["errors"] == ["Broken: down"], out["errors"]
print("ok")
