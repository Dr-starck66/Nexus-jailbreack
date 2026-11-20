/**
 * NEXUS / ASTRA Ω — offline supply-chain gate for Python agent runtimes.
 * Provenance: ASTRA PyPI guard PR #307, with extended installed-runtime inspection.
 * No Python process, pip, subprocess, network, credential reads, or code evaluation.
 * Threat intel: GHSA-764m-3ppc-5m73 (2026-11-18).
 */
import { lstat, readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const BAD = new Set(['1.26.1', '1.26.2']);
const IOC = new Set(['agent_framework_meta.pth', 'af_runtime_diag.pth', 'af_runtime_diag.py']);
const IGNORE = new Set(['.git', 'node_modules', '.venv', 'venv', '__pycache__', '.next', 'build', 'dist', '.cache']);
const MANIFEST = /^(?:requirements(?:[-_.\w]*)\.txt|pyproject\.toml|poetry\.lock|uv\.lock|Pipfile(?:\.lock)?|setup\.py|setup\.cfg|environment\.ya?ml)$/i;
const REFS = /(^|[^\w-])agent[-_]framework(?![\w-])(?:\[[^\]]*\])?\s*["\']?\s*(?:(===|==|~=|>=|<=|>|<|=|:)\s*["']?\s*)?([0-9]+\.[0-9]+\.[0-9]+)?/gim;
const LIMIT_FILES = 25000;
const LIMIT_SIZE = 4_000_000;

// Not a resolver: a clean pinned version is not proof of what pip actually installed.
export function classifyReference(line) {
  const src = String(line).replace(/\s+#.*$/, '').trim();
  if (!src || src.startsWith('#')) return [];
  const hits=[];
  for (const m of src.matchAll(REFS)) {
    const version=m[3] || null;
    const op=m[2] || null;
    const pinned = ['===','==','='].includes(op);
    hits.push({version, code:BAD.has(version)?'COMPROMISED_DEPENDENCY':!pinned||!version?'UNRESOLVED_DEPENDENCY':'OTHER_PINNED_VERSION'});
  }
  return hits;
}

function classifyMetadata(file, text) {
  const folder=path.basename(path.dirname(file)).toLowerCase().replace(/-/g,'_');
  if (!/^agent_framework(?:-[^/]+)?\.dist_info$/.test(folder) && !/^agent_framework(?:_[^/]+)?\.dist_info$/.test(folder)) return [];
  const packageName=/^Name:\s*([^\r\n]+)/mi.exec(text)?.[1]?.trim().toLowerCase().replace(/_/g,'-');
  const version=/^Version:\s*([^\r\n]+)/mi.exec(text)?.[1]?.trim() || null;
  if (packageName!=='agent-framework') return [];
  return [{version,code:BAD.has(version)?'COMPROMISED_INSTALLED_PACKAGE':version?'OTHER_INSTALLED_VERSION':'MISSING_INSTALLED_VERSION'}];
}

export async function scanSupplyChain(targets = []) {
  const findings=[];
  const stats={filesVisited:0,sourceManifests:0,runtimeMetadata:0,startupHooks:0,skippedSymlinks:0,unreadable:0};
  let incomplete=false;
  let sourceTargets=0, runtimeTargets=0;
  const add=(file, code, severity, extras={})=>findings.push({file,code,severity,...extras});
  async function scan(target,mode){
    if(stats.filesVisited>=LIMIT_FILES){incomplete=true;return;}
    let st;
    try {st=await lstat(target);}catch {incomplete=true;stats.unreadable++;add(target,'TARGET_UNREADABLE','PARTIAL');return;}
    if(st.isSymbolicLink()) {stats.skippedSymlinks++;incomplete=true;add(target,'SYMLINK_NOT_FOLLOWED','PARTIAL');return;}
    if(st.isDirectory()) {
      if(mode==='source' && IGNORE.has(path.basename(target))) return;
      let entries;
      try {entries=(await readdir(target)).sort();}catch {incomplete=true;stats.unreadable++;add(target,'DIRECTORY_UNREADABLE','PARTIAL');return;}
      for(const entry of entries){if(mode==='source' && IGNORE.has(entry))continue;await scan(path.join(target,entry),mode);}
      return;
    }
    if(!st.isFile()) return;
    stats.filesVisited++;
    const base=path.basename(target);
    const parent=path.basename(path.dirname(target));
    const known=IOC.has(base) || (base==='_telemetry.py' && parent==='agent_framework_meta');
    if(known) add(target,'KNOWN_MALWARE_ARTIFACT','FAIL');
    const isManifest=mode==='source'&&MANIFEST.test(base);
    const isMetadata=mode==='runtime'&&base==='METADATA'&&/agent[-_]framework.*\.dist-info$/i.test(parent);
    const isPth=mode==='runtime'&&base.endsWith('.pth');
    if(!isManifest&&!isMetadata&&!isPth)return;
    if(st.size>LIMIT_SIZE){incomplete=true;add(target,'FILE_TOO_LARGE','PARTIAL');return;}
    let text;
    try{text=await readFile(target,'utf8');}catch{incomplete=true;stats.unreadable++;add(target,'FILE_UNREADABLE','PARTIAL');return;}
    if(isManifest){
      stats.sourceManifests++;
      const lines=text.split(/\r?\n/);
      for(let i=0;i<lines.length;i++){
        for(const hit of classifyReference(lines[i]))add(target,hit.code,hit.code==='COMPROMISED_DEPENDENCY'?'FAIL':hit.code==='UNRESOLVED_DEPENDENCY'?'PARTIAL':'INFO',{line:i+1,version:hit.version});
        // Poetry/uv TOML locks use name and version on separate lines.
        if(/^\s*name\s*=\s*['"]agent[-_]framework['"]\s*(?:#.*)?$/i.test(lines[i])) {
          for(let j=i+1;j<Math.min(i+10,lines.length);j++){
            if(/^\s*\[/.test(lines[j])||/^\s*name\s*=/.test(lines[j]))break;
            const m=/^\s*version\s*=\s*['"]([^'"]+)['"]/.exec(lines[j]);
            if(m){add(target,BAD.has(m[1])?'COMPROMISED_LOCKFILE':'OTHER_LOCKFILE_VERSION',BAD.has(m[1])?'FAIL':'INFO',{line:j+1,version:m[1]});break;}
          }
        }
      }
    }
    if(isMetadata){
      stats.runtimeMetadata++;
      for(const hit of classifyMetadata(target,text))add(target,hit.code,hit.code==='COMPROMISED_INSTALLED_PACKAGE'?'FAIL':hit.code==='MISSING_INSTALLED_VERSION'?'PARTIAL':'INFO',{version:hit.version});
    }
    if(isPth){
      stats.startupHooks++;
      if(text.split(/\r?\n/).some(line=>/^\s*import(?:\s|\()/.test(line))) add(target,'EXECUTABLE_PTH_REVIEW','PARTIAL');
    }
  }
  for(const input of targets){
    const mode=input?.mode;
    if(!['source','runtime'].includes(mode)||typeof input.path!=='string'||!input.path.trim()){
      incomplete=true;add(null,'INVALID_TARGET','PARTIAL');continue;
    }
    mode==='source'?sourceTargets++:runtimeTargets++;
    const root=path.resolve(input.path);
    if(mode==='runtime'&&!/(?:^|[\\/])(?:site-packages|dist-packages)$/.test(root)){
      incomplete=true;add(root,'RUNTIME_TARGET_MUST_BE_SITE_PACKAGES','PARTIAL');continue;
    }
    await scan(root,mode);
  }
  const foundFail=findings.some(x=>x.severity==='FAIL');
  const foundPartial=findings.some(x=>x.severity==='PARTIAL');
  const noEvidence=!(stats.sourceManifests||stats.runtimeMetadata||stats.startupHooks);
  const status=foundFail?'FAIL':incomplete||foundPartial||noEvidence?'PARTIAL':'PASS_SCOPED';
  return {schema:'nexus-astra-supply-chain/1',status,targets:{source:sourceTargets,runtime:runtimeTargets},stats,findings,proof:'SCANNED_FILES_ONLY',limits:'ONLY_TARGET_PATHS; OTHER_ENVIRONMENTS_AND_BUILD_CACHES_UNVERIFIED; NO_SECRETS_READ'};
}

export function parseCli(args){
  const targets=[];
  for(let i=0;i<args.length;i++){
    if(args[i]==='--source'||args[i]==='--runtime'){
      if(!args[i+1]||args[i+1].startsWith('--'))throw Error('PATH_REQUIRED_FOR_'+args[i].slice(2).toUpperCase());
      targets.push({mode:args[i].slice(2),path:args[++i]});
    }else throw Error('UNKNOWN_ARGUMENT');
  }
  if(!targets.length)throw Error('AT_LEAST_ONE_SOURCE_OR_RUNTIME_PATH_REQUIRED');
  return targets;
}

if(process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  let report;
  try {report=await scanSupplyChain(parseCli(process.argv.slice(2)));}
  catch(e){report={schema:'nexus-astra-supply-chain/1',status:'PARTIAL',reason:e.message};}
  process.stdout.write(JSON.stringify(report,null,2)+'\n');
  process.exitCode=report.status==='FAIL'?2:report.status==='PASS_SCOPED'?0:1;
}
