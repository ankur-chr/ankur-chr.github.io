"""
P1 proof: does a tiny next-token transformer, trained ONLY to predict the next move
of an agent on a grid, secretly build a decodable internal map (agent x,y)?

Gate 1: agent position linearly decodable from residual stream (R^2 / cell accuracy).
Gate 2: the model actually predicts the LEGAL move set (it uses the position).
(Causal-edit gate handled in a follow-up once gates 1-2 pass.)
"""
import torch, torch.nn as nn, numpy as np
from sklearn.linear_model import Ridge, LogisticRegression

torch.manual_seed(0); np.random.seed(0)

# ---- world ----
GRID = 7
START = (3, 3)                      # fixed start => absolute position is determined by moves
DIRS = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
TOK = {'N': 0, 'S': 1, 'E': 2, 'W': 3}
NAMES = ['N', 'S', 'E', 'W']
VOCAB = 4
SEQ = 64

def legal_moves(x, y):
    return [d for d, (dx, dy) in DIRS.items() if 0 <= x + dx < GRID and 0 <= y + dy < GRID]

def gen_seq():
    x, y = START
    toks, pos, legalsets = [], [], []
    for _ in range(SEQ):
        lm = legal_moves(x, y)
        d = lm[np.random.randint(len(lm))]
        dx, dy = DIRS[d]; x += dx; y += dy
        toks.append(TOK[d]); pos.append((x, y)); legalsets.append(lm)
    return toks, pos, legalsets

def batch(n):
    T, P = [], []
    for _ in range(n):
        t, p, _ = gen_seq(); T.append(t); P.append(p)
    return torch.tensor(T), np.array(P)

# ---- tiny decoder-only transformer ----
class Block(nn.Module):
    def __init__(s, d, h):
        super().__init__()
        s.ln1 = nn.LayerNorm(d); s.attn = nn.MultiheadAttention(d, h, batch_first=True)
        s.ln2 = nn.LayerNorm(d); s.mlp = nn.Sequential(nn.Linear(d, 4*d), nn.GELU(), nn.Linear(4*d, d))
    def forward(s, x, mask):
        q = s.ln1(x); a, _ = s.attn(q, q, q, attn_mask=mask, need_weights=False); x = x + a
        x = x + s.mlp(s.ln2(x)); return x

class TinyGPT(nn.Module):
    def __init__(s, vocab=VOCAB, d=64, L=3, h=4, ctx=SEQ):
        super().__init__()
        s.tok = nn.Embedding(vocab, d); s.pos = nn.Embedding(ctx, d)
        s.blocks = nn.ModuleList([Block(d, h) for _ in range(L)])
        s.lnf = nn.LayerNorm(d); s.head = nn.Linear(d, vocab); s.d = d
    def forward(s, idx, return_hidden=False):
        B, T = idx.shape
        x = s.tok(idx) + s.pos(torch.arange(T, device=idx.device))[None]
        mask = torch.triu(torch.full((T, T), float('-inf')), diagonal=1)
        hid = []
        for b in s.blocks:
            x = b(x, mask); hid.append(x)
        logits = s.head(s.lnf(x))
        return (logits, hid) if return_hidden else logits

# ---- train ----
model = TinyGPT()
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
print("training tiny transformer on next-move prediction...")
for step in range(2500):
    X, _ = batch(128)
    logits = model(X[:, :-1])
    loss = nn.functional.cross_entropy(logits.reshape(-1, VOCAB), X[:, 1:].reshape(-1))
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 500 == 0:
        print(f"  step {step:4d}  loss {loss.item():.3f}")
nparams = sum(p.numel() for p in model.parameters())
print(f"  params: {nparams:,}")

# ---- GATE 2: does it predict the legal move set? ----
model.eval()
with torch.no_grad():
    correct_legal, total = 0, 0
    illegal_mass = 0.0
    for _ in range(50):
        x, y = START
        toks = []
        for t in range(SEQ):
            if toks:
                logits = model(torch.tensor([toks]))[0, -1]
                p = torch.softmax(logits, -1).numpy()
                lm = set(TOK[d] for d in legal_moves(x, y))
                illegal_mass += p[[i for i in range(VOCAB) if i not in lm]].sum()
                total += 1
                if int(p.argmax()) in lm: correct_legal += 1
            lm_names = legal_moves(x, y); d = lm_names[np.random.randint(len(lm_names))]
            dx, dy = DIRS[d]; x += dx; y += dy; toks.append(TOK[d])
    print(f"\nGATE 2  argmax-is-legal: {correct_legal/total*100:.1f}%   "
          f"avg prob mass on ILLEGAL moves: {illegal_mass/total*100:.2f}%  (lower=better)")

# ---- GATE 1: is agent position linearly decodable from the residual stream? ----
Xtr, Ptr = batch(500); Xte, Pte = batch(200)
with torch.no_grad():
    _, Htr = model(Xtr, return_hidden=True)
    _, Hte = model(Xte, return_hidden=True)
print("\nGATE 1  position decodability per layer:")
for layer in range(len(Htr)):
    A_tr = Htr[layer].reshape(-1, model.d).numpy(); A_te = Hte[layer].reshape(-1, model.d).numpy()
    yx_tr, yy_tr = Ptr[:, :, 0].reshape(-1), Ptr[:, :, 1].reshape(-1)
    yx_te, yy_te = Pte[:, :, 0].reshape(-1), Pte[:, :, 1].reshape(-1)
    rx = Ridge(alpha=1.0).fit(A_tr, yx_tr); ry = Ridge(alpha=1.0).fit(A_tr, yy_tr)
    r2x, r2y = rx.score(A_te, yx_te), ry.score(A_te, yy_te)
    cell_tr = (Ptr[:, :, 0] * GRID + Ptr[:, :, 1]).reshape(-1)
    cell_te = (Pte[:, :, 0] * GRID + Pte[:, :, 1]).reshape(-1)
    clf = LogisticRegression(max_iter=300, C=1.0).fit(A_tr, cell_tr)
    acc = clf.score(A_te, cell_te)
    print(f"  layer {layer}:  R2(x)={r2x:.3f}  R2(y)={r2y:.3f}   cell-accuracy={acc*100:.1f}%")
print("\n(chance cell-accuracy ~ {:.1f}%)".format(100/(GRID*GRID)))
