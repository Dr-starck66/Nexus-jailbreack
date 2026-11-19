#!/usr/bin/env python3
"""Original stdlib-only geometry audit of the public EmotionScope .pt format.
Restricts pickle GLOBAL objects to known PyTorch storage primitives.
Not a Gemma forward pass, predictive evaluation or extraction replication.
"""
from __future__ import annotations
import argparse
import collections
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import pickle
import struct
import zipfile

SOURCE="https://github.com/saanidhi-git/EmotionScope/blob/main/results/vectors/google_gemma-2-2b-it.pt"
KNOWN_SHA256="e56af36b8d1ed5695694111ade1706453a1f65c6e145836cac872d9cb9c33cf2"
STRESS_POS=('afraid','nervous','desperate')
SHORTCUT_POS=('desperate','frustrated','nervous')
NEG=('calm','confident','reflective')
class FloatStorage: pass
@dataclass
class Storage:
    key: str
    size: int
@dataclass
class Tensor:
    storage: Storage
    offset: int
    size: tuple
    stride: tuple
def rebuild_tensor(storage,offset,size,stride,requires_grad,backward_hooks):
    if not isinstance(storage,Storage) or not (isinstance(size,tuple) and 1<=len(size)<=2):
        raise ValueError('Unsupported tensor layout')
    expected_stride=(1,) if len(size)==1 else (size[1],1)
    if offset!=0 or stride!=expected_stride or math.prod(size)!=storage.size:
        raise ValueError('Unsupported tensor offset, stride or size')
    return Tensor(storage,offset,size,stride)
class RestrictedCheckpointUnpickler(pickle.Unpickler):
    def find_class(self,module,name):
        allowed={('torch._utils','_rebuild_tensor_v2'):rebuild_tensor,
                 ('torch','FloatStorage'):FloatStorage,
                 ('collections','OrderedDict'):collections.OrderedDict}
        if (module,name) not in allowed:
            raise pickle.UnpicklingError('Disallowed pickle GLOBAL: '+module+'.'+name)
        return allowed[(module,name)]
    def persistent_load(self,pid):
        if type(pid) is not tuple or len(pid)!=5 or pid[0]!='storage':
            raise pickle.UnpicklingError('Invalid persistent reference')
        _,dtype,key,device,size=pid
        if dtype is not FloatStorage or device!='cpu' or not isinstance(key,str) or not key.isdigit() or not isinstance(size,int) or size<=0:
            raise pickle.UnpicklingError('Invalid float32 storage')
        return Storage(key,size)
def parse_checkpoint(path,expected_sha256=KNOWN_SHA256):
    raw=Path(path).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if expected_sha256 and digest!=expected_sha256:
        raise ValueError('Unexpected SHA-256: '+digest)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        pkl=[s for s in zf.namelist() if s.endswith('/data.pkl')]
        if len(pkl)!=1: raise ValueError('Not expected PyTorch ZIP')
        root=pkl[0][:-len('/data.pkl')]
        saved=RestrictedCheckpointUnpickler(io.BytesIO(zf.read(pkl[0]))).load()
        if not isinstance(saved,dict) or not isinstance(saved.get('vectors'),dict):
            raise ValueError('Invalid emotion vector dictionary')
        vectors={}
        for name,t in saved['vectors'].items():
            if not isinstance(name,str) or not isinstance(t,Tensor) or len(t.size)!=1:
                raise ValueError('Invalid emotion vector')
            b=zf.read(f'{root}/data/{t.storage.key}')
            if len(b)!=t.storage.size*4: raise ValueError('Incorrect vector bytes')
            vals=struct.unpack(f'<{t.storage.size}f',b)
            if not all(math.isfinite(x) for x in vals): raise ValueError('Non-finite weights')
            vectors[name]=vals
    return saved,vectors,digest,len(raw)
def dot(a,b): return math.fsum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def cos(a,b): return dot(a,b)/(norm(a)*norm(b))
def geometry_report(path,expected_sha256=KNOWN_SHA256):
    saved,vectors,digest,nbytes=parse_checkpoint(path,expected_sha256)
    info=saved.get('model_info')
    if not isinstance(info,dict) or info.get('model_name')!='google/gemma-2-2b-it' or info.get('d_model')!=2304 or saved.get('probe_layer_used')!=22:
        raise ValueError('Model/layer mismatch')
    if len(vectors)!=20 or {len(v) for v in vectors.values()}!={2304}:
        raise ValueError('Wrong emotion vector dimensions')
    keys=list(vectors)
    pairs=sorted((cos(vectors[x],vectors[y]),x,y) for i,x in enumerate(keys) for y in keys[i+1:])
    def mean(names):return [sum(vectors[n][i] for n in names)/len(names) for i in range(2304)]
    def sub(a,b):return [x-y for x,y in zip(a,b)]
    stress=sub(mean(STRESS_POS),mean(NEG))
    shortcut=sub(mean(SHORTCUT_POS),mean(NEG))
    magnitudes=list(map(norm,vectors.values()))
    return {
        'status':'PASS_REAL_VECTOR_GEOMETRY_ONLY','source':SOURCE,
        'artifact_sha256':digest,'artifact_bytes':nbytes,
        'model_info':info,'probe_layer_used':saved['probe_layer_used'],
        'n_vectors':len(vectors),'vector_dim':2304,
        'min_l2_norm':min(magnitudes),'max_l2_norm':max(magnitudes),
        'mean_off_diagonal_cosine':sum(p[0] for p in pairs)/len(pairs),
        'max_cosine_pair':list(pairs[-1]),'min_cosine_pair':list(pairs[0]),
        'proxy_stress_norm':norm(stress),
        'proxy_shortcut_norm':norm(shortcut),
        'proxy_stress_vs_shortcut_cosine':cos(stress,shortcut),
        'selected_cosines':{x+'__'+y:cos(vectors[x],vectors[y]) for x,y in [
            ('angry','hostile'),('angry','frustrated'),('hostile','frustrated'),
            ('afraid','nervous'),('desperate','nervous'),('calm','confident')]},
        'limitations':['No pretrained Gemma inference','No 48-item model scores','Not a head-to-head result']
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument('checkpoint')
    p.add_argument('--output',default='vector_geometry_audit.json')
    p.add_argument('--expected-sha256',default=KNOWN_SHA256)
    args=p.parse_args()
    result=geometry_report(args.checkpoint,args.expected_sha256)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
