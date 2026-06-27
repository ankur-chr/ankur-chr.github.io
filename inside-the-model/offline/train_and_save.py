"""Train the tiny world-model transformer once, save checkpoint + probe for fast iteration."""
import torch, torch.nn as nn, numpy as np
from sklearn.linear_model import Ridge
torch.manual_seed(0); np.random.seed(0)
torch.set_num_threads(torch.get_num_threads())

GRID=7; START=(3,3); SEQ=64; VOCAB=4
DIRS={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}; TOK={'N':0,'S':1,'E':2,'W':3}
def legal_moves(x,y): return [d for d,(dx,dy) in DIRS.items() if 0<=x+dx<GRID and 0<=y+dy<GRID]
def gen_seq():
    x,y=START; toks,pos=[],[]
    for _ in range(SEQ):
        lm=legal_moves(x,y); d=lm[np.random.randint(len(lm))]
        dx,dy=DIRS[d]; x+=dx; y+=dy; toks.append(TOK[d]); pos.append((x,y))
    return toks,pos
def batch(n):
    T,P=[],[]
    for _ in range(n):
        t,p=gen_seq(); T.append(t); P.append(p)
    return torch.tensor(T),np.array(P)

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
        s.blocks=nn.ModuleList([Block(d,h) for _ in range(L)]); s.lnf=nn.LayerNorm(d); s.head=nn.Linear(d,vocab); s.d=d; s.L=L
    def forward(s,idx,return_hidden=False):
        B,T=idx.shape; x=s.tok(idx)+s.pos(torch.arange(T)[None]); mask=torch.triu(torch.full((T,T),float('-inf')),1); hid=[]
        for b in s.blocks: x=b(x,mask); hid.append(x)
        logits=s.head(s.lnf(x)); return (logits,hid) if return_hidden else logits

model=TinyGPT(); opt=torch.optim.AdamW(model.parameters(),lr=3e-3)
print("training...")
for step in range(1800):
    X,_=batch(128); logits=model(X[:,:-1])
    loss=nn.functional.cross_entropy(logits.reshape(-1,VOCAB),X[:,1:].reshape(-1))
    opt.zero_grad(); loss.backward(); opt.step()
    if step%600==0: print(f"  step {step} loss {loss.item():.3f}")
model.eval()
# fit ridge probe at layer 1 (best) -> x,y directions
Xt,Pt=batch(600)
with torch.no_grad(): _,H=model(Xt,return_hidden=True)
LAYER=1; A=H[LAYER].reshape(-1,model.d).numpy()
rx=Ridge(alpha=1.0).fit(A,Pt[:,:,0].reshape(-1)); ry=Ridge(alpha=1.0).fit(A,Pt[:,:,1].reshape(-1))
torch.save(model.state_dict(),"ckpt.pt")
np.savez("probe.npz", wx=rx.coef_, bx=rx.intercept_, wy=ry.coef_, by=ry.intercept_, layer=LAYER)
print(f"saved ckpt.pt + probe.npz (layer {LAYER}). params={sum(p.numel() for p in model.parameters()):,}")
