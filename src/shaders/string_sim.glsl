uniform vec4 uCur;    // finger x, y, pressed
uniform vec4 uPrev;   // lagged finger x, y (sweep start)
uniform vec4 uP;      // tension along string, coupling to neighbor strings, damping, restore
uniform vec4 uG;      // finger reach x, y
out vec4 fragColor;

// one column per string, rows run from bottom to top of the string
void main(){
    vec2 uv = vUV.st;
    vec2 px = 1.0/uTDOutputInfo.res.zw;
    vec2 c = texture(sTD2DInputs[0], uv).xy;       // x = sideways offset, y = velocity
    float l = texture(sTD2DInputs[0], uv - vec2(px.x,0.0)).x;
    float r = texture(sTD2DInputs[0], uv + vec2(px.x,0.0)).x;
    float u = texture(sTD2DInputs[0], uv + vec2(0.0,px.y)).x;
    float d = texture(sTD2DInputs[0], uv - vec2(0.0,px.y)).x;

    float a = uP.x*(u + d - 2.0*c.x) + uP.y*(l + r - 2.0*c.x) - uP.w*c.x - uP.z*c.y;

    float pos = uv.x + c.x;                          // where this bit of string is right now
    float x0 = min(uCur.x, uPrev.x), x1 = max(uCur.x, uPrev.x);
    float y0 = min(uCur.y, uPrev.y), y1 = max(uCur.y, uPrev.y);
    float dx = pos  - clamp(pos,  x0, x1);
    float dy = uv.y - clamp(uv.y, y0, y1);
    float g = exp(-(dx*dx)/(2.0*uG.x*uG.x) - (dy*dy)/(2.0*uG.y*uG.y)) * uCur.z;
    float fv = (uCur.x - uPrev.x)/4.5;
    a += g*0.30*(fv - c.y);                          // finger drags the string along
    a += g*0.02*((uCur.x - uv.x) - c.x);             // weak tether to the finger
    float vel = c.y + a;

    float off = clamp(c.x + vel, -0.45, 0.45);
    off = mix(off, 0.5*(u + d), 0.04);               // smooth along the string only
    float anchor = step(px.y*1.5, uv.y) * step(uv.y, 1.0 - px.y*1.5);
    fragColor = vec4(off*anchor, vel*anchor, 0.0, 1.0);
}
