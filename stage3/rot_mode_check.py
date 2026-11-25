"""AG v17 (ChatGPT R3): failure mode on P4c rotated pages. Per page: exact-token recall, reversed-token recall
(each known word with characters reversed), and character-multiset recall of the page's characters in the whole output.
usage: python -I stage3/rot_mode_check.py OUT.json"""
import sys, os, json, glob, collections, warnings
warnings.simplefilter("ignore"); HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); sys.path.insert(0,HERE)
from conserve2 import toks
import pikepdf
def load(fid,p):
    if fid=="un_pdf":
        from unstructured.partition.auto import partition
        return "\n".join(e.text for e in partition(filename=p,content_type="application/pdf"))
    from markitdown import MarkItDown
    return MarkItDown().convert(p).text_content
out=[]; agg=collections.defaultdict(lambda:[0,0,0,0,0])
for sd in sorted(glob.glob(os.path.join(ROOT,"fixtures3_p4c","*"))):
    p=os.path.join(sd,"P04_rotated.pdf"); man=json.load(open(p+".json"))
    with pikepdf.open(p) as pdf: rots=[int(pg.obj.get("/Rotate",0))%360 for pg in pdf.pages]
    for fid in ("un_pdf","mk_pdf"):
        text=load(fid,p); O=toks(text); Orev=toks(text[::-1]); C=collections.Counter(c for c in text if not c.isspace())
        for i,u in enumerate(man["units"]):
            R=collections.Counter(); [R.update(toks(w)) for w in u["words"]]
            RR=collections.Counter(); [RR.update(toks(w[::-1])) for w in u["words"]]
            n=sum(R.values()); f=sum(min(v,O[t]) for t,v in R.items()); fr=sum(min(v,O[t]) for t,v in RR.items())
            fr2=sum(min(v,Orev[t]) for t,v in R.items())
            PC=collections.Counter(c for w in u["words"] for c in w if not c.isspace()); cr=sum(min(v,C[c]) for c,v in PC.items())/max(1,sum(PC.values()))
            out.append(dict(seed=os.path.basename(sd),loader=fid,page=i,rot=rots[i],n=n,exact=f,reversed=fr,cr=round(cr,3),outlen=len(text)))
            a=agg[(fid,rots[i])]; a[0]+=1; a[1]+=n; a[2]+=f; a[3]+=fr; a[4]+=(f==0 and fr==0)
        print(os.path.basename(sd),fid,len(text),flush=True)
json.dump(out,open(sys.argv[1],"w"))
print("loader rot pages tokens exact_found reversed_found pages_with_neither")
for k in sorted(agg): print(*k,*agg[k])
s=[r for r in out if r["seed"]=="20261401"]
print("seed 20261401:",[(r["loader"],r["rot"],r["n"],r["exact"],r["reversed"]) for r in s])
