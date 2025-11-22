from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def downloadFile(filename):
    url = f"https://sourceforge.net/p/tinyfiledialogs/code/ci/master/tree/{filename}?format=raw"
    out_path = Path.cwd() / filename
    req = Request(url, headers={"User-Agent": "python-urllib/3"})
    try:
        with urlopen(req) as resp:
            if getattr(resp, 'status', None) and resp.status >= 400:
                raise RuntimeError(f"HTTP error: {resp.status} {getattr(resp, 'reason', '')}")
            data = resp.read()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
                print(f"Downloaded {filename} to {out_path}")
    except HTTPError as e:
        raise RuntimeError(f"HTTP Error: {e.code} {e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"URL Error: {e.reason}") from e
    return str(out_path)

if __name__ == "__main__":
    downloadFile("tinyfiledialogs.h")
    downloadFile("tinyfiledialogs.c")
