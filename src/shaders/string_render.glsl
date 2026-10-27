uniform float uStrings;
uniform vec2 uTime;   // x = seconds, y = vibration width
uniform vec4 uLow;
uniform vec4 uHigh;
uniform vec4 uHit;
uniform float uThick;   // string thickness multiplier
out vec4 fragColor;

// input 0: string state (offset, velocity) one column per string
// input 1: energy, row 0 = own pluck, row 1 = room audio at the string's pitch
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;
    float N = uStrings;
    float e = 1.5/res.y;
    float belly = sin(3.14159*uv.y);                 // vibration is widest mid-string
    vec3 col = vec3(0.0);
    float maxReach = 70.0*max(1.0, uThick) + 1.5*belly*res.x*uTime.y;
    for(int k=0; k<50; k++){
        if(float(k) >= N) break;
        float xr = (float(k) + 0.5)/N;
        vec2 s = texture(sTD2DInputs[0], vec2(xr, uv.y)).xy;
        float dpx = (uv.x - (xr + s.x))*res.x;
        if(abs(dpx) > maxReach) continue;            // far from this string: one texture read and out
        float hit = texture(sTD2DInputs[1], vec2(xr, 0.25)).r;
        float env = texture(sTD2DInputs[1], vec2(xr, 0.75)).r;
        float vib = clamp(hit + env*0.6, 0.0, 1.5);
        float A = vib*belly*res.x*uTime.y*(0.65 + 0.35*sin(uTime.x*(38.0 + float(k)*2.7)));

        float sUp = texture(sTD2DInputs[0], vec2(xr, uv.y + e)).x;
        float sDn = texture(sTD2DInputs[0], vec2(xr, uv.y - e)).x;
        float m = (sUp - sDn)/(2.0*e)*(res.y/res.x);
        float dp = dpx/sqrt(1.0 + m*m);
        float dd = max(abs(dp) - A, 0.0);            // vibrating string reads as a blurred spindle
        float w = uThick*(1.0 + 0.5*vib);
        float core = exp(-dd*dd/(2.0*w*w))/(1.0 + A*0.08);
        float glow = exp(-abs(dp)/(7.0*sqrt(uThick) + A))*(0.18 + 0.35*vib);
        float stress = clamp(abs(s.x)*5.0 + abs(s.y)*60.0 + abs(m)*0.6, 0.0, 1.0);
        vec3 base = mix(uLow.rgb, uHigh.rgb, N > 1.0 ? float(k)/(N - 1.0) : 0.0);
        vec3 c = mix(base, uHit.rgb, clamp(stress*0.8 + hit*0.9, 0.0, 1.0));
        col += c*(core*(1.0 + 0.6*stress + 0.8*vib) + glow);
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
