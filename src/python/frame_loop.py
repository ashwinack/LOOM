def onStart():
    # rebuild the plucked-string sound bank if it is missing (it is not stored in git)
    import os
    sb = mod('/project1/soundbank')
    if not os.path.exists(sb.bank_path()):
        sb.build()
        for k in range(12):
            op('/project1/voice%d' % k).par.reloadpulse.pulse()
    return

def onFrameStart(frame):
    mod('/project1/instrument').step()
    return
