"""Parse every cached input into plain numpy structures.

Tables that exist only inside papers are parsed from the papers' own LaTeX (arXiv e-print), so
the numbers are traceable to the source file whose checksum is in data/MANIFEST.json.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from data import download as dl


# ----------------------------------------------------------------------------- SPARC
@dataclass
class Galaxy:
    name: str
    D: float            # Mpc
    eD: float
    inc: float          # deg
    einc: float
    quality: int
    Rdisk: float        # kpc, [3.6] exponential scale length
    L36: float          # 1e9 Lsun
    MHI: float          # 1e9 Msun
    Vflat: float
    r: np.ndarray       # kpc
    vobs: np.ndarray
    err: np.ndarray
    vgas: np.ndarray    # signed: negative means gas pulls outward (central hole); Vgas|Vgas| is used
    vdisk: np.ndarray   # for M/L = 1
    vbul: np.ndarray    # for M/L = 1
    has_bulge: bool = False


def load_sparc(min_points: int = 5) -> list[Galaxy]:
    meta = {}
    txt = open(dl.path("sparc_table")).read().splitlines()
    for line in txt:
        p = line.split()
        if len(p) < 18 or not re.fullmatch(r"\d+", p[1]) or not re.fullmatch(r"\d+", p[17]):
            continue
        meta[p[0]] = dict(D=float(p[2]), eD=float(p[3]), inc=float(p[5]), einc=float(p[6]), L36=float(p[7]), Rdisk=float(p[11]),
                          MHI=float(p[13]), Vflat=float(p[15]), Q=int(p[17]))
    gals = []
    for fname, body in sorted(dl.zip_members("sparc_rotmod").items()):
        name = fname.split("/")[-1].replace("_rotmod.dat", "")
        rows = [l.split() for l in body.splitlines() if l.strip() and not l.startswith("#")]
        a = np.array([[float(x) for x in r[:6]] for r in rows])
        if len(a) < min_points or name not in meta:
            continue
        m = meta[name]
        g = Galaxy(name=name, D=m["D"], eD=m["eD"], inc=m["inc"], einc=m["einc"], quality=m["Q"], Rdisk=m["Rdisk"], L36=m["L36"],
                   MHI=m["MHI"], Vflat=m["Vflat"], r=a[:, 0], vobs=a[:, 1], err=a[:, 2], vgas=a[:, 3],
                   vdisk=a[:, 4], vbul=a[:, 5], has_bulge=bool(np.any(a[:, 5] > 0)))
        gals.append(g)
    return gals


# ----------------------------------------------------------------------------- DESI BAO
@dataclass
class BAOData:
    label: str
    z: np.ndarray
    value: np.ndarray
    kind: list
    cov: np.ndarray
    icov: np.ndarray = field(init=False)

    def __post_init__(self):
        self.icov = np.linalg.inv(self.cov)


def load_desi(release: str = "dr2") -> BAOData:
    rows = [l.split() for l in open(dl.path(f"desi_{release}_mean")) if l.strip() and not l.startswith("#")]
    cov = np.loadtxt(dl.path(f"desi_{release}_cov"))
    return BAOData(label=f"DESI {release.upper()} BAO", z=np.array([float(r[0]) for r in rows]),
                   value=np.array([float(r[1]) for r in rows]), kind=[r[2] for r in rows], cov=cov)


# ----------------------------------------------------------------------------- Pantheon+
@dataclass
class SNData:
    z: np.ndarray       # zHD (CMB frame, peculiar-velocity corrected)
    zhel: np.ndarray
    mb: np.ndarray      # m_b_corr
    icov: np.ndarray
    n: int


def load_pantheon(zmin: float = 0.01) -> SNData:
    p = dl.path("pantheon_dat")
    head = open(p).readline().split()
    raw = np.genfromtxt(p, names=head, dtype=None, encoding=None, skip_header=1)
    z = np.asarray(raw["zHD"], float)
    keep = z > zmin  # standard uncalibrated SN likelihood (as in DESI DR2 analysis): drop z<0.01
    with open(dl.path("pantheon_cov")) as f:
        n = int(f.readline())
        c = np.fromstring(f.read(), sep=" ").reshape(n, n)
    c = c[np.ix_(keep, keep)]
    return SNData(z=z[keep], zhel=np.asarray(raw["zHEL"], float)[keep],
                  mb=np.asarray(raw["m_b_corr"], float)[keep], icov=np.linalg.inv(c), n=int(keep.sum()))


# ----------------------------------------------------------------------------- Planck priors
def _num(s: str) -> float:
    return float(re.sub(r"[{}$\s]", "", s))


@dataclass
class CMBPriors:
    mean: np.ndarray     # R, l_A, omega_b
    cov: np.ndarray
    icov: np.ndarray
    source: str


def load_planck_priors() -> CMBPriors:
    """Chen, Huang & Wang 2019 Table 1, base-LCDM block, Planck 2018 TT,TE,EE+lowE.

    Parsed from the paper's LaTeX. n_s is marginalised by dropping its row/column; asymmetric
    errors are symmetrised (mean of upper and lower)."""
    tex = dl.read_member("arxiv_1808.05724", ".tex")
    block = tex[tex.index("$\\Lambda$CDM & $Planck"):]
    block = block[:block.index("\\hline\\hline", 20)]
    vals, sig, corr = [], [], []
    for lab in ["$R$", "$l_\\textrm{A}$", "$\\Omega_b h^2$"]:
        line = [l for l in block.splitlines() if l.strip().startswith(lab)][0]
        cells = [c.strip() for c in line.split("&")]
        m = re.match(r"\$([\d.]+)(?:\\pm([\d.]+)|\^\{\+([\d.]+)\}_\{-([\d.]+)\})\$", cells[1])
        vals.append(float(m.group(1)))
        sig.append(float(m.group(2)) if m.group(2) else 0.5 * (float(m.group(3)) + float(m.group(4))))
        corr.append([_num(c.replace("\\\\", "")) for c in cells[2:5]])
    sig = np.array(sig)
    cov = np.array(corr) * np.outer(sig, sig)
    return CMBPriors(mean=np.array(vals), cov=cov, icov=np.linalg.inv(cov),
                     source="arXiv:1808.05724 Table 1 (LCDM, TT,TE,EE+lowE)")


# ----------------------------------------------------------------------------- f sigma8
@dataclass
class GrowthData:
    z: np.ndarray
    fs8: np.ndarray
    cov: np.ndarray
    icov: np.ndarray
    om_fid: np.ndarray
    names: list


def load_fsigma8() -> GrowthData:
    """Gold-2017 (Nesseris+2017, Table II) with the WiggleZ 3x3 covariance from their eq. (2.5)."""
    tex = dl.read_member("arxiv_1703.10538", ".tex")
    t = tex[tex.index("label{tab:fs8-data-gold}"):]
    t = t[:t.index("\\end{tabular}")]
    z, v, e, om, names = [], [], [], [], []
    last_om = None
    for line in t.splitlines():
        cells = [c.strip() for c in line.split("&")]
        if len(cells) < 6 or not cells[0].isdigit():
            continue
        zz = _num(cells[2])
        m = re.search(r"([\d.]+)\s*\\pm\s*([\d.]+)", cells[3])
        note = cells[6] if len(cells) > 6 else ""
        mo = re.search(r"\\Omega_m[^=]*\)=\(([\d.]+)", note)
        if mo:
            last_om = float(mo.group(1))
        z.append(zz); v.append(float(m.group(1))); e.append(float(m.group(2)))
        om.append(last_om); names.append(cells[1])
    z, v, e = map(np.array, (z, v, e))
    cov = np.diag(e ** 2)
    wz = [i for i, n in enumerate(names) if "WiggleZ" in n]
    mwz = re.search(r"C_\{ij\}\^\{\\text\{WiggleZ\}\}=10\^\{-3\}\\left\((.*?)\\right\)", tex, re.S)
    body = re.sub(r"\\(begin|end)\{array\}(\{c+\})?", "", mwz.group(1))
    rows = [r for r in body.split("\\\\") if "&" in r]
    wcov = 1e-3 * np.array([[_num(x) for x in r.split("&")] for r in rows])
    cov[np.ix_(wz, wz)] = wcov
    return GrowthData(z=z, fs8=v, cov=cov, icov=np.linalg.inv(cov), om_fid=np.array(om, float), names=names)


# ----------------------------------------------------------------------------- dwarfs
@dataclass
class Dwarf:
    name: str
    kind: str          # dSph or dIrr
    Mstar: float       # Msun
    Mgas: float        # Msun
    Rhalf: float       # kpc (stellar half-light)
    Rgas: float        # kpc (gas exponential scale length; nan for dSph)
    M200: float        # Msun, pre-infall (abundance matching / HI rotation curves)
    eM200: float
    rho150: float      # Msun/kpc^3
    erho_lo: float
    erho_hi: float
    t_trunc: float     # Gyr


def load_dwarfs() -> list[Dwarf]:
    """Read, Walker & Steger 2019 Table 1: the rho_DM(150 pc) compilation that Correa 2021
    (MNRAS 503, 920) fits with velocity-dependent SIDM."""
    tex = dl.read_member("arxiv_1808.06634", ".tex")
    out = []
    for line in tex.splitlines():
        cells = [c.strip() for c in line.split("&")]
        if len(cells) < 13 or cells[1] not in ("dSph", "dIrr"):
            continue
        def first(s):
            return float(re.search(r"[\d,]*\.?\d+", s.replace(",", "")).group(0))
        mstar = first(cells[3]) * 1e6
        mgas = first(cells[4]) * 1e6 if cells[4] != "--" else 0.0
        rhalf = first(cells[5])
        rgas = first(cells[6]) if cells[6] != "--" else np.nan
        mm = re.search(r"\$([\d.]+)\s*(?:\\pm\s*([\d.]+)|_\{-([\d.]+)\}\^\{\+([\d.]+)\})", cells[7])
        m200 = float(mm.group(1)) * 1e9
        em = float(mm.group(2)) if mm.group(2) else 0.5 * (float(mm.group(3)) + float(mm.group(4)))
        mr = re.search(r"\$([\d.]+)_\{-([\d.]+)\}\^\{\+([\d.]+)\}", cells[10])
        out.append(Dwarf(name=cells[0], kind=cells[1], Mstar=mstar, Mgas=mgas, Rhalf=rhalf, Rgas=rgas,
                         M200=m200, eM200=em * 1e9, rho150=float(mr.group(1)) * 1e8,
                         erho_lo=float(mr.group(2)) * 1e8, erho_hi=float(mr.group(3)) * 1e8,
                         t_trunc=first(cells[9])))
    return out


# ----------------------------------------------------------------------------- PBH bounds
def load_pbh_bound(name: str) -> tuple[np.ndarray, np.ndarray]:
    """(M [Msun], f_max) from Kavanagh's PBHbounds digitisations."""
    a = np.loadtxt(dl.path(f"pbh_{name}"), comments="#")
    a = a[np.argsort(a[:, 0])]
    return a[:, 0], a[:, 1]
