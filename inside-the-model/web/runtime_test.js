// Gate 4: does the JS forward pass reproduce PyTorch logits? (run in Node)
const fs = require('fs');
const M = JSON.parse(fs.readFileSync(__dirname + '/model.json', 'utf8'));
const C = M.config, d = C.d, h = C.h, hd = d / h, L = C.L;

const dot = (a, b, ao = 0, bo = 0, n = a.length) => { let s = 0; for (let i = 0; i < n; i++) s += a[ao + i] * b[bo + i]; return s; };
const matvec = (W, x, bias) => W.map((row, o) => dot(row, x) + (bias ? bias[o] : 0)); // W: (out,in)
const add = (a, b) => a.map((v, i) => v + b[i]);
function layernorm(x, g, b, eps = 1e-5) {
  const n = x.length; let m = 0; for (const v of x) m += v; m /= n;
  let s = 0; for (const v of x) s += (v - m) * (v - m); s /= n;
  const inv = 1 / Math.sqrt(s + eps);
  return x.map((v, i) => (v - m) * inv * g[i] + b[i]);
}
function erf(x) { // Abramowitz-Stegun 7.1.26, ~1e-7
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return x >= 0 ? y : -y;
}
const gelu = x => 0.5 * x * (1 + erf(x / Math.SQRT2));
function softmax(a) { const m = Math.max(...a); let s = 0; const e = a.map(v => { const z = Math.exp(v - m); s += z; return z; }); return e.map(v => v / s); }

// returns { logits (last pos), resid (final-block residual, last pos) }
function forward(ids, injDelta = null) {
  const T = ids.length;
  let X = ids.map((id, t) => add(M.tok[id], M.pos[t]));        // T x d
  for (let li = 0; li < L; li++) {
    const ly = M.layers[li];
    const nrm = X.map(v => layernorm(v, ly.ln1_g, ly.ln1_b));
    const Q = [], K = [], V = [];
    for (let t = 0; t < T; t++) { const p = matvec(ly.in_w, nrm[t], ly.in_b); Q.push(p.slice(0, d)); K.push(p.slice(d, 2 * d)); V.push(p.slice(2 * d, 3 * d)); }
    const attn = X.map(() => new Array(d).fill(0));
    for (let head = 0; head < h; head++) {
      const off = head * hd;
      for (let i = 0; i < T; i++) {
        const sc = [];
        for (let j = 0; j <= i; j++) sc.push(dot(Q[i], K[j], off, off, hd) / Math.sqrt(hd));
        const w = softmax(sc);
        for (let j = 0; j <= i; j++) for (let k = 0; k < hd; k++) attn[i][off + k] += w[j] * V[j][off + k];
      }
    }
    const O = attn.map(a => matvec(ly.out_w, a, ly.out_b));
    X = X.map((v, t) => add(v, O[t]));
    const nrm2 = X.map(v => layernorm(v, ly.ln2_g, ly.ln2_b));
    X = X.map((v, t) => { const h1 = matvec(ly.fc1_w, nrm2[t], ly.fc1_b).map(gelu); const h2 = matvec(ly.fc2_w, h1, ly.fc2_b); return add(v, h2); });
  }
  let xl = X[T - 1].slice();
  if (injDelta) for (let i = 0; i < d; i++) xl[i] += injDelta[i];
  const xf = layernorm(xl, M.lnf_g, M.lnf_b);
  const logits = matvec(M.head_w, xf, M.head_b);
  return { logits, resid: xl };
}

let maxErr = 0;
M.parity.forEach((p, k) => {
  const out = forward(p.ids);
  const err = Math.max(...out.logits.map((v, i) => Math.abs(v - p.logits[i])));
  maxErr = Math.max(maxErr, err);
  console.log(`case ${k}: T=${p.ids.length}  maxAbsLogitErr=${err.toExponential(2)}  ` +
    `JS=[${out.logits.map(v => v.toFixed(3)).join(', ')}]`);
});
console.log(`\nGATE 4 ${maxErr < 1e-2 ? 'PASS ✅' : 'FAIL ❌'}  (max abs logit error ${maxErr.toExponential(2)}, tol 1e-2)`);
