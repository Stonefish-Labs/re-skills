from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from .models import ApiDef, FieldDef, ParamDef, ReturnDef, SearchResult, SuccessRule, TypeDef


def _norm_name(value: str) -> str:
    return value.strip().lower()


def _norm_module(value: str) -> str:
    value = value.strip().lower()
    return value[:-4] if value.endswith(".dll") else value


def _clean_type_name(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^(const|volatile)\s+", "", value)
    value = value.replace(" __RPC_FAR", "")
    return value.strip()


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    try:
        return int(text, 0)
    except ValueError:
        return None


class DefinitionIndex:
    def __init__(self) -> None:
        self.types: dict[str, TypeDef] = {}
        self.apis: dict[tuple[str, str], ApiDef] = {}
        self.api_aliases: dict[tuple[str, str], ApiDef] = {}

    def add_type(self, type_def: TypeDef) -> None:
        key = _norm_name(type_def.name)
        existing = self.types.get(key)
        if existing is None or (not existing.fields and not existing.enum and not existing.flags):
            self.types[key] = type_def

    def add_api(self, api_def: ApiDef) -> None:
        module_key = _norm_module(api_def.module)
        name_key = _norm_name(api_def.name)
        key = (module_key, name_key)
        existing = self.apis.get(key)
        if existing is None or (existing.is_stub and not api_def.is_stub):
            self.apis[key] = api_def
        self._add_api_aliases(module_key, api_def)

    def _add_api_aliases(self, module_key: str, api_def: ApiDef) -> None:
        names = {api_def.name}
        if api_def.both_charset and not api_def.name.endswith(("A", "W")):
            names.add(f"{api_def.name}A")
            names.add(f"{api_def.name}W")
        modules = {module_key, api_def.module.lower()}
        if api_def.module.lower().endswith(".dll"):
            modules.add(api_def.module[:-4].lower())
        for module in modules:
            for name in names:
                alias_key = (_norm_module(module), _norm_name(name))
                existing = self.api_aliases.get(alias_key)
                if existing is None or (existing.is_stub and not api_def.is_stub):
                    self.api_aliases[alias_key] = api_def

    def find_type(self, type_name: str | None) -> TypeDef | None:
        if not type_name:
            return None
        candidates = [type_name, _clean_type_name(type_name)]
        cleaned = _clean_type_name(type_name)
        candidates.append(cleaned.rstrip("*").strip())
        unbracketed = cleaned.strip("[]")
        if unbracketed != cleaned:
            candidates.append(unbracketed)
        elif unbracketed:
            candidates.append(f"[{unbracketed}]")
        for candidate in candidates:
            found = self.types.get(_norm_name(candidate))
            if found:
                return found
        return None

    def resolve_type(self, type_name: str | None, max_depth: int = 8) -> TypeDef | None:
        current = self.find_type(type_name)
        if current is None:
            return None

        merged_enum: dict[int, str] = dict(current.enum)
        merged_flags: dict[int, str] = dict(current.flags)
        merged_fields = list(current.fields)
        first = current
        depth = 0
        while current and current.kind.lower() == "alias" and current.base and depth < max_depth:
            nested = self.find_type(current.base)
            if nested is None:
                break
            inherited_enum = dict(nested.enum)
            inherited_enum.update(merged_enum)
            merged_enum = inherited_enum

            inherited_flags = dict(nested.flags)
            inherited_flags.update(merged_flags)
            merged_flags = inherited_flags

            if not merged_fields and nested.fields:
                merged_fields = list(nested.fields)
            current = nested
            depth += 1
        if merged_enum or merged_flags or merged_fields:
            return TypeDef(
                name=first.name,
                kind=first.kind,
                base=first.base,
                display=first.display,
                fields=merged_fields,
                enum=merged_enum,
                flags=merged_flags,
                count=first.count,
                source=first.source,
            )
        return current or first

    def find_api(self, spec: str, module: str | None = None) -> ApiDef | None:
        parsed_module, parsed_name = split_api_spec(spec)
        if module and not parsed_module:
            parsed_module = module
        if parsed_module:
            return self.api_aliases.get((_norm_module(parsed_module), _norm_name(parsed_name)))

        matches = [api for (mod, name), api in self.api_aliases.items() if name == _norm_name(parsed_name)]
        if not matches:
            return None
        matches.sort(key=lambda api: (api.is_stub, api.module.lower(), api.name.lower()))
        return matches[0]

    def require_api(self, spec: str, module: str | None = None) -> ApiDef:
        api = self.find_api(spec, module)
        if api is None:
            raise KeyError(f"API definition not found: {spec}")
        return api

    def search(self, query: str, kind: str | None = None, module: str | None = None, limit: int = 50) -> list[SearchResult]:
        q = query.lower()
        kind_filter = _normalize_kind(kind)
        module_filter = _norm_module(module) if module else None
        results: list[SearchResult] = []

        if kind_filter in {None, "api"}:
            seen: set[tuple[str, str]] = set()
            for (mod, name), api in sorted(self.apis.items()):
                if module_filter and mod != module_filter:
                    continue
                haystack = " ".join(part or "" for part in [api.module, api.name, api.category, api.signature()]).lower()
                if q in haystack and (mod, name) not in seen:
                    results.append(SearchResult("api", api.display_name, api.signature(), str(api.source) if api.source else None))
                    seen.add((mod, name))
                if len(results) >= limit:
                    return results

        if kind_filter in {None, "type", "enum", "flag", "interface"}:
            for type_def in sorted(self.types.values(), key=lambda item: item.name.lower()):
                type_kind = type_def.kind.lower()
                if kind_filter == "enum" and not type_def.has_enum:
                    continue
                if kind_filter == "flag" and not type_def.has_flags:
                    continue
                if kind_filter == "interface" and type_kind != "interface":
                    continue
                if kind_filter == "type" and type_kind == "interface":
                    continue
                value_names = " ".join([*type_def.enum.values(), *type_def.flags.values()])
                haystack = " ".join(
                    [type_def.name, type_def.kind, type_def.base or "", type_def.display or "", value_names]
                ).lower()
                if q in haystack:
                    detail = type_def.kind
                    if type_def.base:
                        detail += f" base={type_def.base}"
                    if type_def.has_enum:
                        detail += f" enum={len(type_def.enum)}"
                    if type_def.has_flags:
                        detail += f" flags={len(type_def.flags)}"
                    if type_def.fields:
                        detail += f" fields={len(type_def.fields)}"
                    results.append(SearchResult("type", type_def.name, detail, str(type_def.source) if type_def.source else None))
                if len(results) >= limit:
                    return results
        return results


class ApiMonitorDefinitions:
    def __init__(self, api_root: str | Path) -> None:
        self.api_root = Path(api_root)
        self.index = DefinitionIndex()
        self._seen_files: set[Path] = set()
        self._loaded = False
        self.errors: list[str] = []

    def load_all(self) -> DefinitionIndex:
        if self._loaded:
            return self.index
        if not self.api_root.exists():
            raise FileNotFoundError(f"API Monitor XML root not found: {self.api_root}")
        xml_files = sorted(self.api_root.rglob("*.xml"))
        if not xml_files:
            raise FileNotFoundError(
                f"No API Monitor XML files found in {self.api_root}. "
                "Copy API Monitor's API folder contents into api-monitor-xml, "
                "or set APIMON_XML_ROOT to the folder that contains Headers/ and Windows/."
            )
        for xml_file in xml_files:
            self.parse_file(xml_file)
        self._loaded = True
        return self.index

    def parse_file(self, path: str | Path) -> None:
        xml_path = self._resolve_path(path)
        if xml_path in self._seen_files or not xml_path.exists():
            return
        self._seen_files.add(xml_path)

        root = self._parse_xml_root(xml_path)
        if root is None:
            return
        for include in root.findall("Include"):
            filename = include.attrib.get("Filename")
            if filename:
                self.parse_file(filename)

        for variable in root.findall(".//Variable"):
            self._parse_variable(variable, xml_path)

        for module in root.findall("Module"):
            self._parse_module(module, xml_path)

    def _parse_xml_root(self, xml_path: Path) -> ET.Element | None:
        try:
            return ET.parse(xml_path).getroot()
        except ET.ParseError as first_error:
            try:
                text = xml_path.read_text(encoding="utf-8-sig")
                first_tag = text.find("<")
                if first_tag > 0:
                    return ET.fromstring(text[first_tag:])
            except Exception:
                pass
            self.errors.append(f"{xml_path}: {first_error}")
            return None

    def _resolve_path(self, path: str | Path) -> Path:
        if isinstance(path, Path) and path.is_absolute():
            return path.resolve()
        path_text = str(path).replace("\\", "/")
        candidate = Path(path_text)
        if candidate.is_absolute():
            return candidate.resolve()
        if candidate.parts and candidate.parts[0] == self.api_root.name:
            return candidate.resolve()
        return (self.api_root / candidate).resolve()

    def _parse_module(self, module_node: ET.Element, source: Path) -> None:
        module_name = module_node.attrib.get("Name", source.stem)
        calling_convention = module_node.attrib.get("CallingConvention")
        error_func = module_node.attrib.get("ErrorFunc")
        online_help = module_node.attrib.get("OnlineHelp")
        category: str | None = None

        for child in module_node:
            if child.tag == "Variable":
                self._parse_variable(child, source)
            elif child.tag == "Category":
                category = child.attrib.get("Name")
            elif child.tag == "Api":
                api = self._parse_api(
                    child,
                    module_name=module_name,
                    calling_convention=calling_convention,
                    error_func=error_func,
                    online_help=online_help,
                    category=category,
                    source=source,
                )
                self.index.add_api(api)

    def _parse_variable(self, node: ET.Element, source: Path) -> None:
        name = node.attrib.get("Name")
        kind = node.attrib.get("Type")
        if not name or not kind:
            return

        enum: dict[int, str] = {}
        flags: dict[int, str] = {}
        fields: list[FieldDef] = []
        display = None

        display_node = node.find("Display")
        if display_node is not None:
            display = display_node.attrib.get("Name")

        for field_node in node.findall("Field"):
            field_name = field_node.attrib.get("Name")
            field_type = field_node.attrib.get("Type")
            if field_name and field_type:
                fields.append(FieldDef(type=field_type, name=field_name, attrs=dict(field_node.attrib)))

        enum_node = node.find("Enum")
        if enum_node is not None:
            enum.update(_parse_sets(enum_node.findall("Set")))

        flag_node = node.find("Flag")
        if flag_node is not None:
            flags.update(_parse_sets(flag_node.findall("Set")))

        self.index.add_type(
            TypeDef(
                name=name,
                kind=kind,
                base=node.attrib.get("Base"),
                display=display,
                fields=fields,
                enum=enum,
                flags=flags,
                count=node.attrib.get("Count"),
                source=source,
            )
        )

    def _parse_api(
        self,
        node: ET.Element,
        module_name: str,
        calling_convention: str | None,
        error_func: str | None,
        online_help: str | None,
        category: str | None,
        source: Path,
    ) -> ApiDef:
        params: list[ParamDef] = []
        for param_node in node.findall("Param"):
            param_type = param_node.attrib.get("Type", "LPVOID")
            param_name = param_node.attrib.get("Name", f"arg{len(params)}")
            params.append(ParamDef(type=param_type, name=param_name, attrs=dict(param_node.attrib)))

        return_node = node.find("Return")
        return_def = ReturnDef(
            type=return_node.attrib.get("Type", "void") if return_node is not None else "void",
            attrs=dict(return_node.attrib) if return_node is not None else {},
        )

        success_node = node.find("Success")
        success = None
        if success_node is not None:
            success = SuccessRule(
                relation=success_node.attrib.get("Return"),
                value=success_node.attrib.get("Value"),
            )

        return ApiDef(
            module=module_name,
            name=node.attrib.get("Name", ""),
            calling_convention=calling_convention,
            error_func=error_func,
            online_help=online_help,
            category=category,
            params=params,
            return_def=return_def,
            success=success,
            attrs=dict(node.attrib),
            source=source,
        )


def _parse_sets(nodes: Iterable[ET.Element]) -> dict[int, str]:
    values: dict[int, str] = {}
    for item in nodes:
        value = _parse_int(item.attrib.get("Value"))
        name = item.attrib.get("Name")
        if value is not None and name:
            values[value] = name
    return values


def _normalize_kind(kind: str | None) -> str | None:
    if kind is None:
        return None
    value = kind.lower()
    aliases = {
        "apis": "api",
        "types": "type",
        "enums": "enum",
        "flags": "flag",
        "interfaces": "interface",
    }
    return aliases.get(value, value)


def split_api_spec(spec: str) -> tuple[str | None, str]:
    text = spec.strip()
    if "!" in text:
        module, name = text.split("!", 1)
        return module.strip(), name.strip()
    if "." in text and not text.lower().endswith(".dll"):
        module, name = text.split(".", 1)
        return module.strip(), name.strip()
    return None, text


def module_aliases(module: str) -> list[str]:
    base = module.strip()
    aliases = [base]
    if base.lower().endswith(".dll"):
        aliases.append(base[:-4])
    else:
        aliases.append(f"{base}.dll")
    return aliases
