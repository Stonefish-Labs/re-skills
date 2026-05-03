from __future__ import annotations

from typing import Any

from .definitions import DefinitionIndex
from .models import ApiDef, ParamDef, TraceEvent, TypeDef


INTEGER_TYPES = {
    "BOOL",
    "BOOLEAN",
    "BYTE",
    "CHAR",
    "DWORD",
    "DWORD32",
    "DWORD64",
    "HRESULT",
    "INT",
    "LONG",
    "LONG32",
    "LONG64",
    "LONGLONG",
    "NTSTATUS",
    "SHORT",
    "UCHAR",
    "UINT",
    "UINT32",
    "UINT64",
    "ULONG",
    "ULONG32",
    "ULONG64",
    "ULONGLONG",
    "USHORT",
    "WORD",
}


def parse_numeric(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            return None
    return None


def decode_named_value(type_def: TypeDef | None, value: Any) -> dict[str, Any] | None:
    numeric = parse_numeric(value)
    if type_def is None or numeric is None:
        return None
    if type_def.has_enum:
        name = type_def.enum.get(numeric)
        return {"kind": "enum", "name": name, "value": numeric} if name else None
    if type_def.has_flags:
        matched = []
        for flag_value, flag_name in sorted(type_def.flags.items()):
            if flag_value == 0 and numeric == 0:
                matched.append(flag_name)
            elif flag_value != 0 and (numeric & flag_value) == flag_value:
                matched.append(flag_name)
        return {"kind": "flags", "names": matched, "value": numeric} if matched else None
    return None


def enrich_event(index: DefinitionIndex, event: TraceEvent) -> TraceEvent:
    api = index.find_api(event.get("api", ""), event.get("module"))
    if api is None:
        return event

    enriched = dict(event)
    enriched["signature"] = api.signature()
    enriched["success"] = evaluate_success(api, event.get("return_value"))

    args = []
    raw_args = event.get("args", [])
    for i, arg in enumerate(raw_args):
        new_arg = dict(arg)
        if i < len(api.params):
            param = api.params[i]
            decoded = decode_named_value(index.resolve_type(param.type), arg.get("value"))
            if decoded:
                new_arg["decoded"] = decoded
        args.append(new_arg)
    enriched["args"] = args

    return_decoded = decode_named_value(index.resolve_type(api.return_def.type), event.get("return_value"))
    if return_decoded:
        enriched["return_decoded"] = return_decoded
    return enriched


def evaluate_success(api: ApiDef, return_value: Any) -> bool | None:
    value = parse_numeric(return_value)
    if value is None:
        return None
    if api.success is not None:
        expected = parse_numeric(api.success.value)
        relation = (api.success.relation or "").lower()
        if relation == "notequal" and expected is not None:
            return value != expected
        if relation == "equal" and expected is not None:
            return value == expected
        if relation == "greaterthan" and expected is not None:
            return value > expected
        if relation == "lessthan" and expected is not None:
            return value < expected
    return_type = api.return_def.type.upper()
    if return_type in {"BOOL", "BOOLEAN"}:
        return value != 0
    if (api.error_func or "").lower() == "hresult":
        return value >= 0
    return None


def classify_param(
    index: DefinitionIndex,
    api: ApiDef,
    param: ParamDef,
    position: int,
    api_name: str | None = None,
) -> dict[str, Any]:
    param_type = param.type
    type_upper = param_type.upper()
    clean_upper = type_upper.replace("CONST ", "")
    charset_name = api_name or api.name
    string_type_tokens = (
        "LPSTR",
        "LPCSTR",
        "LPWSTR",
        "LPCWSTR",
        "LPTSTR",
        "LPCTSTR",
        "PSTR",
        "PCSTR",
        "PWSTR",
        "PCWSTR",
        "PTSTR",
        "PCTSTR",
        "BSTR",
        "LPOLESTR",
        "LPCOLESTR",
    )
    is_t_string = "TSTR" in clean_upper or "TCHAR" in clean_upper
    is_wide = (
        "WSTR" in clean_upper
        or "WCHAR" in clean_upper
        or "OLESTR" in clean_upper
        or "BSTR" in clean_upper
        or (is_t_string and charset_name.endswith("W"))
    )
    is_string = any(token in clean_upper for token in string_type_tokens) or (
        any(token in clean_upper for token in ["STR", "TCHAR", "WCHAR", "CHAR*"]) and "*" in clean_upper
    )
    has_length = param.attr("Length") is not None
    has_post_length = param.attr("PostLength") is not None
    has_count = param.attr("Count") is not None
    has_deref_post_count = param.attr("DerefPostCount") is not None
    resolved = index.resolve_type(param_type)

    if is_string:
        kind = "string"
    elif has_length or has_post_length or has_count or has_deref_post_count:
        kind = "buffer"
    elif "*" in param_type or clean_upper.startswith(("LP", "P")):
        kind = "pointer"
    else:
        kind = "value"

    return {
        "index": position,
        "name": param.name,
        "type": param.type,
        "kind": kind,
        "wide": is_wide,
        "length_param": param.attr("Length"),
        "post_length_param": param.attr("PostLength"),
        "count_param": param.attr("Count"),
        "deref_post_count": param.attr("DerefPostCount"),
        "output_only": param.is_output_only,
        "has_enum": bool(resolved and resolved.has_enum),
        "has_flags": bool(resolved and resolved.has_flags),
        "hints": {key: value for key, value in param.attrs.items() if key in {"Length", "PostLength", "Count", "DerefPostCount"}},
    }


def describe_value_decoder(index: DefinitionIndex, type_name: str) -> str | None:
    type_def = index.resolve_type(type_name)
    if type_def is None:
        return None
    if type_def.has_enum:
        preview = ", ".join(f"{name}={value:#x}" for value, name in list(type_def.enum.items())[:8])
        return f"enum {type_def.name}: {preview}"
    if type_def.has_flags:
        preview = ", ".join(f"{name}={value:#x}" for value, name in list(type_def.flags.items())[:8])
        return f"flags {type_def.name}: {preview}"
    return None
