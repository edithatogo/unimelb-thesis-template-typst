#!/usr/bin/env python3
"""Opt-in, Linux network-isolated replay of one declared Typst input closure.

This is a local replay lock, not a release bundle or a complete environment image.
External commands use the existing canonical 60-second process-group runner.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import socket
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.native_evidence import strict_json, validate_dependencies
from scripts.package_template import RUNTIME_PATHS

MAX_FILES = 5000
MAX_BYTES = 64 * 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}")
PRODUCER_PATHS = (
    "scripts/replay_build.py", "scripts/native_evidence.py",
    "scripts/package_template.py", "scripts/verify.py",
)
TOOL_ARGUMENTS = {
    "typst": ["--version"], "qpdf": ["--version"],
    "pdftotext": ["-v"], "pdffonts": ["-v"], "unshare": ["--version"],
}
ISOLATION_BACKENDS = ("user-network", "privileged-network")
PRIVILEGED_ARGUMENTS = {"sudo": ["--version"], "setpriv": ["--version"]}
RECIPE_KEYS = {
    "schema_version", "id", "entrypoint", "creation_timestamp", "cli_inputs",
    "required_native_inputs", "fonts", "font_licenses", "expected_pdf_fonts",
    "expected_text", "scope",
}
LOCK_KEYS = {
    "schema_version", "artifact_kind", "recipe", "source", "tools", "environment",
    "producer_sha256", "project_files", "package_files", "font_files", "packages",
    "font_sources", "observed_inputs", "expected_pdf_sha256", "scope",
}


class ReplayError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.details = code, details


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_name(value):
    if (type(value) is not str or not value or "\\" in value or "\x00" in value
            or PurePosixPath(value).is_absolute()
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ReplayError("unsafe-path", "Expected a normalized relative input path")
    return value


def source_path(root, name):
    path = Path(root)
    for part in PurePosixPath(safe_name(name)).parts:
        path /= part
        if path.is_symlink():
            raise ReplayError("symlink-input", "Locked inputs cannot follow symlinks: " + name)
    if not path.is_file():
        raise ReplayError("missing-input", "Declared input is missing: " + name)
    return path


def identity(path):
    path = Path(path)
    return {"sha256": digest(path), "bytes": path.stat().st_size}


def inventory(root, *, ignore=()):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ReplayError("missing-input", "Expected an ordinary input directory")
    result, pending, total = {}, [root], 0
    while pending:
        for path in sorted(pending.pop().iterdir()):
            if path.parent == root and path.name in ignore:
                continue
            if path.is_symlink():
                raise ReplayError("symlink-input", "An input inventory cannot contain symlinks")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                result[path.relative_to(root).as_posix()] = identity(path)
                total += path.stat().st_size
                if len(result) > MAX_FILES or total > MAX_BYTES:
                    raise ReplayError("input-limit", "Input inventory exceeds the bounded replay limit")
            else:
                raise ReplayError("invalid-input", "Only ordinary files belong in a replay inventory")
    return dict(sorted(result.items()))


def validate_inventory(value, *, allow_empty=False):
    if type(value) is not dict or (not value and not allow_empty) or len(value) > MAX_FILES:
        raise ReplayError("invalid-lock", "A nonempty bounded file inventory is required")
    total = 0
    for name, entry in value.items():
        safe_name(name)
        if (type(entry) is not dict or set(entry) != {"sha256", "bytes"}
                or type(entry["sha256"]) is not str or not HEX.fullmatch(entry["sha256"])
                or type(entry["bytes"]) is not int or entry["bytes"] < 0):
            raise ReplayError("invalid-lock", "File identities require a SHA-256 and integer byte count")
        total += entry["bytes"]
    if total > MAX_BYTES:
        raise ReplayError("input-limit", "Declared input inventory exceeds the byte limit")


def check_inventory(root, expected, *, ignore=()):
    validate_inventory(expected, allow_empty=True)
    observed = inventory(root, ignore=ignore)
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    changed = sorted(name for name in set(expected) & set(observed) if expected[name] != observed[name])
    if missing or extra or changed:
        raise ReplayError("input-mismatch", "Locked input inventory differs; restore the declared files",
                          {"missing": missing, "unexpected": extra, "changed": changed})
    return observed


def copy_inputs(source, target, files):
    validate_inventory(files, allow_empty=True)
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    for name, expected in sorted(files.items()):
        src = source_path(source, name)
        if identity(src) != expected:
            raise ReplayError("input-mismatch", "Input changed before copying: " + name)
        dst = target / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        dst.chmod(0o444)
        if identity(dst) != expected or identity(src) != expected:
            raise ReplayError("input-mismatch", "Input changed while copying: " + name)
    check_inventory(target, files)


def validate_recipe(value):
    if type(value) is not dict or set(value) != RECIPE_KEYS or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ReplayError("invalid-recipe", "Expected the exact version-1 replay recipe fields")
    for key in ("id", "scope"):
        if type(value[key]) is not str or not value[key].strip():
            raise ReplayError("invalid-recipe", "Recipe identity and scope must be nonempty")
    safe_name(value["entrypoint"])
    if (type(value["creation_timestamp"]) is not int or not 0 <= value["creation_timestamp"] <= 2**31 - 1
            or type(value["cli_inputs"]) is not dict
            or any(type(k) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]*", k)
                   or type(v) is not str for k, v in value["cli_inputs"].items())):
        raise ReplayError("invalid-recipe", "Recipe time and CLI inputs have invalid types")
    for key in ("required_native_inputs", "fonts", "font_licenses", "expected_pdf_fonts", "expected_text"):
        items = value[key]
        if (type(items) is not list or not items or len(items) > 100
                or any(type(x) is not str or not x.strip() for x in items) or len(set(items)) != len(items)):
            raise ReplayError("invalid-recipe", "Recipe lists must be bounded, nonempty and unique")
    for name in value["required_native_inputs"] + value["fonts"] + value["font_licenses"]:
        safe_name(name)
        if name.split("/")[0] == "_replay":
            raise ReplayError("invalid-recipe", "The _replay directory is reserved for fresh outputs")
    if value["entrypoint"] not in value["required_native_inputs"]:
        raise ReplayError("invalid-recipe", "The entrypoint must be a required native input")
    names = [Path(p).name for p in value["fonts"] + value["font_licenses"]]
    if len(set(names)) != len(names):
        raise ReplayError("invalid-recipe", "Selected fonts and licences need distinct filenames")
    return value


def environment(isolation="user-network"):
    return {
        "network_isolation_backend": isolation,
        "platform": sys.platform, "machine": platform.machine(), "kernel": platform.release(),
        "libc": list(platform.libc_ver()), "python": sys.version.split()[0],
        "python_executable_sha256": digest(Path(sys.executable).resolve()),
        "schema_validator_version": package_version("jsonschema"),
        "compiler_locale": "C.UTF-8", "compiler_timezone": "UTC", "compiler_jobs": 1,
        "system_fonts_disabled": True, "embedded_fonts_disabled": True,
        "dynamic_libraries_locked": False, "container_image": None,
    }


def producer_identity():
    return {name: digest(ROOT / name) for name in PRODUCER_PATHS}


def resolve_tools(compiler=None, expected=None, *, isolation="user-network"):
    if isolation not in ISOLATION_BACKENDS:
        raise ReplayError("unsupported-isolation", "Select an explicit supported namespace backend")
    paths = {}
    names = (*TOOL_ARGUMENTS, *PRIVILEGED_ARGUMENTS) if isolation == "privileged-network" else TOOL_ARGUMENTS
    for name in names:
        system_setup = isolation == "privileged-network" and name in ("unshare", "sudo", "setpriv")
        found = ("/usr/bin/" + name if system_setup else
                 str(compiler) if name == "typst" and compiler else shutil.which(name))
        if not found:
            code = "network-isolation-unavailable" if name == "unshare" else "missing-tool"
            raise ReplayError(code, "Required executable is unavailable: " + name)
        path = Path(found).resolve()
        if not path.is_file():
            code = "network-isolation-unavailable" if system_setup else "missing-tool"
            raise ReplayError(code, "Required executable is absent: " + name)
        if system_setup and (path.parent != Path("/usr/bin") or path.stat().st_uid != 0
                             or path.stat().st_mode & 0o022):
            raise ReplayError("unsafe-namespace-tool", "Privileged setup requires root-owned, non-writable system tools")
        if expected is not None and digest(path) != expected[name]["sha256"]:
            raise ReplayError("tool-mismatch", "Executable bytes differ from the lock: " + name)
        paths[name] = path
    return paths


class Runner:
    """An independent instance of the unchanged canonical process runner."""
    def __init__(self, project):
        spec = importlib.util.spec_from_file_location("replay_canonical_runner", ROOT / "scripts/verify.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.project = Path(project).resolve()
        self.output = self.project / "_replay"
        self.output.mkdir(parents=True, exist_ok=True)
        self.module.ROOT, self.module.OUTPUT = self.project, self.output

    def run(self, argv, name, records, **kwargs):
        return self.module.run([str(x) for x in argv], name, records, **kwargs)


def tool_inventory(paths, runner, records):
    result = {}
    for name, path in paths.items():
        before = digest(path)
        arguments = TOOL_ARGUMENTS[name] if name in TOOL_ARGUMENTS else PRIVILEGED_ARGUMENTS[name]
        output = runner.run([path, *arguments], name + "-version.log", records, combined=True).strip()
        if not output:
            raise ReplayError("missing-tool-version", "Executable reported no version: " + name)
        if digest(path) != before:
            raise ReplayError("tool-mismatch", "Executable changed during version capture: " + name)
        result[name] = {"sha256": before, "version": output.splitlines()[0]}
    return result


@contextmanager
def network_control():
    if sys.platform != "linux" or not Path("/proc/self/ns/net").exists():
        raise ReplayError("network-isolation-unavailable", "This replay backend requires Linux network namespaces")
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(4)
        server.settimeout(2)
        with socket.create_connection(server.getsockname(), timeout=2):
            accepted, _ = server.accept()
            accepted.close()
        yield {"parent_namespace": os.readlink("/proc/self/ns/net"),
               "loopback_port": server.getsockname()[1], "parent_connection_succeeded": True}


def check_privilege_drop(isolation, observed):
    """Require the host user, no retained groups/capabilities and no privilege gains."""
    if (type(isolation.get("uid")) is not int or isolation["uid"] <= 0
            or type(isolation.get("gid")) is not int or isolation["gid"] <= 0
            or observed.get("uid") != [isolation["uid"]] * 4
            or observed.get("gid") != [isolation["gid"]] * 4
            or observed.get("groups") != []
            or observed.get("capabilities") != {"CapEff": 0, "CapPrm": 0, "CapAmb": 0}
            or observed.get("no_new_privs") != 1):
        raise ReplayError("privileges-not-dropped", "Project code must run as the original non-root user without privileges")


def privilege_observation():
    rows = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    return {"uid": [int(v) for v in rows["Uid"].split()],
            "gid": [int(v) for v in rows["Gid"].split()],
            "groups": [int(v) for v in rows["Groups"].split()],
            "capabilities": {key: int(rows[key], 16) for key in ("CapEff", "CapPrm", "CapAmb")},
            "no_new_privs": int(rows["NoNewPrivs"])}


def namespace_command(tools, spec_path):
    """Elevated setup, when explicitly selected, ends before the Python worker starts."""
    worker_command = [sys.executable, "-I", Path(__file__).resolve(), "_worker", str(spec_path)]
    if "sudo" not in tools:
        return [tools["unshare"], "--user", "--map-root-user", "--net", *worker_command], {"backend": "user-network"}
    uid, gid = os.getuid(), os.getgid()
    if uid <= 0 or gid <= 0 or os.geteuid() != uid or os.getegid() != gid:
        raise ReplayError("privileges-not-dropped", "Privileged namespace setup requires an ordinary non-root caller")
    command = [tools["sudo"], "--non-interactive", "--", tools["unshare"], "--net",
               "--setgid", str(gid), "--setuid", str(uid), "--", tools["setpriv"],
               "--no-new-privs", "--", *worker_command]
    return command, {"backend": "privileged-network", "uid": uid, "gid": gid}


def check_process_control(observed, supervisor):
    if (type(observed) is not dict or observed.get("supervisor_pid") != supervisor
            or any(type(observed.get(key)) is not int or observed[key] <= 0
                   for key in ("supervisor_pid", "launcher_pid", "process_group", "session"))
            or observed["launcher_pid"] != observed["process_group"]
            or observed["launcher_pid"] != observed["session"]):
        raise ReplayError("process-control-unproven", "The compiler must remain in the canonical watchdog's process group")


def process_control(supervisor):
    """Find the actual launcher ancestor and bind the worker to its session/group."""
    current = os.getpid()
    for _ in range(32):
        fields = Path(f"/proc/{current}/stat").read_text().rpartition(") ")[2].split()
        parent = int(fields[1])
        if parent == supervisor:
            observed = {"supervisor_pid": supervisor, "launcher_pid": current,
                        "process_group": os.getpgrp(), "session": os.getsid(0)}
            check_process_control(observed, supervisor)
            return observed
        if parent <= 1:
            break
        current = parent
    raise ReplayError("process-control-unproven", "The worker cannot identify its canonical launcher ancestor")


def worker(spec_path):
    """Probe the new namespace, then replace this process with the exact compiler."""
    spec = strict_json(Path(spec_path).read_text(encoding="utf-8"))
    isolation = spec.get("isolation", {"backend": "user-network"})
    if isolation.get("backend") not in ISOLATION_BACKENDS:
        raise ReplayError("unsupported-isolation", "Unknown namespace worker backend")
    privileges = None
    if isolation["backend"] == "privileged-network":
        privileges = privilege_observation()
        check_privilege_drop(isolation, privileges)
    supervisor = spec.get("supervisor_pid")
    process = process_control(supervisor) if supervisor is not None else None
    if isolation["backend"] == "privileged-network":
        check_process_control(process, supervisor)
    if spec["network"].get("parent_connection_succeeded") is not True:
        raise ReplayError("network-not-isolated", "The parent must establish a working network control before isolation")
    observed = os.readlink("/proc/self/ns/net")
    interface_text = Path("/proc/net/dev").read_text(encoding="utf-8")
    interfaces = sorted(re.findall(r"^\s*([^\s:]+):", interface_text, re.MULTILINE))
    if observed == spec["network"]["parent_namespace"] or interfaces != ["lo"]:
        raise ReplayError("network-not-isolated", "A new network namespace without external interfaces is required")
    try:
        with socket.create_connection(("127.0.0.1", spec["network"]["loopback_port"]), timeout=2):
            raise ReplayError("network-not-isolated", "The isolated process reached the parent's positive-control listener")
    except OSError as exc:
        failure = {"type": type(exc).__name__, "errno": exc.errno}
    proof = {**spec["network"], "child_namespace": observed, "interfaces": interfaces,
             "isolation": isolation, "privilege_observation": privileges,
             "process_control": process,
             "interface_inventory_source": "/proc/net/dev",
             "interface_inventory_sha256": hashlib.sha256(interface_text.encode()).hexdigest(),
             "child_connection_failed": True, "connection_error": failure,
             "compiler_argv": spec["compiler_argv"], "compiler_environment": spec["compiler_environment"]}
    Path(spec["network_report"]).write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    os.execve(spec["compiler_argv"][0], spec["compiler_argv"], spec["compiler_environment"])


def inspect_pdf(pdf, recipe, tools, runner, records):
    if not pdf.is_file() or not pdf.stat().st_size:
        raise ReplayError("missing-output", "The compiler produced no fresh PDF")
    runner.run([tools["qpdf"], "--check", pdf], "qpdf.log", records)
    text = runner.run([tools["pdftotext"], "-layout", pdf, "-"], "text.log", records)
    if any(expected not in " ".join(text.split()) for expected in recipe["expected_text"]):
        raise ReplayError("unexpected-text", "The actual PDF omits a required synthetic sentinel")
    raw_fonts = runner.run([tools["pdffonts"], pdf], "fonts.log", records)
    fonts = []
    for line in raw_fonts.splitlines()[2:]:
        fields = line.split()
        if len(fields) < 8:
            raise ReplayError("invalid-font-observation", "Malformed native PDF font row")
        name = fields[0].split("+")[-1].removesuffix("-Identity-H")
        fonts.append({"name": name, "embedded": fields[-5], "subset": fields[-4], "unicode_map": fields[-3]})
    if (not fonts or {f["name"] for f in fonts} != set(recipe["expected_pdf_fonts"])
            or any(f["embedded"] != "yes" for f in fonts)):
        raise ReplayError("unexpected-font", "Actual PDF fonts differ from the declared embedded-font set")
    return {"pdf": identity(pdf), "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "fonts": fonts}


def _compile_fresh(project, cache, fonts, recipe, tools, records):
    project, cache, fonts = (Path(x).resolve() for x in (project, cache, fonts))
    runner = Runner(project)
    output = runner.output
    pdf, dependencies = output / "document.pdf", output / "dependencies.json"
    for path in (pdf, dependencies, output / "network.json"):
        if path.exists():
            raise ReplayError("stale-output", "A replay compile must start without prior output")
    local = output / "local-packages"
    local.mkdir()
    argv = [str(tools["typst"]), "compile", "--root", str(project),
            "--package-cache-path", str(cache), "--package-path", str(local),
            "--ignore-system-fonts", "--ignore-embedded-fonts", "--font-path", str(fonts),
            "--creation-timestamp", str(recipe["creation_timestamp"]), "--jobs", "1"]
    for key, value in sorted(recipe["cli_inputs"].items()):
        argv.extend(["--input", key + "=" + value])
    argv.extend(["--deps", str(dependencies), "--deps-format", "json",
                 str(project / recipe["entrypoint"]), str(pdf)])
    compiler_env = {"TZ": "UTC", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                    "SOURCE_DATE_EPOCH": str(recipe["creation_timestamp"])}
    with network_control() as control:
        spec_path = output / "invocation.json"
        launcher, isolation = namespace_command(tools, spec_path)
        spec = {"network": control, "compiler_argv": argv, "compiler_environment": compiler_env,
                "network_report": str(output / "network.json"), "isolation": isolation,
                "supervisor_pid": os.getpid()}
        spec_path.write_text(json.dumps(spec, indent=2) + "\n")
        try:
            runner.run(launcher, "compile.log", records, combined=True)
        except Exception as exc:
            log = (output / "compile.log").read_text(errors="replace")
            if not (output / "network.json").exists() and re.search(r"(?m)^(?:unshare|sudo|setpriv):", log):
                raise ReplayError("network-isolation-unavailable", "The host rejected the required namespace backend") from exc
            raise
    proof = strict_json((output / "network.json").read_text())
    if (proof["compiler_argv"] != argv or proof["compiler_environment"] != compiler_env
            or proof["parent_namespace"] == proof["child_namespace"]
            or proof["parent_connection_succeeded"] is not True or proof["child_connection_failed"] is not True
            or proof["interfaces"] != ["lo"] or proof.get("isolation") != isolation):
        raise ReplayError("network-not-isolated", "The executed compiler lacks a valid isolation receipt")
    if isolation["backend"] == "privileged-network":
        check_privilege_drop(isolation, proof.get("privilege_observation", {}))
    check_process_control(proof.get("process_control"), os.getpid())
    # The trusted worker probes the namespace and uses execve, keeping the same
    # PID/process group; its final status/log is the compiler's status/log.
    inner = {**records[0], "command": argv, "outer_invocation": records[0]["command"],
             "execution_binding": "namespace-worker-execve", "environment_overrides": compiler_env}
    details = {"source": recipe["entrypoint"], "pdf": str(pdf.relative_to(project)),
               "source_sha256": digest(project / recipe["entrypoint"]), "pdf_sha256": digest(pdf)}
    raw = dependencies.read_text(encoding="utf-8")
    native = validate_dependencies(raw, root=project, details=details, commands=[inner],
                                   approved_external_roots={"package-cache": cache},
                                   required_inputs=recipe["required_native_inputs"])
    checked = inspect_pdf(pdf, recipe, tools, runner, records)
    result = {"result": "pass", "commands": records, "compiler_execution": inner,
              "network": proof, "native_inventory": native, **checked,
              "output": str(pdf), "compiler_environment_is_minimal": True}
    return result


def compile_isolated(project, cache, fonts, recipe, tools):
    destination = Path(project).resolve() / "_replay" / "compile-receipt.json"
    if destination.exists() or destination.is_symlink():
        raise ReplayError("stale-output", "A compile cannot reuse a previous receipt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "artifact_kind": "isolated-typst-compile", "result": "fail",
               "commands": [], "started_at_utc": datetime.now(timezone.utc).isoformat()}
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        receipt.update(_compile_fresh(project, cache, fonts, recipe, tools, receipt["commands"]))
        return receipt
    except Exception as exc:
        receipt.update({"error": str(exc), "code": getattr(exc, "code", type(exc).__name__)})
        raise
    finally:
        receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def package_records(cache, observed, cache_files):
    roots = set()
    for value in observed:
        if value.startswith("package-cache:"):
            name = value.partition(":")[2]
            safe_name(name)
            parts = name.split("/")
            if len(parts) < 4 or parts[0] != "preview" or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", parts[2]):
                raise ReplayError("unsupported-package", "Only observed preview package/version roots are supported")
            roots.add("/".join(parts[:3]))
    files, packages = {}, []
    for prefix in sorted(roots):
        selected = {name: entry for name, entry in cache_files.items() if name.startswith(prefix + "/")}
        manifest = tomllib.loads(source_path(cache, prefix + "/typst.toml").read_text())
        name, version = prefix.split("/")[1:]
        package = manifest.get("package", {})
        licenses = [p for p in selected if re.match(r"^(license|copying|notice)", Path(p).name, re.I)]
        if (package.get("name") != name or package.get("version") != version
                or type(package.get("license")) is not str or not package["license"].strip() or not licenses):
            raise ReplayError("missing-package-identity", "Observed packages need matching metadata and retained licence files")
        files.update(selected)
        packages.append({"root": prefix, "name": name, "version": version, "license": package["license"],
                         "license_files": sorted(licenses),
                         "content_inventory_sha256": hashlib.sha256(canonical(selected)).hexdigest()})
    return dict(sorted(files.items())), packages


def observed_identities(result):
    return {entry["path"]: entry["sha256_observed_after_compile"] for entry in result["native_inventory"]["inputs"]}


def require_observed(observed, project, packages):
    for name, sha in observed.items():
        if type(name) is not str or type(sha) is not str or not HEX.fullmatch(sha):
            raise ReplayError("invalid-lock", "Native input identities must be named SHA-256 values")
        label, _, relative = name.partition(":")
        values = project if label == "project" else packages if label == "package-cache" else {}
        if relative not in values or values[relative]["sha256"] != sha:
            raise ReplayError("undeclared-dependency", "Native input is absent from or differs from the lock: " + name)


def validate_lock(value):
    if (type(value) is not dict or set(value) != LOCK_KEYS or type(value["schema_version"]) is not int
            or value["schema_version"] != 1 or value["artifact_kind"] != "bounded-typst-replay-lock"):
        raise ReplayError("invalid-lock", "Expected the exact version-1 replay lock fields")
    validate_recipe(value["recipe"])
    for key in ("project_files", "font_files", "package_files"):
        validate_inventory(value[key], allow_empty=key == "package_files")
    if any(name.split("/")[0] == "_replay" for name in value["project_files"]):
        raise ReplayError("invalid-lock", "Fresh output paths cannot be locked source inputs")
    isolation = value.get("environment", {}).get("network_isolation_backend") if type(value.get("environment")) is dict else None
    if isolation not in ISOLATION_BACKENDS:
        raise ReplayError("invalid-lock", "The lock must declare its exact namespace backend")
    expected_tools = set(TOOL_ARGUMENTS) | (set(PRIVILEGED_ARGUMENTS) if isolation == "privileged-network" else set())
    if (type(value["tools"]) is not dict or set(value["tools"]) != expected_tools
            or any(type(v) is not dict or set(v) != {"sha256", "version"}
                   or type(v["sha256"]) is not str or not HEX.fullmatch(v["sha256"])
                   or type(v["version"]) is not str or not v["version"] for v in value["tools"].values())):
        raise ReplayError("invalid-lock", "Exact executable digests and versions are required")
    if (type(value["producer_sha256"]) is not dict or set(value["producer_sha256"]) != set(PRODUCER_PATHS)
            or any(type(v) is not str or not HEX.fullmatch(v) for v in value["producer_sha256"].values())
            or type(value["expected_pdf_sha256"]) is not str or not HEX.fullmatch(value["expected_pdf_sha256"])):
        raise ReplayError("invalid-lock", "Producer and PDF identities are malformed")
    if type(value["environment"]) is not dict or type(value["source"]) is not dict or type(value["scope"]) is not str or not value["scope"].strip():
        raise ReplayError("invalid-lock", "Environment/source observations and scope are required")
    shape = environment()
    if (set(value["environment"]) != set(shape)
            or any(type(v) is not type(shape[k]) for k, v in value["environment"].items())
            or len(value["environment"]["libc"]) != 2
            or any(type(v) is not str for v in value["environment"]["libc"])):
        raise ReplayError("invalid-lock", "Environment observations must retain their declared types")
    if (set(value["source"]) != {"git_revision", "git_tree", "git_dirty"}
            or any(v is not None and (type(v) is not str or not re.fullmatch(r"[0-9a-f]{40}", v))
                   for k, v in value["source"].items() if k != "git_dirty")
            or value["source"]["git_dirty"] is not None and type(value["source"]["git_dirty"]) is not bool):
        raise ReplayError("invalid-lock", "Git observations must retain their actual types and identities")
    if type(value["observed_inputs"]) is not dict or not value["observed_inputs"]:
        raise ReplayError("invalid-lock", "The lock must retain successful native input identities")
    require_observed(value["observed_inputs"], value["project_files"], value["package_files"])
    if (not set(value["recipe"]["required_native_inputs"]).issubset(value["project_files"])
            or not {"project:" + p for p in value["recipe"]["required_native_inputs"]}.issubset(value["observed_inputs"])):
        raise ReplayError("invalid-lock", "A required source is missing from the declared or observed closure")
    if (type(value["packages"]) is not list or type(value["font_sources"]) is not list
            or not value["font_sources"]):
        raise ReplayError("invalid-lock", "Package and font/licence inventories are required")
    font_keys = {"source", "filename", "role", "sha256", "bytes"}
    names, sources = set(), set()
    for item in value["font_sources"]:
        if type(item) is not dict or set(item) != font_keys:
            raise ReplayError("invalid-lock", "Malformed font/licence source record")
        safe_name(item["source"])
        filename = Path(item["source"]).name
        expected_role = "font" if item["source"] in value["recipe"]["fonts"] else "license"
        if (item["filename"] != filename or filename in names or item["source"] in sources
                or item["role"] != expected_role
                or type(item["bytes"]) is not int
                or {"sha256": item["sha256"], "bytes": item["bytes"]} != value["font_files"].get(filename)):
            raise ReplayError("invalid-lock", "Font source records disagree with the locked files")
        names.add(filename)
        sources.add(item["source"])
    if names != set(value["font_files"]) or sources != set(value["recipe"]["fonts"] + value["recipe"]["font_licenses"]):
        raise ReplayError("invalid-lock", "Font/licence source inventory is incomplete")
    roots = set()
    for package in value["packages"]:
        if (type(package) is not dict or set(package) != {"root", "name", "version", "license", "license_files", "content_inventory_sha256"}
                or any(type(package[k]) is not str or not package[k] for k in ("root", "name", "version", "license", "content_inventory_sha256"))
                or not re.fullmatch(r"[a-z][a-z0-9-]*", package["name"])
                or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", package["version"])
                or package["root"] != "preview/" + package["name"] + "/" + package["version"]
                or package["root"] in roots or type(package["license_files"]) is not list or not package["license_files"]):
            raise ReplayError("invalid-lock", "Malformed or duplicate complete-package identity")
        selected = {name: entry for name, entry in value["package_files"].items() if name.startswith(package["root"] + "/")}
        if (any(type(p) is not str or p not in selected for p in package["license_files"])
                or package["content_inventory_sha256"] != hashlib.sha256(canonical(selected)).hexdigest()):
            raise ReplayError("invalid-lock", "Complete package inventory differs from its record")
        roots.add(package["root"])
    if any(not any(name.startswith(prefix + "/") for prefix in roots) for name in value["package_files"]):
        raise ReplayError("invalid-lock", "A package file has no complete-package record")
    return value


def write_report(output, report):
    (Path(output) / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def new_output(path):
    path = Path(path).absolute()
    if path.exists() or path.is_symlink() or path.resolve() != path:
        raise ReplayError("unsafe-output", "Choose a new output directory with no symlink components")
    path.mkdir(parents=True, exist_ok=False)
    return path


def source_identity(root):
    observed = {"git_revision": None, "git_tree": None, "git_dirty": None}
    if (Path(root) / ".git").exists():
        for key, args in (("git_revision", ["rev-parse", "HEAD"]), ("git_tree", ["rev-parse", "HEAD^{tree}"]),
                          ("git_dirty", ["status", "--porcelain"])):
            result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=5, check=True)
            observed[key] = bool(result.stdout.strip()) if key == "git_dirty" else result.stdout.strip()
    return observed


def make_lock(root, recipe_path, cache, output, compiler=None, *, isolation="user-network"):
    root, cache = Path(root).resolve(), Path(cache).resolve()
    output = new_output(output)
    report = {"schema_version": 1, "result": "fail", "artifact_kind": "replay-lock-capture",
              "tool_commands": [], "started_at_utc": datetime.now(timezone.utc).isoformat()}
    write_report(output, report)
    try:
        producer_before = producer_identity()
        report["producer_sha256"] = producer_before
        recipe_path = Path(recipe_path)
        recipe_path = recipe_path if recipe_path.is_absolute() else root / recipe_path
        relative_recipe = recipe_path.resolve().relative_to(root).as_posix()
        recipe_bytes = source_path(root, relative_recipe).read_bytes()
        recipe = validate_recipe(strict_json(recipe_bytes.decode("utf-8")))
        recipe_identity = {"sha256": hashlib.sha256(recipe_bytes).hexdigest(), "bytes": len(recipe_bytes)}
        report["recipe_sha256"] = recipe_identity["sha256"]
        names = sorted(set((*RUNTIME_PATHS, *recipe["required_native_inputs"], relative_recipe, "typst.toml", "LICENSE")))
        project_files = {name: identity(source_path(root, name)) for name in names}
        if project_files[relative_recipe] != recipe_identity:
            raise ReplayError("input-mismatch", "Recipe changed after its parsed snapshot; restart capture")
        font_sources = [{"source": name, "filename": Path(name).name,
                         "role": "font" if name in recipe["fonts"] else "license",
                         **identity(source_path(root, name))} for name in recipe["fonts"] + recipe["font_licenses"]]
        fonts = output / "fonts"
        fonts.mkdir()
        for item in sorted(font_sources, key=lambda x: x["filename"]):
            shutil.copyfile(source_path(root, item["source"]), fonts / item["filename"])
        font_files = inventory(fonts)
        cache_before = inventory(cache)
        discovery = output / "discovery" / "project"
        copy_inputs(root, discovery, project_files)
        tools = resolve_tools(compiler, isolation=isolation)
        tool_runner, tool_commands = Runner(discovery), report["tool_commands"]
        locked_tools = tool_inventory(tools, tool_runner, tool_commands)
        manifest = tomllib.loads(source_path(root, "typst.toml").read_text())
        if locked_tools["typst"]["version"].split()[:2] != ["typst", manifest["tool"]["typst"]["version"]]:
            raise ReplayError("compiler-version-mismatch", "The compiler differs from typst.toml's exact version")
        report["tool_commands"] = tool_commands
        result = compile_isolated(discovery, cache, fonts, recipe, tools)
        report["discovery"] = result
        check_inventory(discovery, project_files, ignore=("_replay",))
        check_inventory(cache, cache_before)
        check_inventory(fonts, font_files)
        resolve_tools(compiler, locked_tools, isolation=isolation)
        if producer_identity() != producer_before:
            raise ReplayError("producer-mismatch", "Producer source changed during lock capture")
        for name, expected in project_files.items():
            if identity(source_path(root, name)) != expected:
                raise ReplayError("input-mismatch", "Original source changed during capture: " + name)
        for item in font_sources:
            if identity(source_path(root, item["source"])) != {"sha256": item["sha256"], "bytes": item["bytes"]}:
                raise ReplayError("input-mismatch", "Original font/licence changed during capture")
        observed = observed_identities(result)
        package_files, packages = package_records(cache, observed, cache_before)
        require_observed(observed, project_files, package_files)
        copy_inputs(discovery, output / "project", project_files)
        copy_inputs(cache, output / "packages", package_files)
        lock = {"schema_version": 1, "artifact_kind": "bounded-typst-replay-lock", "recipe": recipe,
                "source": source_identity(root), "tools": locked_tools, "environment": environment(isolation),
                "producer_sha256": producer_before, "project_files": project_files,
                "package_files": package_files, "font_files": font_files, "packages": packages,
                "font_sources": font_sources, "observed_inputs": observed,
                "expected_pdf_sha256": result["pdf"]["sha256"],
                "scope": "One declared source closure in the observed Linux/tool environment; no release or whole-environment claim"}
        validate_lock(lock)
        (output / "lock.json").write_bytes(canonical(lock) + b"\n")
        report.update({"result": "pass", "lock_sha256": digest(output / "lock.json"),
                       "project_file_count": len(project_files), "package_count": len(packages),
                       "package_file_count": len(package_files), "font_file_count": len(recipe["fonts"]),
                       "network_disabled_discovery": True, "two_build_replay_qualified": False})
        return report
    except Exception as exc:
        report.update({"error": str(exc), "code": getattr(exc, "code", type(exc).__name__)})
        if report["code"] == "network-isolation-unavailable":
            report["result"] = "unsupported"
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_report(output, report)


def compare_pdfs(first, second, expected):
    a, b = Path(first).read_bytes(), Path(second).read_bytes()
    result = {"first_sha256": hashlib.sha256(a).hexdigest(), "second_sha256": hashlib.sha256(b).hexdigest(),
              "first_bytes": len(a), "second_bytes": len(b), "bytes_equal": a == b}
    if not a or a != b:
        result["first_difference_offset"] = next((i for i, pair in enumerate(zip(a, b)) if pair[0] != pair[1]), min(len(a), len(b)))
        raise ReplayError("byte-mismatch", "Independent PDF bytes differ; equal text cannot qualify replay", result)
    if result["first_sha256"] != expected:
        raise ReplayError("expected-artifact-mismatch", "Equal builds differ from the locked PDF identity", result)
    return result


def replay(bundle, expected_digest, output, compiler=None, *, isolation="user-network"):
    output = new_output(output)
    report = {"schema_version": 1, "result": "fail", "artifact_kind": "bounded-two-build-replay", "builds": [],
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "byte_replay_qualified": False}
    write_report(output, report)
    try:
        bundle = Path(bundle).resolve()
        if type(expected_digest) is not str or not HEX.fullmatch(expected_digest):
            raise ReplayError("lock-mismatch", "The lock differs from the caller's trusted SHA-256")
        lock_bytes = source_path(bundle, "lock.json").read_bytes()
        if hashlib.sha256(lock_bytes).hexdigest() != expected_digest:
            raise ReplayError("lock-mismatch", "The lock differs from the caller's trusted SHA-256")
        lock = validate_lock(strict_json(lock_bytes.decode("utf-8")))
        report.update({"lock_sha256": expected_digest, "source": lock["source"],
                       "producer_sha256": lock["producer_sha256"], "environment": lock["environment"]})
        if lock["producer_sha256"] != producer_identity():
            raise ReplayError("producer-mismatch", "Replay validation/runner source differs from the locked producer")
        if lock["environment"].get("network_isolation_backend") != isolation:
            raise ReplayError("isolation-mismatch", "Explicitly select the same namespace backend as the trusted lock")
        if lock["environment"] != environment(isolation):
            raise ReplayError("environment-mismatch", "Observed OS/runtime differs from the locked replay scope")
        tools = resolve_tools(compiler, lock["tools"], isolation=isolation)
        for folder, key in (("project", "project_files"), ("packages", "package_files"), ("fonts", "font_files")):
            check_inventory(bundle / folder, lock[key])
        actual_package_files, actual_packages = package_records(bundle / "packages", lock["observed_inputs"], lock["package_files"])
        if actual_package_files != lock["package_files"] or actual_packages != lock["packages"]:
            raise ReplayError("invalid-lock", "Package metadata/licences disagree with their actual manifests")
        for name in ("first", "relocated-second"):
            area = output / name
            area.mkdir()
            for folder, key in (("project", "project_files"), ("packages", "package_files"), ("fonts", "font_files")):
                copy_inputs(bundle / folder, area / folder, lock[key])
            result = compile_isolated(area / "project", area / "packages", area / "fonts", lock["recipe"], tools)
            report["builds"].append(result)
            check_inventory(area / "project", lock["project_files"], ignore=("_replay",))
            check_inventory(area / "packages", lock["package_files"])
            check_inventory(area / "fonts", lock["font_files"])
            resolve_tools(compiler, lock["tools"], isolation=isolation)
            if producer_identity() != lock["producer_sha256"]:
                raise ReplayError("producer-mismatch", "Producer source changed during replay")
            observed = observed_identities(result)
            require_observed(observed, lock["project_files"], lock["package_files"])
            if observed != lock["observed_inputs"]:
                raise ReplayError("dependency-set-mismatch", "The relocated native input closure differs from the lock")
            write_report(output, report)
        for folder, key in (("project", "project_files"), ("packages", "package_files"), ("fonts", "font_files")):
            check_inventory(bundle / folder, lock[key])
        comparison = compare_pdfs(report["builds"][0]["output"], report["builds"][1]["output"], lock["expected_pdf_sha256"])
        report.update({"result": "pass", "lock_sha256": expected_digest, "comparison": comparison,
                       "byte_replay_qualified": True, "network_disabled_builds": 2,
                       "cross_environment_semantic_repeatability_qualified": False,
                       "release_bundle_qualified": False, "complete_environment_image_locked": False})
        return report
    except Exception as exc:
        report.update({"error": str(exc), "code": getattr(exc, "code", type(exc).__name__)})
        if getattr(exc, "details", None) is not None:
            report["diagnostic"] = exc.details
        if report["code"] == "network-isolation-unavailable":
            report["result"] = "unsupported"
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_report(output, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    capture = sub.add_parser("lock")
    capture.add_argument("--root", type=Path, default=ROOT)
    capture.add_argument("--recipe", type=Path, default=Path("replay/synthetic.json"))
    capture.add_argument("--package-cache", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--compiler", type=Path)
    capture.add_argument("--isolation", choices=ISOLATION_BACKENDS, default="user-network")
    check = sub.add_parser("replay")
    check.add_argument("--bundle", type=Path, required=True)
    check.add_argument("--lock-sha256", required=True)
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--compiler", type=Path)
    check.add_argument("--isolation", choices=ISOLATION_BACKENDS, default="user-network")
    child = sub.add_parser("_worker", help=argparse.SUPPRESS)
    child.add_argument("spec", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "_worker":
            worker(args.spec)
        elif args.action == "lock":
            result = make_lock(args.root, args.recipe, args.package_cache, args.output, args.compiler, isolation=args.isolation)
            print(json.dumps({"result": result["result"], "lock_sha256": result["lock_sha256"]}))
        else:
            result = replay(args.bundle, args.lock_sha256, args.output, args.compiler, isolation=args.isolation)
            print(json.dumps({"result": result["result"], "pdf_sha256": result["comparison"]["first_sha256"]}))
        return 0
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        result = "unsupported" if code == "network-isolation-unavailable" else "fail"
        print(json.dumps({"result": result, "code": code, "error": str(exc)}), file=sys.stderr)
        return 2 if result == "unsupported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
