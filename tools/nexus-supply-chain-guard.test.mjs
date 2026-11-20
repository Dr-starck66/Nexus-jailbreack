import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import path from 'node:path';
import {tmpdir} from 'node:os';
import {classifyReference,scanSupplyChain,parseCli} from './nexus-supply-chain-guard.mjs';

async function fixture(tree,run){
  const d=await mkdtemp(path.join(tmpdir(),'nexus-guard-'));
  try{
    for(const [p,body] of Object.entries(tree)){
      const to=path.join(d,p);await mkdir(path.dirname(to),{recursive:true});await writeFile(to,body);
    }
    await run(d);
  }finally{await rm(d,{recursive:true,force:true});}
}
const codes=r=>r.findings.map(x=>x.code);
test('exact compromised pins flagged, underscores included',()=>{
  for(const v of ['1.26.1','1.26.2']){
    assert.equal(classifyReference('agent-framework=='+v)[0].code,'COMPROMISED_DEPENDENCY');
    assert.equal(classifyReference('"agent_framework": "'+v+'"')[0].code,'COMPROMISED_DEPENDENCY');
  }
});
test('different package and comments excluded',()=>{
  assert.deepEqual(classifyReference('agent-framework-core==1.26.2'),[]);
  assert.deepEqual(classifyReference('# agent-framework==1.26.2'),[]);
  assert.deepEqual(classifyReference('anthropic==1.26.2'),[]);
});
test('source manifests detect compromised pins, no secret content exposure',async()=>fixture({
  'requirements.txt':'agent-framework==1.26.1\n',
  '.env':'OPENAI_API_KEY=very-secret-dont-log'
},async d=>{
  const r=await scanSupplyChain([{mode:'source',path:d}]);
  assert.equal(r.status,'FAIL');assert.ok(codes(r).includes('COMPROMISED_DEPENDENCY'));
  assert.ok(!JSON.stringify(r).includes('very-secret-dont-log'));
}));
test('poetry and uv lock versions on next line are detected',async()=>fixture({
  'poetry.lock':'[[package]]\nname = "agent-framework"\nversion = "1.26.2"\n'
},async d=>{
  const r=await scanSupplyChain([{mode:'source',path:d}]);
  assert.equal(r.status,'FAIL');assert.ok(codes(r).includes('COMPROMISED_LOCKFILE'));
}));
test('unresolved range gives PARTIAL instead of PASS',async()=>fixture({
  'pyproject.toml':'dependencies = ["agent-framework>=1.26.0"]'
},async d=>assert.equal((await scanSupplyChain([{mode:'source',path:d}])).status,'PARTIAL')));
test('clean source scan is explicitly limited to source',async()=>fixture({
  'requirements-dev.txt':'pytest==8.4.0\n'
},async d=>{const r=await scanSupplyChain([{mode:'source',path:d}]);assert.equal(r.status,'PASS_SCOPED');assert.match(r.limits,/OTHER_ENVIRONMENTS/);}));
test('installed dist-info METADATA is inspected without Python',async()=>fixture({
  'site-packages/agent_framework-1.26.2.dist-info/METADATA':'Name: agent-framework\nVersion: 1.26.2\n'
},async d=>{const r=await scanSupplyChain([{mode:'runtime',path:path.join(d,'site-packages')}]);assert.equal(r.status,'FAIL');assert.ok(codes(r).includes('COMPROMISED_INSTALLED_PACKAGE'));}));
test('known .pth IOC signals FAIL even with no package metadata',async()=>fixture({
  'site-packages/af_runtime_diag.pth':'import af_runtime_diag\n'
},async d=>{const r=await scanSupplyChain([{mode:'runtime',path:path.join(d,'site-packages')}]);assert.equal(r.status,'FAIL');assert.ok(codes(r).includes('KNOWN_MALWARE_ARTIFACT'));}));
test('unknown executable startup hook is review only',async()=>fixture({
  'site-packages/vendor.pth':'import vendor_bootstrap\n'
},async d=>{const r=await scanSupplyChain([{mode:'runtime',path:path.join(d,'site-packages')}]);assert.equal(r.status,'PARTIAL');assert.ok(codes(r).includes('EXECUTABLE_PTH_REVIEW'));}));
test('source scanner excludes virtualenvs; runtime scanner explicitly accepts them',async()=>fixture({
  '.venv/lib/python3.12/site-packages/agent_framework_meta.pth':'import agent_framework_meta\n',
  'requirements.txt':'numpy==1.26.4\n'
},async d=>{
  assert.equal((await scanSupplyChain([{mode:'source',path:d}])).status,'PASS_SCOPED');
  assert.equal((await scanSupplyChain([{mode:'runtime',path:path.join(d,'.venv/lib/python3.12/site-packages')}])).status,'FAIL');
}));
test('missing runtime and empty runtime fail closed',async()=>fixture({
  'site-packages/hello.txt':'hello'
},async d=>{
  assert.equal((await scanSupplyChain([{mode:'runtime',path:path.join(d,'missing','site-packages')}])).status,'PARTIAL');
  assert.equal((await scanSupplyChain([{mode:'runtime',path:path.join(d,'site-packages')}])).status,'PARTIAL');
}));
test('symlinks are not followed',async()=>fixture({'requirements.txt':'numpy==1.26.4'},async d=>{
  await symlink(path.join(d,'requirements.txt'),path.join(d,'linked.txt'));
  const r=await scanSupplyChain([{mode:'source',path:d}]);assert.equal(r.status,'PARTIAL');assert.ok(codes(r).includes('SYMLINK_NOT_FOLLOWED'));
}));
test('CLI requires explicit paths and rejects unknown arguments',()=>{
  assert.deepEqual(parseCli(['--source','.']),[{mode:'source',path:'.'}]);
  assert.throws(()=>parseCli([]),/AT_LEAST_ONE/);
  assert.throws(()=>parseCli(['--runtime']),/PATH_REQUIRED/);
  assert.throws(()=>parseCli(['--eval']),/UNKNOWN_ARGUMENT/);
});
