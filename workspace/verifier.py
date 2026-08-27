import json
import numpy as np

# NumPy 2.0 removed np.trapz (renamed np.trapezoid). Bind the available name so
# the oracle runs identically on NumPy 1.x and 2.x. (reviewer fix, 2026-08-26)
_TRAPZ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz

# ============================================================================
# voc-minimal-subset -- SEALED VERIFIER (the sole oracle)
#
# A candidate is a measurement PROTOCOL:
#   {'modalities': <subset of ['srpl','trpl','transmission'], size 1-2>,
#    'configs': {<modality>: [<cfg>, ...]}}
#
# verify(candidate) -> {'valid': bool, 'reason': str, 'details': {...}}
# valid iff G1 (<=10 mV worst-case LODO recovery of the FULL protocol's OWN
# implied V_OC) AND G2 (<=2 modalities, on-menu) AND G3 (budget strictly
# Pareto-dominates the full protocol). G4 (determinism) holds by construction.
#
# SCOPE: information sufficiency vs the pinned forward model's OWN implied
# V_OC. NOT adequacy vs measured JV V_OC (the ~170 mV real-device stack
# offset from arXiv:2508.21037 is OUT of scope).
# ============================================================================

KT = 0.025852  # eV at 300 K (kT/q in volts)
GRID_SEED = 20250827
N_DEV = 24
CERT_SEEDS = tuple(range(1000, 1020))  # certification seeds; disjoint from screening (0..999)
TOL_MV = 10.0

MODALITIES = ('srpl', 'trpl', 'transmission')
FLUENCE_MENU = (0.1, 0.25, 1.0)              # suns-equivalent (laser)
SRPL_WINDOW_MENU_MS = (10.0, 50.0, 100.0)
TRPL_WINDOW_MENU_NS = (50.0, 100.0, 500.0)  # NOTE: inert in this model — TRPL time/dose
# and noise depend only on fluence (below), so window_ns is a validated but non-acting knob.
TRANS_WINDOW_MENU_MS = (5.0, 20.0)
TRANS_PROBE_FLUX = 0.05                       # broadband lamp, fixed, no laser fluence
TRPL_TIME_MS = 100.0                          # pulse-averaging-limited acquisition time unit
TRPL_DOSE_UNIT = 100.0

# Pinned FULL three-measurement protocol (the reduction reference).
FULL_PROTOCOL = {
    'modalities': ['srpl', 'trpl', 'transmission'],
    'configs': {
        'srpl': [{'fluence': 1.0, 'window_ms': 100.0}],
        'trpl': [{'fluence': 1.0, 'window_ns': 100.0}],
        'transmission': [{'window_ms': 20.0}],
    },
}

# Nominal single-config doses (SNR reference for the noise model).
SRPL_NOM_DOSE = 1.0 * 100.0
TRANS_NOM_DOSE = TRANS_PROBE_FLUX * 20.0
TRPL_NOM_DOSE = 1.0 * TRPL_DOSE_UNIT

# Base 1-sigma measurement uncertainties at nominal dose (shot-noise-limited:
# sigma scales as sqrt(nominal_dose / actual_dose)).
BASE_SIG_EG = 0.002       # transmission -> bandgap edge (eV)
BASE_SIG_EU_SRPL = 0.0010 # SRPL PL tail -> Urbach energy (eV)
BASE_SIG_EU_TRANS = 0.0015# transmission edge -> Urbach energy (eV)
BASE_SIG_D = 8.0          # transmission -> thickness (nm)
BASE_SIG_LNP_SRPL = 0.03  # SRPL -> PLQE DIRECT (log-space); precise
BASE_SIG_LNP_TRPL = 0.20  # TRPL -> PLQE INDIRECT via kinetic reconstruction;
                          # unbiased but ~7x less precise (assumes injection
                          # level / radiative coefficient)

# Deterministic noise-quantity keys.
K_EG, K_EU_T, K_D, K_LNP_S, K_EU_S, K_LNP_T = 1, 2, 3, 4, 5, 6

# Fixed absolute energy grid for the detailed-balance integrals.
E_GRID = np.linspace(1.35, 2.35, 2001)
_PHI_BB = E_GRID ** 2 / (np.exp(E_GRID / KT) - 1.0)   # Boltzmann emission tail (arb prefactor)
_PHI_SUN = E_GRID ** 2 / (np.exp(E_GRID / 0.5) - 1.0) # fixed solar generation spectrum


def _vrad(Eg, EU, d_nm):
    # Detailed-balance radiative V_OC from an Urbach-broadened absorptance edge.
    d_cm = d_nm * 1e-7
    alpha0 = 1.0e5  # cm^-1 above-gap absorption coefficient
    # np.where evaluates BOTH branches; clip the sub-gap exponent so the (discarded)
    # above-gap entries don't overflow to inf and throw a RuntimeWarning. The used
    # branch has (E_GRID-Eg)<=0, so the clip is a no-op on every selected value.
    alpha = np.where(E_GRID >= Eg, alpha0, alpha0 * np.exp(np.clip((E_GRID - Eg) / EU, -700.0, 0.0)))
    a = 1.0 - np.exp(-alpha * d_cm)  # absorptance (thickness-dependent)
    J0 = _TRAPZ(a * _PHI_BB, E_GRID)   # radiative saturation current (reciprocity)
    Jsc = _TRAPZ(a * _PHI_SUN, E_GRID) # absorbed generation
    return KT * np.log(Jsc / J0)


def _build_grid():
    # Synthetic p-i-n grid spanning the published batch's realistic spread
    # (arXiv:2508.21037: perovskite ~1.6 eV, Urbach ~15 meV, PLQE 0.2-5%).
    r = np.random.RandomState(GRID_SEED)
    devs = []
    for i in range(N_DEV):
        Eg = 1.55 + 0.08 * r.rand()                                    # 1.55-1.63 eV
        EU = 0.013 + 0.005 * r.rand()                                  # 13-18 meV
        lnP = np.log(0.002) + (np.log(0.05) - np.log(0.002)) * r.rand()# PLQE 0.2-5%
        tau = 50.0 + 750.0 * r.rand()                                  # non-rad lifetime (ns)
        d = 400.0 + 300.0 * r.rand()                                   # thickness (nm)
        devs.append({'Eg': Eg, 'EU': EU, 'lnP': lnP, 'tau': tau, 'd': d})
    return devs


DEVICES = _build_grid()
_EG = np.array([d['Eg'] for d in DEVICES])
_EU = np.array([d['EU'] for d in DEVICES])
_LNP = np.array([d['lnP'] for d in DEVICES])
_D = np.array([d['d'] for d in DEVICES])


def _lodo(arr):
    # Leave-one-device-out population mean: the honest nominal prior a reduced
    # protocol uses for a quantity whose measuring modality it dropped, WITHOUT
    # peeking at the held-out device.
    n = len(arr)
    tot = arr.sum()
    return np.array([(tot - arr[i]) / (n - 1) for i in range(n)])


PRIOR_EG = _lodo(_EG)
PRIOR_EU = _lodo(_EU)
PRIOR_LNP = _lodo(_LNP)
PRIOR_D = _lodo(_D)


def _z(seed, dev, key):
    # Deterministic standard-normal draw keyed by (seed, device, quantity).
    # Independent of the protocol, so a modality retained by both the reduced
    # and full protocols carries the SAME noise draw -> their difference is
    # exactly the dropped modality's information contribution.
    s = (int(seed) * 1000003 + int(dev) * 1009 + int(key)) % 2147483647
    return np.random.RandomState(s).standard_normal()


def _sig(base, nom_dose, dose):
    return base * np.sqrt(nom_dose / max(dose, 1e-9))


def _fuse(pairs):
    # Precision-weighted (inverse-variance) fusion of (value, sigma) estimates.
    # Floor sigma so the fusion stays finite at (near-)infinite dose / zero noise
    # (e.g. the dress rehearsal): there the fused values are identical, so equal
    # floored weights return that exact value instead of inf/inf -> nan. Real
    # finite-dose grading never hits the floor. (reviewer fix, 2026-08-26)
    floored = [(v, s if s > 1e-12 else 1e-12) for v, s in pairs]
    w = [1.0 / (s * s) for _, s in floored]
    sw = sum(w)
    return sum(wi * v for wi, (v, _) in zip(w, floored)) / sw


def _mod_dose(mod, cfgs):
    tot = 0.0
    for c in cfgs:
        if mod == 'srpl':
            tot += c['fluence'] * c['window_ms']
        elif mod == 'transmission':
            tot += TRANS_PROBE_FLUX * c['window_ms']
        elif mod == 'trpl':
            tot += c['fluence'] * TRPL_DOSE_UNIT
    return tot


def _budget(protocol):
    # Returns (total_time_ms, total_photon_dose).
    t = 0.0
    d = 0.0
    for mod in protocol['modalities']:
        for c in protocol['configs'][mod]:
            if mod == 'srpl':
                t += c['window_ms']
                d += c['fluence'] * c['window_ms']
            elif mod == 'transmission':
                t += c['window_ms']
                d += TRANS_PROBE_FLUX * c['window_ms']
            elif mod == 'trpl':
                t += TRPL_TIME_MS / c['fluence']  # lower fluence -> more averaging -> more time
                d += c['fluence'] * TRPL_DOSE_UNIT
    return t, d


def _implied_voc(mods, doses, dev_i, seed):
    # Compute implied V_OC from ONLY the retained modalities' simulated data +
    # protocol-independent LODO priors for any dropped quantity.
    if 'transmission' in mods:
        sg = _sig(BASE_SIG_EG, TRANS_NOM_DOSE, doses['transmission'])
        Eg = _EG[dev_i] + _z(seed, dev_i, K_EG) * sg
        sd = _sig(BASE_SIG_D, TRANS_NOM_DOSE, doses['transmission'])
        d = _D[dev_i] + _z(seed, dev_i, K_D) * sd
    else:
        Eg = PRIOR_EG[dev_i]   # dropped transmission -> nominal bandgap prior
        d = PRIOR_D[dev_i]
    eu_pairs = []
    if 'srpl' in mods:
        s = _sig(BASE_SIG_EU_SRPL, SRPL_NOM_DOSE, doses['srpl'])
        eu_pairs.append((_EU[dev_i] + _z(seed, dev_i, K_EU_S) * s, s))
    if 'transmission' in mods:
        s = _sig(BASE_SIG_EU_TRANS, TRANS_NOM_DOSE, doses['transmission'])
        eu_pairs.append((_EU[dev_i] + _z(seed, dev_i, K_EU_T) * s, s))
    EU = _fuse(eu_pairs) if eu_pairs else PRIOR_EU[dev_i]
    p_pairs = []
    if 'srpl' in mods:
        s = _sig(BASE_SIG_LNP_SRPL, SRPL_NOM_DOSE, doses['srpl'])
        p_pairs.append((_LNP[dev_i] + _z(seed, dev_i, K_LNP_S) * s, s))  # DIRECT PLQE
    if 'trpl' in mods:
        s = _sig(BASE_SIG_LNP_TRPL, TRPL_NOM_DOSE, doses['trpl'])
        p_pairs.append((_LNP[dev_i] + _z(seed, dev_i, K_LNP_T) * s, s))  # INDIRECT PLQE
    lnP = _fuse(p_pairs) if p_pairs else PRIOR_LNP[dev_i]
    return _vrad(Eg, max(EU, 1e-3), d) - KT * abs(lnP)


def _full_voc(dev_i, seed):
    # Ground truth for G1: the FULL protocol's OWN implied V_OC on this
    # device+seed (all three modalities at nominal configs).
    doses = {'srpl': SRPL_NOM_DOSE, 'trpl': TRPL_NOM_DOSE, 'transmission': TRANS_NOM_DOSE}
    return _implied_voc(('srpl', 'trpl', 'transmission'), doses, dev_i, seed)


def dress_rehearsal():
    # ANTI-HALLUCINATION GATE: at infinite dose (zero noise) the full pipeline
    # must reproduce the true implied V_OC exactly. Returns the worst residual
    # (volts). If it is not ~0 the referee is unfaithful and must not grade.
    inf = float('inf')
    doses = {'srpl': inf, 'trpl': inf, 'transmission': inf}
    worst = 0.0
    for i in range(N_DEV):
        v0 = _implied_voc(('srpl', 'trpl', 'transmission'), doses, i, CERT_SEEDS[0])
        vt = _vrad(_EG[i], _EU[i], _D[i]) - KT * abs(_LNP[i])
        worst = max(worst, abs(v0 - vt))
    return worst


_REFEREE_OK = dress_rehearsal() < 1e-6


def pre_search_checks():
    # SETUP-TIME GATES (printed, not per-candidate):
    #  * full-protocol leave-one-device-out seed scatter (ILL-POSED-BAR kill if >10 mV)
    #  * per-modality LEVERAGE = mV that dropping the modality (replacing its
    #    native quantity with the LODO prior / other route) moves the full
    #    answer. Leverage<=10 mV => non-load-bearing-by-construction (TRPL is
    #    expected here: redundant with SRPL for the V_OC scalar), never a
    #    discovered shortcut. A load-bearing modality below 10 mV => grid too
    #    narrow, widen it.
    scat = 0.0
    for i in range(N_DEV):
        vs = [_full_voc(i, s) for s in CERT_SEEDS]
        scat = max(scat, float(np.std(vs)) * 1000.0)
    lev = {}
    for drop in MODALITIES:
        keep = tuple(m for m in MODALITIES if m != drop)
        doses = {m: (SRPL_NOM_DOSE if m == 'srpl' else TRANS_NOM_DOSE if m == 'transmission' else TRPL_NOM_DOSE) for m in keep}
        w = 0.0
        for i in range(N_DEV):
            for s in CERT_SEEDS:
                w = max(w, abs(_full_voc(i, s) - _implied_voc(keep, doses, i, s)) * 1000.0)
        lev[drop] = w
    return {'full_scatter_mv': scat, 'ill_posed': scat > TOL_MV,
            'leverage_mv': lev, 'load_bearing': {k: (v > TOL_MV) for k, v in lev.items()}}


def _validate(c):
    if not isinstance(c, dict):
        return False, 'candidate not a dict'
    if 'modalities' not in c or 'configs' not in c:
        return False, 'missing modalities or configs'
    mods = c['modalities']
    if not isinstance(mods, list) or len(mods) == 0:
        return False, 'modalities empty'
    if len(set(mods)) != len(mods):
        return False, 'duplicate modalities'
    for m in mods:
        if m not in MODALITIES:
            return False, 'unknown modality ' + str(m)
        if m not in c['configs'] or not c['configs'][m]:
            return False, 'no configs for ' + str(m)
        for cfg in c['configs'][m]:
            if m == 'srpl':
                if cfg.get('fluence') not in FLUENCE_MENU:
                    return False, 'srpl fluence off-menu'
                if cfg.get('window_ms') not in SRPL_WINDOW_MENU_MS:
                    return False, 'srpl window off-menu'
            elif m == 'trpl':
                if cfg.get('fluence') not in FLUENCE_MENU:
                    return False, 'trpl fluence off-menu'
                if cfg.get('window_ns') not in TRPL_WINDOW_MENU_NS:
                    return False, 'trpl window off-menu'
            elif m == 'transmission':
                if cfg.get('window_ms') not in TRANS_WINDOW_MENU_MS:
                    return False, 'transmission window off-menu'
    return True, 'ok'


def verify(candidate):
    # Infra / referee failure RAISES (INCONCLUSIVE) -- it never silently scores.
    if not _REFEREE_OK:
        raise RuntimeError('INCONCLUSIVE: dress rehearsal failed; referee unfaithful')
    if isinstance(candidate, str):
        # The candidate arrives as text. The searcher / engine may hand us either
        # JSON (double-quoted) OR a Python-repr dict (single-quoted str(dict)), so
        # try JSON first, then ast.literal_eval (safe -- literals only). A string
        # that is neither is a malformed candidate -> REFUSE, never crash. (An
        # oracle that raises on bad input cannot be trusted, and the engine's
        # re-verification hands the stored candidate string straight back here --
        # if we can't parse it we falsely reject every real hit.) reviewer fix.
        try:
            candidate = json.loads(candidate)
        except (ValueError, TypeError):
            import ast
            try:
                candidate = ast.literal_eval(candidate)
            except (ValueError, SyntaxError, TypeError):
                return {'valid': False, 'reason': 'malformed candidate: not JSON or literal'}
    ok, msg = _validate(candidate)
    if not ok:
        return {'valid': False, 'reason': 'malformed candidate: ' + msg}
    mods = tuple(candidate['modalities'])
    # G2
    if len(mods) < 1 or len(mods) > 2:
        return {'valid': False, 'reason': 'G2 fail: ' + str(len(mods)) + ' modalities (must be 1-2)'}
    # G3 -- budget must strictly Pareto-dominate the full protocol.
    bt, bd = _budget(candidate)
    ft, fd = _budget(FULL_PROTOCOL)
    eps = 1e-9
    le = (bt <= ft + eps) and (bd <= fd + eps)
    strict = (bt < ft - eps) or (bd < fd - eps)
    if not (le and strict):
        return {'valid': False,
                'reason': 'G3 fail: budget (time=%.3f dose=%.3f) does not strictly Pareto-dominate full (time=%.3f dose=%.3f)' % (bt, bd, ft, fd),
                'details': {'budget_time': bt, 'budget_dose': bd, 'full_time': ft, 'full_dose': fd}}
    # G1 -- worst-case LODO recovery of the full protocol's own implied V_OC.
    doses = {m: _mod_dose(m, candidate['configs'][m]) for m in mods}
    worst = 0.0
    arg = None
    for i in range(N_DEV):
        for s in CERT_SEEDS:
            e = abs(_implied_voc(mods, doses, i, s) - _full_voc(i, s)) * 1000.0
            if e > worst:
                worst = e
                arg = (i, s)
    if worst > TOL_MV:
        return {'valid': False,
                'reason': 'G1 fail: worst-case |V_reduced-V_full|=%.2f mV > %.1f mV (LODO %d devices x %d seeds)' % (worst, TOL_MV, N_DEV, len(CERT_SEEDS)),
                'details': {'worst_mv': worst, 'argmax_dev_seed': arg, 'budget_time': bt, 'budget_dose': bd}}
    # G4 (determinism) is guaranteed by construction; the engine double-runs to confirm byte-identity.
    return {'valid': True,
            'reason': 'PASS: subset=%s worst-case %.2f mV <= %.1f mV; budget time %.2f<%.2f dose %.3f<%.3f' % (list(mods), worst, TOL_MV, bt, ft, bd, fd),
            'details': {'worst_mv': worst, 'budget_time': bt, 'budget_dose': bd, 'full_time': ft, 'full_dose': fd}}


if __name__ == '__main__':
    print('referee_ok', _REFEREE_OK, 'dress_floor_V', dress_rehearsal())
    print('pre_search', pre_search_checks())
    cands = {
        'win_srpl_trans_nominal': {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 100.0}], 'transmission': [{'window_ms': 20.0}]}},
        'drop_transmission': {'modalities': ['srpl', 'trpl'], 'configs': {'srpl': [{'fluence': 0.25, 'window_ms': 50.0}], 'trpl': [{'fluence': 1.0, 'window_ns': 100.0}]}},
        'drop_srpl': {'modalities': ['transmission', 'trpl'], 'configs': {'transmission': [{'window_ms': 20.0}], 'trpl': [{'fluence': 1.0, 'window_ns': 100.0}]}},
        'only_transmission': {'modalities': ['transmission'], 'configs': {'transmission': [{'window_ms': 5.0}]}},
        'budget_bloat': {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 100.0}, {'fluence': 1.0, 'window_ms': 100.0}, {'fluence': 1.0, 'window_ms': 100.0}], 'transmission': [{'window_ms': 20.0}]}},
    }
    for name, cand in cands.items():
        r = verify(cand)
        print(name, r['valid'], '|', r['reason'])
