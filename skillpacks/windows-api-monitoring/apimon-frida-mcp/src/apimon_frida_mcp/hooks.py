from __future__ import annotations

import json
from typing import Iterable

from .decoding import classify_param
from .definitions import DefinitionIndex
from .models import ApiDef


def build_hook_specs(index: DefinitionIndex, api_specs: Iterable[str]) -> list[dict]:
    specs: list[dict] = []
    for api_spec in api_specs:
        api = index.require_api(api_spec)
        specs.append(_hook_spec_for_api(index, api, requested=api_spec))
    return specs


def _hook_spec_for_api(index: DefinitionIndex, api: ApiDef, requested: str) -> dict:
    export_name = requested.split("!", 1)[-1].split(".", 1)[-1]
    if api.both_charset and export_name.lower() not in {api.name.lower(), f"{api.name.lower()}a", f"{api.name.lower()}w"}:
        export_name = api.name
    elif api.both_charset and export_name.lower() == api.name.lower():
        export_name = f"{api.name}W"

    return {
        "requested": requested,
        "module": api.module,
        "name": api.name,
        "export_name": export_name,
        "logical_api": f"{api.module}!{api.name}",
        "error_func": api.error_func,
        "return_type": api.return_def.type,
        "params": [classify_param(index, api, param, i, api_name=export_name) for i, param in enumerate(api.params)],
    }


def generate_trace_script(specs: list[dict], max_buffer_bytes: int = 256) -> str:
    specs_json = json.dumps(specs, ensure_ascii=True)
    return f"""
'use strict';

const SPECS = {specs_json};
const MAX_BUFFER_BYTES = {int(max_buffer_bytes)};

function ptrText(value) {{
  try {{ return value.toString(); }} catch (_) {{ return String(value); }}
}}

function ptrInt(value) {{
  try {{ return value.toUInt32(); }} catch (_) {{}}
  try {{ return value.toInt32(); }} catch (_) {{}}
  return null;
}}

function readU32Pointer(value) {{
  try {{
    if (value.isNull()) return null;
    return value.readU32();
  }} catch (e) {{
    return null;
  }}
}}

function readString(value, wide) {{
  try {{
    if (value.isNull()) return null;
    return wide ? value.readUtf16String() : value.readCString();
  }} catch (e) {{
    return {{ error: e.message, pointer: ptrText(value) }};
  }}
}}

function readBuffer(value, length) {{
  try {{
    if (value.isNull() || length === null || length <= 0) return null;
    const capped = Math.min(length, MAX_BUFFER_BYTES);
    const bytes = value.readByteArray(capped);
    if (bytes === null) return null;
    const view = new Uint8Array(bytes);
    let hex = "";
    for (let i = 0; i < view.length; i++) {{
      hex += view[i].toString(16).padStart(2, "0");
    }}
    return {{ hex, captured: capped, length }};
  }} catch (e) {{
    return {{ error: e.message, pointer: ptrText(value), length }};
  }}
}}

function findParam(params, name) {{
  if (!name) return null;
  for (const param of params) {{
    if (param.name === name) return param;
  }}
  return null;
}}

function lengthFromParam(params, rawArgs, name, afterCall) {{
  const param = findParam(params, name);
  if (param === null) return null;
  const raw = rawArgs[param.index];
  if (param.kind === "pointer" || param.type.indexOf("*") !== -1) {{
    return afterCall ? readU32Pointer(raw) : null;
  }}
  return ptrInt(raw);
}}

function decodeArg(param, rawArgs, afterCall) {{
  const raw = rawArgs[param.index];
  const decoded = {{
    name: param.name,
    type: param.type,
    pointer: ptrText(raw)
  }};

  if (param.kind === "string") {{
    decoded.value = readString(raw, param.wide);
  }} else if (param.kind === "buffer") {{
    const lengthName = afterCall && param.post_length_param
      ? param.post_length_param
      : (param.length_param || param.count_param || param.deref_post_count);
    const length = lengthFromParam(SPECS_BY_CURRENT.params, rawArgs, lengthName, afterCall);
    decoded.value = ptrText(raw);
    decoded.buffer = readBuffer(raw, length);
  }} else if (param.kind === "value") {{
    const asInt = ptrInt(raw);
    decoded.value = asInt === null ? ptrText(raw) : asInt;
  }} else {{
    decoded.value = ptrText(raw);
    if (afterCall && param.type.indexOf("*") !== -1) {{
      const pointed = readU32Pointer(raw);
      if (pointed !== null) decoded.deref_u32 = pointed;
    }}
  }}
  return decoded;
}}

let SPECS_BY_CURRENT = null;

function resolveExport(moduleName, exportName) {{
  const candidates = [moduleName];
  if (moduleName.toLowerCase().endsWith(".dll")) {{
    candidates.push(moduleName.slice(0, -4));
  }} else {{
    candidates.push(moduleName + ".dll");
  }}
  const lowerModule = moduleName.toLowerCase();
  if (lowerModule === "kernel32" || lowerModule === "kernel32.dll") {{
    candidates.push("KernelBase.dll");
    candidates.push("KernelBase");
  }}

  for (const candidate of candidates) {{
    try {{
      const module = Process.findModuleByName(candidate);
      if (module !== null && module.findExportByName !== undefined) {{
        const found = module.findExportByName(exportName);
        if (found !== null) return found;
      }}
    }} catch (_) {{}}
    try {{
      const found = Module.findExportByName(candidate, exportName);
      if (found !== null) return found;
    }} catch (_) {{}}
  }}
  try {{
    return Module.findGlobalExportByName(exportName);
  }} catch (_) {{
    return null;
  }}
}}

function hookSpec(spec) {{
  const address = resolveExport(spec.module, spec.export_name);
  if (address === null) {{
    send({{ type: "apimon.trace_error", error: "export not found", spec }});
    return;
  }}

  Interceptor.attach(address, {{
    onEnter(args) {{
      this.spec = spec;
      this.rawArgs = [];
      for (let i = 0; i < spec.params.length; i++) {{
        this.rawArgs.push(args[i]);
      }}
      SPECS_BY_CURRENT = spec;
      this.enterArgs = spec.params.map(param => decodeArg(param, this.rawArgs, false));
    }},
    onLeave(retval) {{
      SPECS_BY_CURRENT = this.spec;
      const leaveArgs = this.spec.params.map(param => decodeArg(param, this.rawArgs, true));
      let lastError = null;
      try {{ lastError = this.lastError; }} catch (_) {{}}
      send({{
        type: "apimon.trace_event",
        event: {{
          api: this.spec.logical_api,
          requested: this.spec.requested,
          module: this.spec.module,
          function: this.spec.name,
          export_name: this.spec.export_name,
          thread_id: this.threadId,
          depth: this.depth,
          return_address: ptrText(this.returnAddress),
          return_value: ptrText(retval),
          last_error: lastError,
          args: leaveArgs
        }}
      }});
    }}
  }});

  send({{ type: "apimon.hook_loaded", api: spec.logical_api, export_name: spec.export_name, address: ptrText(address) }});
}}

for (const spec of SPECS) {{
  try {{
    hookSpec(spec);
  }} catch (e) {{
    send({{ type: "apimon.trace_error", error: e.message, spec }});
  }}
}}
"""
