# Reacts to the LOOM controls node
PRESETS = {'1920x1080':(1920,1080),'2560x1440':(2560,1440),'3840x2160':(3840,2160),'1280x720':(1280,720),
           '2560x1080':(2560,1080),'3840x1080':(3840,1080),'1080x1920':(1080,1920)}

def onValueChange(par, prev):
    c = par.owner
    if par.name == 'Respreset' and par.eval() in PRESETS:
        w, h = PRESETS[par.eval()]
        c.store('settingres', True)
        c.par.Resw = w; c.par.Resh = h
        c.store('settingres', False)
    elif par.name in ('Resw', 'Resh') and not c.fetch('settingres', False):
        cur = (c.par.Resw.eval(), c.par.Resh.eval())
        match = [k for k, v in PRESETS.items() if v == cur]
        c.par.Respreset = match[0] if match else 'custom'
    return

def onPulse(par):
    w = op('/project1/output_window')
    if par.name == 'Openwindow':
        w.par.winopen.pulse()
    elif par.name == 'Closewindow':
        w.par.winclose.pulse()
    return
