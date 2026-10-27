"""Download every public input once, cache it under data/cache/, and checksum it.

The first successful download of a file records its SHA-256 in data/MANIFEST.json (committed).
Later runs verify the cached file against that checksum; a mismatch is reported loudly and the
file is re-downloaded once. If the remote file itself has changed, the new hash is logged as a
warning in the run log rather than silently accepted.

Nothing here is hand-typed data. Numbers that only exist in papers are taken from the papers'
own LaTeX source (arXiv e-print) and parsed in data/loaders.py.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tarfile
import gzip
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
MANIFEST = os.path.join(HERE, "MANIFEST.json")

RAW = "https://raw.githubusercontent.com"
PBH = f"{RAW}/bradkav/PBHbounds/master/bounds"
PANTHEON = f"{RAW}/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_Data/4_DISTANCES_AND_COVAR"
BAO = f"{RAW}/CobayaSampler/bao_data/master"

# (key, url, local filename, description)
SOURCES = [
    ("sparc_rotmod", "https://astroweb.cwru.edu/SPARC/Rotmod_LTG.zip", "sparc/Rotmod_LTG.zip",
     "SPARC mass models: rotation curve + baryonic components, 175 galaxies (Lelli+2016)"),
    ("sparc_table", "https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt", "sparc/SPARC_Lelli2016c.mrt",
     "SPARC galaxy table (distance, inclination, quality, disk scale length, ...)"),
    ("desi_dr2_mean", f"{BAO}/desi_bao_dr2/desi_gaussian_bao_ALL_GCcomb_mean.txt", "desi/dr2_mean.txt",
     "DESI DR2 BAO (arXiv:2503.14738) Gaussian likelihood mean, as distributed for Cobaya"),
    ("desi_dr2_cov", f"{BAO}/desi_bao_dr2/desi_gaussian_bao_ALL_GCcomb_cov.txt", "desi/dr2_cov.txt",
     "DESI DR2 BAO covariance"),
    ("desi_dr1_mean", f"{BAO}/desi_2024_gaussian_bao_ALL_GCcomb_mean.txt", "desi/dr1_mean.txt",
     "DESI DR1 (2024) BAO mean (arXiv:2404.03002)"),
    ("desi_dr1_cov", f"{BAO}/desi_2024_gaussian_bao_ALL_GCcomb_cov.txt", "desi/dr1_cov.txt",
     "DESI DR1 BAO covariance"),
    ("pantheon_dat", f"{PANTHEON}/Pantheon%2BSH0ES.dat", "pantheon/PantheonPlusSH0ES.dat",
     "Pantheon+ SN Ia distances (Scolnic+2022, Brout+2022)"),
    ("pantheon_cov", f"{PANTHEON}/Pantheon%2BSH0ES_STAT%2BSYS.cov", "pantheon/PantheonPlusSH0ES_STAT+SYS.cov",
     "Pantheon+ statistical+systematic covariance"),
    # Papers whose tables are parsed from their LaTeX source
    ("arxiv_1808.05724", "https://arxiv.org/e-print/1808.05724", "arxiv/1808.05724.tar.gz",
     "Chen, Huang & Wang 2019: Planck 2018 distance priors (R, l_A, omega_b)"),
    ("arxiv_1703.10538", "https://arxiv.org/e-print/1703.10538", "arxiv/1703.10538.tar.gz",
     "Nesseris, Pantazis & Perivolaropoulos 2017: 'Gold-2017' f*sigma8 compilation"),
    ("arxiv_1808.06634", "https://arxiv.org/e-print/1808.06634", "arxiv/1808.06634.tar.gz",
     "Read, Walker & Steger 2019: dwarf central densities rho_DM(150 pc); input to Correa 2021 (MNRAS 503, 920)"),
    ("arxiv_1503.07675", "https://arxiv.org/e-print/1503.07675", "arxiv/1503.07675.tar.gz",
     "Harvey et al. 2015: 72 cluster collisions, DM-gas fractional lag beta"),
    ("arxiv_2006.12515", "https://arxiv.org/e-print/2006.12515", "arxiv/2006.12515.tar.gz",
     "Sagunski et al. 2021: SIDM cross-sections of groups and clusters"),
    ("arxiv_2305.16176", "https://arxiv.org/e-print/2305.16176", "arxiv/2305.16176.tar.gz",
     "Yang et al. 2023: parametric gravothermal SIDM halo model (coefficients used in physics/sidm.py)"),
    ("arxiv_2610.26877", "https://arxiv.org/e-print/2610.26877", "arxiv/2610.26877.tar.gz",
     "Oct 2026 paper: 'Revisiting self-interacting dark matter with DESI DR2 BAO' (reproduction target)"),
    ("arxiv_abstracts", "https://export.arxiv.org/api/query?id_list=0704.0261,1503.07675,2012.06611,"
     "2006.12515,1808.05603,2105.14030,1310.3278,2007.02958,2105.05259,1712.07962,1303.1521,1508.03339"
     "&max_results=20", "arxiv/abstracts.xml",
     "Abstracts used to verify single-number literature constraints quoted in data/literature.py"),
    ("arxiv_abstracts_desi", "https://export.arxiv.org/api/query?id_list=2503.14738&max_results=1", "arxiv/abstracts_desi.xml",
     "DESI DR2 cosmology abstract (quoted significance of dynamical dark energy)"),
]
for name, desc in [
    ("HSC", "Subaru HSC microlensing of M31 (Niikura+2019, updated Smyth+2020, Croon+2020)"),
    ("OGLE-2019", "OGLE 5-year microlensing (Niikura+2019)"),
    ("EROS", "EROS-2 microlensing (Tisserand+2007)"),
    ("M", "MACHO microlensing (Alcock+2001)"),
    ("UFdwarfs", "Eridanus II star cluster + ultra-faint dwarf heating (Brandt 2016)"),
    ("WideBinaries", "Halo wide-binary disruption (Monroy-Rodriguez & Allen 2014)"),
    ("CMB", "Planck CMB accretion bound incl. DM halo (Serpico+2020)"),
    ("EGRB", "Hawking evaporation: extragalactic gamma-ray background (Carr+2010)"),
    ("Voyager", "Hawking evaporation: Voyager-1 e+e- (Boudaud & Cirelli 2019)"),
    ("511keV", "Hawking evaporation: Galactic 511 keV line (Laha 2019)"),
    ("CMBevap", "Hawking evaporation: CMB energy injection (Poulin+2017)"),
    ("LIGO", "LIGO/Virgo merger rate bounds (for completeness of the window map)"),
]:
    SOURCES.append((f"pbh_{name}", f"{PBH}/{name}.txt", f"pbh/{name}.txt", desc))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch(url: str, dest: str, tries: int = 4) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "theory-tester/1.0 (research; read-only)"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dest)
            return
        except Exception as e:  # network hiccup: back off and retry
            last = e
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"download failed after {tries} tries: {url}: {last}")


def load_manifest() -> dict:
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}


def fetch_all(verbose: bool = True) -> dict:
    """Ensure every source is cached and checksummed. Returns a status dict for the run log."""
    manifest = load_manifest()
    status = {}
    for key, url, rel, desc in SOURCES:
        dest = os.path.join(CACHE, rel)
        note = "cached"
        if not os.path.exists(dest):
            _fetch(url, dest)
            note = "downloaded"
        digest = _sha256(dest)
        rec = manifest.get(key)
        if rec is None:
            manifest[key] = {"url": url, "file": rel, "sha256": digest, "bytes": os.path.getsize(dest),
                             "description": desc, "first_fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            note += ", checksum recorded"
        elif rec["sha256"] != digest:
            # cached copy differs from the recorded one: re-fetch once to tell corruption from upstream change
            _fetch(url, dest)
            digest2 = _sha256(dest)
            if digest2 == rec["sha256"]:
                note = "cache was corrupt; re-downloaded, checksum OK"
            else:
                note = f"WARNING upstream file changed (recorded {rec['sha256'][:12]}, now {digest2[:12]})"
        else:
            note += ", checksum OK"
        status[key] = note
        if verbose:
            print(f"  [data] {key:22s} {note}")
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    return status


def path(key: str) -> str:
    for k, _, rel, _ in SOURCES:
        if k == key:
            return os.path.join(CACHE, rel)
    raise KeyError(key)


def read_member(key: str, endswith: str) -> str:
    """Read one text member (by filename suffix) out of a cached zip / tar.gz / gzip archive."""
    p = path(key)
    with open(p, "rb") as f:
        blob = f.read()
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for n in z.namelist():
                if n.endswith(endswith):
                    return z.read(n).decode("utf-8", "replace")
    else:
        try:
            with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as t:
                for m in t.getmembers():
                    if m.name.endswith(endswith):
                        return t.extractfile(m).read().decode("utf-8", "replace")
        except tarfile.ReadError:
            return gzip.decompress(blob).decode("utf-8", "replace")
    raise FileNotFoundError(f"{endswith} not in {p}")


def zip_members(key: str) -> dict:
    with zipfile.ZipFile(path(key)) as z:
        return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if not n.endswith("/")}


if __name__ == "__main__":
    fetch_all()
    sys.exit(0)
