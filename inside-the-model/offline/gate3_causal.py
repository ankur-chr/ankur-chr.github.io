"""
GATE 3 (the peak): edit the model's mind.
Inject a FALSE position into the residual stream (via the probe directions) and test whether
the model now predicts moves as if it were at the false location — e.g. refuses to 'walk into'
walls that only exist at the believed position.
"""
import torch, torch.nn as nn, numpy as np
np.random.seed(1); torch.manual_seed(1)

GRID=7; START=(3,3); SEQ=64; VOCAB=4
DIRS={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}; TOK={'N':0,'S':1,'E':2,'W':3}; NAMES=['N','S','E','W']
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
    def run(s,idx,inj_layer=None,inj_delta=None):
        B,T=idx.shape; x=s.tok(idx)+s.pos(torch.arange(T)[None]); mask=torch.triu(torch.full((T,T),float('-inf')),1)
        for i,b in enumerate(s.blocks):
            x=b(x,mask)
            if inj_layer==i and inj_delta is not None:
                x=x.clone(); x[:,-1,:]=x[:,-1,:]+inj_delta     # edit the 'current belief' (last token)
        return s.head(s.lnf(x))
    def residual(s,idx,layer):
        B,T=idx.shape; x=s.tok(idx)+s.pos(torch.arange(T)[None]); mask=torch.triu(torch.full((T,T),float('-inf')),1)
        for i,b in enumerate(s.blocks):
            x=b(x,mask)
            if i==layer: return x
        return x

m=TinyGPT(); m.load_state_dict(torch.load("ckpt.pt")); m.eval()
P=np.load("probe.npz"); wx=torch.tensor(P["wx"],dtype=torch.float32); wy=torch.tensor(P["wy"],dtype=torch.float32)
bx=float(P["bx"]); by=float(P["by"]); LAYER=int(P["layer"])

# solve [ax,ay] so adding ax*wx+ay*wy shifts probe readout by (dx,dy) (accounts for cross-talk)
G=torch.tensor([[float(wx@wx),float(wx@wy)],[float(wy@wx),float(wy@wy)]])
def delta_for(dx,dy,scale):
    a=torch.linalg.solve(G,torch.tensor([dx,dy],dtype=torch.float32)); return scale*(a[0]*wx+a[1]*wy)
def probe_read(idx):
    h=m.residual(idx,LAYER)[0,-1]; return float(wx@h+bx), float(wy@h+by)

def walk_to_interior():
    x,y=START; toks=[]
    for _ in range(np.random.randint(8,40)):
        lm=[d for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID]
        d=lm[np.random.randint(len(lm))]; dx,dy=DIRS[d]; x+=dx; y+=dy; toks.append(TOK[d])
    return toks,(x,y)

for scale in [1.0,1.5,2.0]:
    succ=0; n=0; base_ill=[]; inj_ill=[]; moved=[]
    for _ in range(400):
        toks,(x,y)=walk_to_interior()
        if not(1<=x<=5 and 1<=y<=5): continue          # need interior true pos (all 4 legal)
        tx,ty=np.random.randint(0,GRID),np.random.randint(0,GRID)
        if (tx,ty)==(x,y): continue
        illegal_at_target=set(range(VOCAB))-legal_set(tx,ty)
        if not illegal_at_target: continue              # need a wall to 'believe' in
        idx=torch.tensor([toks])
        delta=delta_for(tx-x,ty-y,scale)
        base=torch.softmax(m.run(idx)[0,-1],-1)
        inj =torch.softmax(m.run(idx,LAYER,delta)[0,-1],-1)
        # does the model now suppress the moves that are walls at the BELIEVED location?
        b_ill=float(sum(base[i] for i in illegal_at_target)); i_ill=float(sum(inj[i] for i in illegal_at_target))
        base_ill.append(b_ill); inj_ill.append(i_ill)
        px,py=probe_read(idx)  # sanity (pre-injection readout ~ true pos)
        n+=1
        if i_ill < 0.12: succ+=1
    print(f"scale {scale}:  N={n}  belief-edit success (suppresses walls of FALSE pos) ={succ/n*100:5.1f}%   "
          f"avg illegal-move prob: baseline {np.mean(base_ill)*100:4.1f}%  ->  after edit {np.mean(inj_ill)*100:4.1f}%")
