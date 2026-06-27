"""
Build the shippable world-model: tiny transformer on a grid world WITH a lamp landmark.
Trains on next-token prediction over a stream of moves + forced <lamp> observations.
Verifies all gates, then EXPORTS weights + per-cell residual signatures + parity tests to ../web/model.json
"""
import torch, torch.nn as nn, numpy as np, json, os
torch.manual_seed(0); np.random.seed(0)

# ---------- world ----------
GRID=7; START=(3,3); LAMP=(5,1); SEQ=80
DIRS={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}
TOK={'N':0,'S':1,'E':2,'W':3,'LAMP':4}; NAMES=['N','S','E','W','LAMP']; VOCAB=5
def legal_dirs(x,y): return [d for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID]
def near_lamp(x,y): return abs(x-LAMP[0])+abs(y-LAMP[1])<=1

def gen_seq():
    """moves are legal random walk; after a move that lands near the lamp, the next token is forced <lamp>."""
    x,y=START; toks=[]; pos=[]; nextlamp=False
    while len(toks)<SEQ:
        if nextlamp:
            toks.append(TOK['LAMP']); pos.append((x,y)); nextlamp=False; continue
        d=legal_dirs(x,y); d=d[np.random.randint(len(d))]
        dx,dy=DIRS[d]; x+=dx; y+=dy
        toks.append(TOK[d]); pos.append((x,y))
        if near_lamp(x,y): nextlamp=True
    return toks[:SEQ], pos[:SEQ]

def batch(n):
    T,P=[],[]
    for _ in range(n):
        t,p=gen_seq(); T.append(t); P.append(p)
    return torch.tensor(T), np.array(P)

# ---------- model ----------
class Block(nn.Module):
    def __init__(s,d,h):
        super().__init__(); s.ln1=nn.LayerNorm(d); s.attn=nn.MultiheadAttention(d,h,batch_first=True)
        s.ln2=nn.LayerNorm(d); s.mlp=nn.Sequential(nn.Linear(d,4*d),nn.GELU(),nn.Linear(4*d,d))
    def forward(s,x,mask):
        q=s.ln1(x); a,_=s.attn(q,q,q,attn_mask=mask,need_weights=False); x=x+a
        return x+s.mlp(s.ln2(x))
class TinyGPT(nn.Module):
    def __init__(s,vocab=VOCAB,d=64,L=3,h=4,ctx=SEQ):
        super().__init__(); s.tok=nn.Embedding(vocab,d); s.pos=nn.Embedding(ctx,d)
        s.blocks=nn.ModuleList([Block(d,h) for _ in range(L)]); s.lnf=nn.LayerNorm(d); s.head=nn.Linear(d,vocab)
        s.d=d; s.L=L; s.h=h; s.ctx=ctx
    def run(s,idx,inj_layer=None,delta=None):
        B,T=idx.shape; x=s.tok(idx)+s.pos(torch.arange(T)[None]); mask=torch.triu(torch.full((T,T),float('-inf')),1); hid=[]
        for i,b in enumerate(s.blocks):
            x=b(x,mask)
            if inj_layer==i and delta is not None:
                x=x.clone(); x[:,-1,:]=x[:,-1,:]+delta
            hid.append(x)
        return s.head(s.lnf(x)), hid

m=TinyGPT(); opt=torch.optim.AdamW(m.parameters(),lr=3e-3)
print("training world+lamp model...")
for step in range(2600):
    X,_=batch(128); logits,_=m.run(X[:,:-1])
    loss=nn.functional.cross_entropy(logits.reshape(-1,VOCAB),X[:,1:].reshape(-1))
    opt.zero_grad(); loss.backward(); opt.step()
    if step%650==0: print(f"  step {step} loss {loss.item():.3f}")
m.eval()
print(f"  params {sum(p.numel() for p in m.parameters()):,}")

# ---------- residual signatures per cell at final block ----------
Xt,Pt=batch(800)
with torch.no_grad(): _,H=m.run(Xt)
FB=m.L-1                                   # final block index
A=H[FB].reshape(-1,m.d).numpy(); cells=(Pt[:,:,0]*GRID+Pt[:,:,1]).reshape(-1)
# Use only MOVE-step positions (token != LAMP): this is the "just arrived at this cell" state,
# the one whose next-token decision encodes both wall-legality AND lamp-visibility cleanly.
movemask=(Xt.numpy()!=TOK['LAMP']).reshape(-1)
cellmean=np.zeros((GRID*GRID,m.d),np.float32); cellcount=np.zeros(GRID*GRID)
for c in range(GRID*GRID):
    sel=(cells==c)&movemask
    if sel.any(): cellmean[c]=A[sel].mean(0); cellcount[c]=sel.sum()

# ---------- GATES ----------
# G1: position decodable
from sklearn.linear_model import Ridge, LogisticRegression
Xv,Pv=batch(200)
with torch.no_grad(): _,Hv=m.run(Xv)
Atr=H[FB].reshape(-1,m.d).numpy(); Ate=Hv[FB].reshape(-1,m.d).numpy()
clf=LogisticRegression(max_iter=400).fit(Atr,(Pt[:,:,0]*GRID+Pt[:,:,1]).reshape(-1))
acc=clf.score(Ate,(Pv[:,:,0]*GRID+Pv[:,:,1]).reshape(-1))
print(f"\nG1 cell-accuracy (final block): {acc*100:.1f}%  (chance {100/(GRID*GRID):.1f}%)")
# linear position probe (the in-browser 'mind reader' for live belief readout)
rx=Ridge(alpha=1.0).fit(Atr,Pt[:,:,0].reshape(-1)); ry=Ridge(alpha=1.0).fit(Atr,Pt[:,:,1].reshape(-1))

# G2 + Glamp: predicts legal moves, and predicts LAMP exactly when near lamp
with torch.no_grad():
    legal_ok=tot_move=0; illegal_mass=0.0; lamp_hit=lamp_tot=0
    for _ in range(60):
        x,y=START; toks=[]; nl=False
        for _ in range(SEQ):
            if toks:
                p=torch.softmax(m.run(torch.tensor([toks]))[0][0,-1],-1).numpy()
                if nl:  # next token should be LAMP
                    lamp_tot+=1; lamp_hit+= int(p.argmax()==TOK['LAMP'])
                else:
                    lm=set(TOK[d] for d in legal_dirs(x,y)); tot_move+=1
                    legal_ok+= int(p.argmax() in lm)
                    illegal_mass+= p[[i for i in range(4) if i not in lm]].sum()
            if nl:
                toks.append(TOK['LAMP']); nl=False; continue
            d=legal_dirs(x,y); d=d[np.random.randint(len(d))]; dx,dy=DIRS[d]; x+=dx; y+=dy
            toks.append(TOK[d]); nl=near_lamp(x,y)
print(f"G2 argmax-legal {legal_ok/tot_move*100:.1f}%  illegal-mass {illegal_mass/tot_move*100:.2f}%   "
      f"Glamp predict-LAMP-when-near {lamp_hit/lamp_tot*100:.1f}%")

# G3 causal: patch belief -> behaves as false cell (walls) AND hallucinates/【suppresses lamp
def walk_to(predicate, far_from_lamp=False):
    while True:
        x,y=START; toks=[]; nl=False
        for _ in range(np.random.randint(10,50)):
            if nl: toks.append(TOK['LAMP']); nl=False; continue
            d=legal_dirs(x,y); d=d[np.random.randint(len(d))]; dx,dy=DIRS[d]; x+=dx; y+=dy
            toks.append(TOK[d]); nl=near_lamp(x,y)
        if nl: continue
        if predicate(x,y): return toks,(x,y)
with torch.no_grad():
    # wall test: interior true -> edge/corner belief, suppress its walls
    succ=0;n=0
    for _ in range(300):
        toks,(x,y)=walk_to(lambda a,b: 1<=a<=5 and 1<=b<=5)
        tx,ty=np.random.randint(0,GRID),np.random.randint(0,GRID)
        ill=set(range(4))-set(TOK[d] for d in legal_dirs(tx,ty))
        if (tx,ty)==(x,y) or not ill or near_lamp(x,y): continue
        delta=torch.tensor(cellmean[tx*GRID+ty]-cellmean[x*GRID+y])
        inj=torch.softmax(m.run(torch.tensor([toks]),FB,delta)[0][0,-1],-1)
        n+=1; succ+= int(float(sum(inj[i] for i in ill))<0.12)
    print(f"G3 wall belief-edit success {succ/n*100:.1f}%  (n={n})")
    # lamp hallucination: true far from lamp -> believe a lamp-adjacent cell -> predicts LAMP
    hall=0;n2=0
    lampcells=[(a,b) for a in range(GRID) for b in range(GRID) if near_lamp(a,b)]
    for _ in range(300):
        toks,(x,y)=walk_to(lambda a,b: abs(a-LAMP[0])+abs(b-LAMP[1])>=3)
        tx,ty=lampcells[np.random.randint(len(lampcells))]
        delta=torch.tensor(cellmean[tx*GRID+ty]-cellmean[x*GRID+y])
        base=torch.softmax(m.run(torch.tensor([toks]))[0][0,-1],-1)[TOK['LAMP']]
        inj=torch.softmax(m.run(torch.tensor([toks]),FB,delta)[0][0,-1],-1)[TOK['LAMP']]
        n2+=1; hall+= int(float(inj)>0.5 and float(base)<0.2)
    print(f"G3 lamp hallucination success {hall/n2*100:.1f}%  (n={n2})")

# ---------- EXPORT ----------
def t(x): return x.detach().numpy().astype(np.float32).tolist()
layers=[]
for b in m.blocks:
    layers.append(dict(
        ln1_g=t(b.ln1.weight), ln1_b=t(b.ln1.bias),
        in_w=t(b.attn.in_proj_weight), in_b=t(b.attn.in_proj_bias),
        out_w=t(b.attn.out_proj.weight), out_b=t(b.attn.out_proj.bias),
        ln2_g=t(b.ln2.weight), ln2_b=t(b.ln2.bias),
        fc1_w=t(b.mlp[0].weight), fc1_b=t(b.mlp[0].bias),
        fc2_w=t(b.mlp[2].weight), fc2_b=t(b.mlp[2].bias)))
# parity test cases
parity=[]
with torch.no_grad():
    for _ in range(5):
        toks,_=gen_seq(); k=np.random.randint(5,40); ids=toks[:k]
        lg=m.run(torch.tensor([ids]))[0][0,-1]
        parity.append(dict(ids=ids, logits=t(lg)))
out=dict(
    config=dict(d=m.d,L=m.L,h=m.h,ctx=m.ctx,vocab=VOCAB,grid=GRID,start=list(START),lamp=list(LAMP),
                tokens=NAMES, final_block=FB),
    tok=t(m.tok.weight), pos=t(m.pos.weight), layers=layers,
    lnf_g=t(m.lnf.weight), lnf_b=t(m.lnf.bias), head_w=t(m.head.weight), head_b=t(m.head.bias),
    cellmean=cellmean.tolist(), cellcount=cellcount.tolist(),
    probe=dict(wx=rx.coef_.astype(np.float32).tolist(), bx=float(rx.intercept_),
               wy=ry.coef_.astype(np.float32).tolist(), by=float(ry.intercept_)),
    parity=parity)
os.makedirs("../web",exist_ok=True)
with open("../web/model.json","w") as f: json.dump(out,f)
sz=os.path.getsize("../web/model.json")/1024
print(f"\nexported ../web/model.json  ({sz:.0f} KB)")
