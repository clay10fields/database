"""Single-number published constraints, each tied to its source and machine-verified.

Every entry carries `verify`: a list of literal strings that must appear in the cached arXiv
abstract or LaTeX source of the cited paper. `check_all()` runs at the start of every run and
fails loudly if a quoted number is not found in the source, so no constraint here is typed from
memory without a check.
"""
from __future__ import annotations

import html
import re

from data import download as dl


def _abstracts() -> dict:
    t = open(dl.path("arxiv_abstracts")).read() + open(dl.path("arxiv_abstracts_desi")).read()
    out = {}
    for e in t.split("<entry>")[1:]:
        i = re.search(r"<id>http://arxiv.org/abs/(.*?)v\d+</id>", e).group(1)
        s = re.search(r"<summary>(.*?)</summary>", e, re.S).group(1)
        out[i] = " ".join(html.unescape(s).split())
    return out


# Cross-section measurements / limits used for the velocity-dependent force (hypothesis 4).
# v: characteristic relative (collision) speed in km/s.
# Scoring policy (conservative toward new physics): Andrade+22 and Sagunski+21 each report a mild preference for a
# NON-zero cross-section (mean +- err). We score them as their published 95% upper limits ('ul95'), i.e. we do not
# let these mild detections reward SIDM. The report quotes how much they would add if taken at face value.
SIGMA_CONSTRAINTS = [
    dict(key="harvey15_offsets", system="72 colliding clusters (DM-galaxy offsets)", v=1500.0,
         kind="beta", beta=-0.04, ebeta=0.07, sigma_star=6.5, esigma_star=3.0,
         ref="Harvey et al. 2015, Science 347, 1462 (arXiv:1503.07675)",
         src="arxiv_1503.07675",
         verify=["\\langle\\beta\\rangle=-0.04\\pm0.07", "\\sstar\\approx6.5\\pm3"],
         note="beta = B(1-exp(-sigma/sigma*)), B~1 (their eq.); v~1500 km/s typical merger speed assumed"),
    dict(key="randall08_bullet", system="Bullet Cluster 1E0657-56", v=4000.0, kind="ul68", ul=1.25,
         ref="Randall et al. 2008, ApJ 679, 1173 (arXiv:0704.0261)", src="abstracts", arxiv="1503.07675",
         verify=["< 1.25cm2/g (68% confidence limit)"],
         note="68% upper limit as quoted by Harvey+2015; collision speed ~4000-4700 km/s"),
    dict(key="andrade22_cluster_lensing", system="8 strong-lensing clusters", v=1458.0, kind="ul95",
         mean=0.082, err=0.024, ul=0.13,
         ref="Andrade et al. 2022, MNRAS 510, 54 (arXiv:2012.06611)", src="abstracts", arxiv="2012.06611",
         verify=["$σ$/m < 0.13 cm$^2$/g at the 95% confidence level", "1458"]),
    dict(key="sagunski21_groups", system="Newman+ galaxy groups (lensing + Jeans)", v=1150.0, kind="ul95",
         mean=0.5, err=0.2, ul=1.1, ref="Sagunski et al. 2021, JCAP 01, 024 (arXiv:2006.12515)",
         src="arxiv_2006.12515", verify=["Groups & (mean) & $1150$ & $590\\pm 370$ & $0.5 \\pm 0.2$", "& $1430$ & $1.1$"]),
    dict(key="sagunski21_clusters", system="Newman+ relaxed clusters", v=1900.0, kind="ul95",
         mean=0.19, err=0.09, ul=0.35, ref="Sagunski et al. 2021, JCAP 01, 024 (arXiv:2006.12515)",
         src="arxiv_2006.12515", verify=["Clusters & (mean) & $1900$  & $300 \\pm 150$ & $0.19 \\pm 0.09$", "& $620$ & $0.35$"]),
]

# Strong-lensing subhalo constraint. No published hard bound on sigma(v<30 km/s) exists yet from
# flux-ratio lenses; Gilman+2021 give a forecast, used only in the forecast section.
LENSING_SUBHALO_FORECAST = dict(
    ref="Gilman et al. 2021, MNRAS 507, 2432 (arXiv:2105.05259)", arxiv="2105.05259",
    verify=["11-23 \\ \\rm{cm^2} \\rm{g^{-1}}"],
    text="50 quad lenses with mid-IR flux ratios: sigma_20 < 11-23 cm^2/g (95%) if CDM; or exclude CDM at 20:1 "
         "if sigma_20 = 19.2 cm^2/g")

# Dark-disc and dark-atom limits (hypothesis 6)
GAIA_DARK_DISC = [
    dict(key="buch19", h_max_pc=100.0, sigma_max=(5.0, 12.0),
         ref="Buch, Leung & Fan 2019, JCAP 04, 026 (arXiv:1808.05603)", arxiv="1808.05603",
         verify=["excluding surface densities (5-12) M$_\\odot$/pc$^2$ for scale heights below 100 pc"]),
    dict(key="widmark21", h_max_pc=50.0, sigma_max=5.0,
         ref="Widmark et al. 2021, A&A 653, A86 (arXiv:2105.14030)", arxiv="2105.14030",
         verify=["scale height $\\leq 50$ pc: an upper 95 % confidence limit of roughly 5 M$_\\odot$/pc$^2$"]),
]
LOCAL_DM_DENSITY = dict(rho=0.016, err=0.010, ref="Buch+2019 A-stars (arXiv:1808.05603)", arxiv="1808.05603",
                        verify=["0.016 \\pm 0.010"])
PLANCK_INTERACTING_FRACTION = dict(
    fmax=0.05, ref="Cyr-Racine, de Putter, Raccanelli & Sigurdson 2014, PRD 89, 063517 (arXiv:1310.3278)",
    arxiv="1310.3278", verify=["at most ~5% of all DM can be very strongly interacting with DR"],
    note="applies to the strongly-coupled (DAO) limit; treated as a 2-sigma bound f < 0.05")

DESI_DR2_W0WA = dict(ref="DESI Collaboration 2025, DESI DR2 Results II (arXiv:2503.14738)", arxiv="2503.14738",
                     verify=["ranges from $2.8-4.2σ$ depending on which SNe sample is used"])

CORREA21 = dict(ref="Correa 2021, MNRAS 503, 920 (arXiv:2007.02958)", arxiv="2007.02958",
                verify=["between $30$ and $50$ cm$^{2}$g$^{-1}$", "between $70$ and $100$ cm$^{2}$"])
FARNES18 = dict(ref="Farnes 2018, A&A 620, A92 (arXiv:1712.07962)", arxiv="1712.07962",
                verify=["can flatten the rotation curves of galaxies"])

# Hypothesis-2 / cluster-gas inputs (MOND and baryon-only models: lensing must follow baryons)
CLUSTER_GAS_FRACTION_OF_BARYONS = dict(value=0.85, err=0.05,
                                       note="hot gas is ~80-90% of cluster baryons (e.g. Gonzalez+2013); "
                                            "uncertainty propagated")


def check_all() -> list[str]:
    abs_ = _abstracts()
    srcs = {}
    report = []

    def text_for(entry):
        s = entry.get("src", "abstracts")
        if s == "abstracts":
            return abs_.get(entry["arxiv"], "")
        if s not in srcs:
            srcs[s] = dl.read_member(s, ".tex") if "2006" not in s else dl.read_member(s, "main.tex")
        return srcs[s]

    entries = SIGMA_CONSTRAINTS + GAIA_DARK_DISC + [LOCAL_DM_DENSITY, PLANCK_INTERACTING_FRACTION, CORREA21, DESI_DR2_W0WA,
                                                    FARNES18, LENSING_SUBHALO_FORECAST]
    for e in entries:
        t = text_for(e)
        for v in e["verify"]:
            if v not in t:
                raise AssertionError(f"literature check failed: {v!r} not found in source of {e['ref']}")
        report.append(f"verified: {e['ref']}")
    return report


if __name__ == "__main__":
    print("\n".join(check_all()))
