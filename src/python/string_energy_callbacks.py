def onCook(scriptOp):
    scriptOp.clear()
    p = op('/project1')
    st = p.fetch('inst', None)
    N = int(op('/project1/controls').par.Strings.eval())
    scriptOp.numSamples = N
    h = scriptOp.appendChan('hit')
    e = scriptOp.appendChan('env')
    if st and len(st.get('hit', [])) == N:
        h.vals = st['hit']
        e.vals = st['env']
    return
