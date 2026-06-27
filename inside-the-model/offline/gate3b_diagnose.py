"""
GATE 3 diagnosis: find an intervention that actually edits the model's belief.
Methods x layers:
  - cell-mean PATCH: swap the last-token residual's position-signature (mean residual of target cell
    minus mean of current cell). Gold-standard causal edit.
  - probe-direction inject (for comparison).
Inject after each block (0,1,2); injecting after the LAST block leaves no room to recompute.
Metric: does the model suppress moves that are walls at the FALSE (believed) cell?
"""
import torch, torch.nn as nn, numpy as np
np.random.seed(2); torch.manual_seed(2)
GRID=7; START=(3,3); SEQ=64; VOCAB=4
DIRS={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}; TOK={'N':0,'S':1,'E':2,'W':3}
def legal_set(x,y): return set(TOK[d] for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID)

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
        s.blocks=nn.ModuleList([Block(d,h) for _ in range(L)]); s.lnf=nn.LayerNorm(d); s.head=nn.Linear(d,vocab); s.d=d
    def run(s,idx,inj_layer=None,delta=None,allpos=False):
        B,T=idx.shape; x=s.tok(idx)+s.pos(torch.arange(T)[None]); mask=torch.triu(torch.full((T,T),float('-inf')),1); hid=[]
        for i,b in enumerate(s.blocks):
            x=b(x,mask)
            if inj_layer==i and delta is not None:
                x=x.clone()
                if allpos: x=x+delta
                else: x[:,-1,:]=x[:,-1,:]+delta
            hid.append(x)
        return s.head(s.lnf(x)), hid

m=TinyGPT(); m.load_state_dict(torch.load("ckpt.pt",weights_only=True)); m.eval()

# ---- collect residuals per layer with cell labels; build per-cell mean residual ----
def batch(n):
    T,P=[],[]
    for _ in range(n):
        x,y=START; toks,pos=[],[]
        for _ in range(SEQ):
            lm=[d for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID]
            d=lm[np.random.randint(len(lm))]; dx,dy=DIRS[d]; x+=dx; y+=dy; toks.append(TOK[d]); pos.append((x,y))
        T.append(toks); P.append(pos)
    return torch.tensor(T),np.array(P)
Xt,Pt=batch(800)
with torch.no_grad(): _,Hs=m.run(Xt)
NL=len(Hs)
cellmean=[np.zeros((GRID*GRID,m.d),dtype=np.float32) for _ in range(NL)]
for L in range(NL):
    A=Hs[L].reshape(-1,m.d).numpy(); cells=(Pt[:,:,0]*GRID+Pt[:,:,1]).reshape(-1)
    for c in range(GRID*GRID):
        sel=cells==c
        if sel.any(): cellmean[L][c]=A[sel].mean(0)

def walk_interior():
    x,y=START; toks=[]
    for _ in range(np.random.randint(8,40)):
        lm=[d for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID]
        d=lm[np.random.randint(len(lm))]; dx,dy=DIRS[d]; x+=dx; y+=dy; toks.append(TOK[d])
    return toks,(x,y)

def trial_set(N=500):
    out=[]
    for _ in range(N*3):
        toks,(x,y)=walk_interior()
        if not(1<=x<=5 and 1<=y<=5): continue
        tx,ty=np.random.randint(0,GRID),np.random.randint(0,GRID)
        ill=set(range(VOCAB))-legal_set(tx,ty)
        if (tx,ty)==(x,y) or not ill: continue
        out.append((toks,(x,y),(tx,ty),ill))
        if len(out)>=N: break
    return out
trials=trial_set(500)
print(f"{len(trials)} trials (true interior -> false edge/corner belief)\n")

for L in range(NL):
    for scale in [1.0,2.0,4.0]:
        succ=0; bi=[]; ii=[]
        for toks,(x,y),(tx,ty),ill in trials:
            idx=torch.tensor([toks])
            delta=torch.tensor(scale*(cellmean[L][tx*GRID+ty]-cellmean[L][x*GRID+y]))
            with torch.no_grad():
                base=torch.softmax(m.run(idx)[0][0,-1],-1)
                inj =torch.softmax(m.run(idx,L,delta)[0][0,-1],-1)
            b=float(sum(base[i] for i in ill)); a=float(sum(inj[i] for i in ill))
            bi.append(b); ii.append(a)
            if a<0.12: succ+=1
        tag="PATCH after block %d"%L
        print(f"{tag:18s} scale {scale:>3}:  success {succ/len(trials)*100:5.1f}%   illegal-prob {np.mean(bi)*100:4.1f}% -> {np.mean(ii)*100:4.1f}%")
    print()
