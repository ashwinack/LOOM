# LOOM string instrument: touch -> pluck detection -> voices, plus per-string energy for the visuals
import math

SCALES = {
    'pentatonic': [0,2,4,7,9],
    'major':      [0,2,4,5,7,9,11],
    'minor':      [0,2,3,5,7,8,10],
    'dorian':     [0,2,3,5,7,9,10],
    'chromatic':  list(range(12)),
    'minpent':    [0,3,5,7,10],
}
PALETTES = {   # low strings, high strings, touch/hit color
    'loom':   ((0.20,0.40,1.00), (0.75,0.88,1.00), (1.00,0.45,0.20)),
    'ice':    ((0.45,0.75,1.00), (0.90,0.97,1.00), (0.60,0.95,1.00)),
    'aurora': ((0.10,1.00,0.60), (0.60,0.30,1.00), (1.00,0.90,0.60)),
    'ember':  ((1.00,0.22,0.08), (1.00,0.75,0.30), (1.00,1.00,0.85)),
    'mono':   ((0.75,0.75,0.75), (1.00,1.00,1.00), (1.00,1.00,1.00)),
}
NVOICES = 12

def P():
    return op('/project1')

def _scale_notes(root, iv, hi):
    out = []; o = 0
    while True:
        for d in iv:
            m = root + 12*o + d
            if m > hi:
                return out
            out.append(m)
        o += 1

def notes_for(N, root, octaves, scale):
    full = _scale_notes(int(root), SCALES.get(scale, SCALES['pentatonic']), 100)
    base = [m for m in full if m <= root + 12*octaves]
    if len(base) < N:
        base = full[:max(N, len(base))]   # more strings than the range holds: keep climbing the scale
    L = len(base)
    if N == 1 or L == 1:
        return [base[0]]*N
    return [base[round(i*(L-1)/(N-1))] for i in range(N)]

def state():
    p = P()
    st = p.fetch('inst', None)
    if st is None:
        st = {'key': None, 'pr': False, 'cx': .5, 'cy': .5, 'px': .5, 'py': .5, 'lx': .5,
              'vend': [0.0]*NVOICES, 'vstart': [0.0]*NVOICES, 'vplaying': [False]*NVOICES}
        p.store('inst', st)
    return st

def palette():
    p = P()
    name = op('/project1/controls').par.Palette.eval()
    if name in PALETTES:
        return PALETTES[name]
    return (tuple(op('/project1/controls').parGroup.Colorlow.eval()), tuple(op('/project1/controls').parGroup.Colorhigh.eval()), tuple(op('/project1/controls').parGroup.Colorhit.eval()))

def pluck(st, i, vel, now):
    p = P()
    if now - st['last'][i] < 0.06:
        return
    st['last'][i] = now
    st['hit'][i] = max(st['hit'][i], vel)
    sb = mod('/project1/soundbank')
    midi = st['notes'][i]
    layer = 1 if vel > 0.55 else 0
    bend = op('/project1/controls').par.Bend.eval()*0.025*vel           # hard, fast plucks go slightly sharp
    free = [k for k in range(NVOICES) if st['vend'][k] < now]
    k = free[0] if free else min(range(NVOICES), key=lambda j: st['vstart'][j])
    v = op('/project1/voice%d' % k)
    v.par.speed = 1.0 + bend
    v.par.volume = 0.2 + 0.8*vel
    v.par.cuepoint = sb.slot_offset(midi, layer)
    v.par.play = 1
    v.par.cuepulse.pulse()
    st['vstart'][k] = now
    st['vend'][k] = now + (sb.SLOT - 0.15)/(1.0 + bend)
    st['vplaying'][k] = True

def step():
    p = P()
    st = state()
    now = absTime.seconds
    dt = 1.0/max(1.0, project.cookRate)
    N = int(op('/project1/controls').par.Strings.eval())
    key = (N, op('/project1/controls').par.Rootnote.eval(), op('/project1/controls').par.Range.eval(), op('/project1/controls').par.Scale.eval())
    if st['key'] != key:
        st['notes'] = notes_for(N, key[1], key[2], key[3])
        st['hit'] = [0.0]*N; st['env'] = [0.0]*N; st['last'] = [-1.0]*N
        st['key'] = key

    # ---- touch ----
    t = op('/project1/touch_source')
    pr = t['pressed'].eval() > 0.5
    tx, ty = t['tx'].eval(), t['ty'].eval()
    if pr:
        if not st['pr']:
            st['cx'] = st['px'] = st['lx'] = tx
            st['cy'] = st['py'] = ty
            i = min(N-1, max(0, int(tx*N)))
            if abs(tx - (i+0.5)/N) < 0.45/N:          # touched right on a string
                pluck(st, i, 0.55, now)
        else:
            st['cx'] += (tx - st['cx'])*0.6;  st['cy'] += (ty - st['cy'])*0.6
            st['px'] += (tx - st['px'])*0.18; st['py'] += (ty - st['py'])*0.18
            lx = st['lx']; dx = tx - lx
            if dx != 0.0:
                speed = abs(dx)/dt                     # screen widths per second
                vel = min(1.0, max(0.15, 0.2 + speed*0.45))
                lo, hi = min(lx, tx), max(lx, tx)
                i0 = max(0, math.ceil(lo*N - 0.5)); i1 = min(N-1, math.floor(hi*N - 0.5))
                rng = range(i0, i1+1) if dx > 0 else range(i1, i0-1, -1)
                for i in rng:
                    pluck(st, i, vel, now)
            st['lx'] = tx
    st['pr'] = pr

    # ---- release finished voices ----
    for k in range(NVOICES):
        if st['vplaying'][k] and st['vend'][k] < now:
            v = op('/project1/voice%d' % k)
            v.par.play = 0; v.par.volume = 0
            st['vplaying'][k] = False

    # ---- per-string energy: own pluck + room audio at the string's pitch ----
    sens = op('/project1/controls').par.Audiosens.eval()
    spec = op('/project1/mic_spectrum')
    ch = spec[0] if spec.numChans else None
    ns = spec.numSamples
    hz = (op('/project1/audio_in').rate*0.5)/max(1, ns)
    lvl = op('/project1/mic_level')[0].eval() if op('/project1/mic_level').numChans else 0.0
    for i in range(N):
        m = st['notes'][i]
        tau = 0.5 + 1.3*(100 - m)/72.0
        st['hit'][i] *= math.exp(-dt/tau)
        mag = 0.0
        if ch is not None and sens > 0:
            f = 440.0*2**((m-69)/12.0)
            for f2 in (f, 2*f):
                j = int(f2/hz)
                if 1 <= j < ns-1:
                    mag = max(mag, ch[j-1], ch[j], ch[j+1])
        target = min(1.0, sens*max(0.0, mag*6.0 + lvl*4.0 - op('/project1/controls').par.Gate.eval()))   # gate: quiet room = still strings
        e = st['env'][i]
        st['env'][i] = e + (target - e)*(0.5 if target > e else 0.08)

    # ---- drive the simulation ----
    E = op('/project1/controls').par.Elasticity.eval(); Nb = op('/project1/controls').par.Neighbors.eval()
    tension = 0.12 + 0.20*E
    coupling = 0.15*Nb
    damping = 0.035 - 0.027*E
    restore = 0.0015 + 0.004*E
    sx = max(0.03, 0.35/N)*op('/project1/controls').par.Touchradius.eval()
    for n in ('sim_a', 'sim_b'):
        s = op('/project1/' + n)
        s.par.vec0valuex = st['cx']; s.par.vec0valuey = st['cy']; s.par.vec0valuez = 1.0 if pr else 0.0
        s.par.vec1valuex = st['px']; s.par.vec1valuey = st['py']
        s.par.vec2valuex = tension; s.par.vec2valuey = coupling
        s.par.vec2valuez = damping; s.par.vec2valuew = restore
        s.par.vec3valuex = sx; s.par.vec3valuey = 0.13 + 0.14*(1.0 - (N - 5)/45.0)   # sparse strings: longer stretch

    # ---- drive the renderer ----
    r = op('/project1/strings')
    lo, hi_, hit = palette()
    r.par.vec0valuex = N
    r.par.vec1valuey = min(0.4/N, 0.02)   # vibration width scales with string spacing
    r.par.vec2valuex, r.par.vec2valuey, r.par.vec2valuez = lo
    r.par.vec3valuex, r.par.vec3valuey, r.par.vec3valuez = hi_
    r.par.vec4valuex, r.par.vec4valuey, r.par.vec4valuez = hit
    op('/project1/string_energy').cook(force=True)
