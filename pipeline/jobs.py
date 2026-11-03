"""Parameter-driven asset jobs: incremental stages, shared render queue, compact results.

    python3 -B -m pipeline.jobs check
    python3 -B -m pipeline.jobs validate jobs/<id>.json
    python3 -B -m pipeline.jobs run jobs/<id>.json [--only STAGE ...] [--force]
    python3 -B -m pipeline.jobs batch jobs/a.json jobs/b.json [--workers 2]
    python3 -B -m pipeline.jobs status [JOB_ID ...]
    python3 -B -m pipeline.jobs report [JOB_ID ...]

Stdlib only. Every stage prints one JSON line; full Blender logs stay on disk.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

from .cli import detect_blender

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "outputs/jobs"
LOCKS = ROOT / "outputs/.locks"
PROFILES = json.loads((ROOT / "config/render_profiles.json").read_text())
# ponytail: fixed slot counts per machine; measure before raising GPU_SLOTS above 1 on 16 GB.
GPU_SLOTS = int(os.environ.get("PERHAPS_GPU_SLOTS", "1"))
BLENDER_SLOTS = int(os.environ.get("PERHAPS_BLENDER_SLOTS", "2"))
SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_print_lock = threading.Lock()


def emit(**data):
    with _print_lock:
        print(json.dumps(data, separators=(",", ":")), flush=True)


def path(value):
    return (ROOT / value).resolve()


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else json.dumps(data, sort_keys=True).encode()).hexdigest()


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 23), b""):
            h.update(block)
    return h.hexdigest()


def write_atomic(p, data):
    tmp = p.with_suffix(p.suffix + ".tmp%d" % os.getpid())
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, p)


def load(job_file):
    job = json.loads(Path(job_file).read_text())
    validate(job, inputs_may_be_pending=True)
    return job


def validate(job, inputs_may_be_pending=False):
    def need(ok, message):
        if not ok:
            raise ValueError("%s: %s" % (job.get("id", "?"), message))
    need(SLUG.match(job.get("id", "")), "id must be a lowercase slug")
    need(path(job["output"]) == JOBS / job["id"], "output must be outputs/jobs/<id>")
    source = path(job["input"])
    need(source.suffix == ".blend", "input must be a .blend")
    need(source.is_file() or (inputs_may_be_pending and job.get("depends_on")), "missing input " + job["input"])
    need(JOBS / job["id"] not in source.parents, "input must not live inside the job output")
    for ref in job.get("references", []) + ([job["geometry_lock"]] if job.get("geometry_lock") else []):
        need(path(ref).exists(), "missing " + ref)
    names = [s["name"] for s in job["stages"]]
    need(len(names) == len(set(names)) and all(SLUG.match(n) for n in names), "stage names must be unique slugs")
    for s in job["stages"]:
        if "render" in s:
            r = s["render"]
            need(r.get("profile") in PROFILES, s["name"] + ": unknown profile")
            need(isinstance(r.get("resolution"), int) and isinstance(r.get("camera"), str), s["name"] + ": camera/resolution")
            need(not PROFILES[r["profile"]].get("border_required") or r.get("border"), s["name"] + ": profile needs border")
        else:
            need((ROOT / "pipeline/steps" / (s.get("step", "") + ".py")).is_file(), s["name"] + ": unknown step")


@contextmanager
def slot(kind, count, job, stage):
    LOCKS.mkdir(parents=True, exist_ok=True)
    waited = False
    while True:
        for i in range(count):
            handle = open(LOCKS / ("%s-%d.lock" % (kind, i)), "w")
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                continue
            try:
                yield
            finally:
                handle.close()  # releases flock; the kernel also releases it if this process dies
            return
        if not waited:
            emit(job=job, stage=stage, status="waiting", slot=kind)
            waited = True
        time.sleep(2)


def param_files(stage):
    """Config files a stage depends on: its tier preset, library materials it names, and those a preset names."""
    params = stage.get("params", {})
    files = {params["preset"]} if params.get("preset") else set()
    files |= {v for v in params.values() if isinstance(v, str) and v.startswith(("config/presets/", "config/watches/"))}
    if params.get("material"):
        files.add("config/material_library/%s.json" % params["material"])
    files |= {"config/material_library/%s.json" % m for m in params.get("library_roles", {}).values()}
    if params.get("spec"):  # a watch spec names further inputs (traced dimensions, traced print): editing them must rerun the build
        spec = json.loads(path(params["spec"]).read_text())
        files |= {v for v in spec.values() if isinstance(v, str) and v.startswith("config/watches/")}
    for f in list(files):
        if f.startswith("config/tiers/"):
            roles = json.loads(path(f).read_text()).get("roles", {})
            files |= {"config/material_library/%s.json" % r["library"] for r in roles.values() if "library" in r}
    return sorted(files)


def code_fresh(code):
    return all((ROOT / p).is_file() and file_sha(ROOT / p) == h for p, h in code.items())


def run_blender(task, log_path):
    blender = detect_blender({})
    command = [blender, "--background", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
               "--python", str(ROOT / "pipeline/job_entry.py"), "--", str(task)]
    with open(log_path, "w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        _, status, usage = os.wait4(process.pid, 0)
    rss = usage.ru_maxrss / 1e6 if sys.platform == "darwin" else usage.ru_maxrss / 1e3
    return os.waitstatus_to_exitcode(status), round(rss), Path(log_path).read_text(errors="replace")


def error_tail(text):
    lines = text.splitlines()
    picked = [l for l in lines if re.search(r"Error|Traceback|Exception|raise ", l)][-6:] + lines[-6:]
    return "\n".join(dict.fromkeys(picked))[-1500:]


def run_job(job_file, only=(), force=False):
    job = load(job_file)
    out = JOBS / job["id"]
    (out / "state").mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    guard = open(out / ".job.lock", "w")
    try:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError(job["id"] + " is already running in another process")
    validate(job)
    write_atomic(out / "job.json", job)
    lock = str(path(job["geometry_lock"])) if job.get("geometry_lock") else None
    scene, chain = path(job["input"]), sha({"input_sha256": file_sha(path(job["input"])), "lock": lock})
    last_target = max((i for i, s in enumerate(job["stages"]) if not only or s["name"] in only), default=-1)
    ran, skipped, started = [], [], time.monotonic()
    for index, stage in enumerate(job["stages"][:last_target + 1]):
        is_render = "render" in stage
        if is_render and only and stage["name"] not in only:
            continue
        profile = PROFILES[stage["render"]["profile"]] if is_render else None
        files = {f: file_sha(path(f)) for f in param_files(stage)}
        fp = sha({"stage": stage, "profile": profile, "upstream": chain, **({"files": files} if files else {})})
        state_path = out / "state" / (stage["name"] + ".json")
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        fresh = (state.get("status") == "ok" and state.get("fingerprint") == fp and code_fresh(state.get("code", {}))
                 and all((out / o).exists() for o in state.get("outputs", [])))
        if fresh and not (force and (not only or stage["name"] in only)):
            skipped.append(stage["name"])
            emit(job=job["id"], stage=stage["name"], status="skipped", reason="unchanged")
        else:
            task = out / "state" / (stage["name"] + ".task.json")
            result_path = out / "state" / (stage["name"] + ".result.json")
            result_path.unlink(missing_ok=True)
            write_atomic(task, {"stage": stage, "profile": profile, "input": str(scene), "out_dir": str(out),
                                "geometry_lock": lock, "result": str(result_path)})
            write_atomic(state_path, {"status": "running", "pid": os.getpid(), "fingerprint": fp, "started": time.time()})
            log_path = out / "logs" / (stage["name"] + ".log")
            t0 = time.monotonic()
            gpu = slot("gpu", GPU_SLOTS, job["id"], stage["name"]) if is_render else nullcontext()
            with gpu, slot("blender", BLENDER_SLOTS, job["id"], stage["name"]):
                t1 = time.monotonic()
                code, rss, text = run_blender(task, log_path)
            seconds = round(time.monotonic() - t1, 1)
            result = json.loads(result_path.read_text()) if code == 0 and result_path.exists() else {}
            state = {"status": "ok" if result else "failed", "fingerprint": fp, "exit_code": code,
                     "seconds": seconds, "queued_seconds": round(t1 - t0, 1), "rss_mb": rss,
                     "render_seconds": result.get("render_seconds"), "outputs": result.get("outputs", []),
                     "code": result.get("code", {}), "settings": result.get("settings"),
                     "summary": result.get("summary"), "lock": result.get("lock_after") or result.get("lock_before"),
                     "finished": time.time()}
            write_atomic(state_path, state)
            with open(out / "events.jsonl", "a") as events:
                events.write(json.dumps({"stage": stage["name"], "kind": "render" if is_render else "scene",
                                         **{k: state[k] for k in ("status", "seconds", "queued_seconds", "rss_mb",
                                                                  "render_seconds", "finished")}}) + "\n")
            line = {"job": job["id"], "stage": stage["name"], "status": state["status"], "s": seconds,
                    "rss_mb": rss, "outputs": state["outputs"], "log": str(log_path.relative_to(ROOT))}
            if not result:
                line["error"] = error_tail(text)
                emit(**line)
                emit(job=job["id"], status="failed", ran=ran, skipped=skipped, wall_s=round(time.monotonic() - started, 1))
                return False
            emit(**line)
            ran.append(stage["name"])
        if not is_render:
            scene, chain = out / (stage["name"] + ".blend"), sha({"fp": fp, "code": state["code"]})
    emit(job=job["id"], status="ok", ran=ran, skipped=skipped, wall_s=round(time.monotonic() - started, 1))
    return True


def batch(files, workers):
    jobs = {load(f)["id"]: f for f in files}
    done, failed = set(), set()
    pending = dict(jobs)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending:
            ready = {i: f for i, f in pending.items() if set(load(f).get("depends_on", [])) <= done}
            blocked = {i for i, f in pending.items() if set(load(f).get("depends_on", [])) & failed}
            for i in blocked:
                emit(job=i, status="blocked", reason="dependency failed")
                failed.add(i)
                pending.pop(i)
            if not ready:
                if pending:
                    raise ValueError("Unresolvable depends_on: " + ", ".join(pending))
                break
            futures = {i: pool.submit(run_job, f) for i, f in ready.items()}
            for i, future in futures.items():
                try:
                    ok = future.result()
                except Exception as exc:
                    emit(job=i, status="failed", error=str(exc))
                    ok = False
                (done if ok else failed).add(i)
                pending.pop(i)
    emit(batch="done", ok=sorted(done), failed=sorted(failed))
    return not failed


def job_dirs(ids):
    return [JOBS / i for i in ids] if ids else sorted(p for p in JOBS.glob("*") if (p / "job.json").exists())


def status(ids):
    for d in job_dirs(ids):
        if not (d / "job.json").exists():
            print(d.name, "not run")
            continue
        stages = []
        for s in json.loads((d / "job.json").read_text())["stages"]:
            p = d / "state" / (s["name"] + ".json")
            st = json.loads(p.read_text()) if p.exists() else {"status": "pending"}
            label = st["status"]
            if label == "running":
                try:
                    os.kill(st["pid"], 0)
                except OSError:
                    label = "stale"
            stages.append("%s:%s%s" % (s["name"], label, " %ss" % st["seconds"] if st.get("seconds") else ""))
        print(d.name, " ".join(stages))


def report(ids):
    rows = []
    for d in job_dirs(ids):
        if (d / "events.jsonl").exists():
            rows += [dict(json.loads(l), job=d.name) for l in (d / "events.jsonl").read_text().splitlines() if l]
    ok = [r for r in rows if r["status"] == "ok"]
    for kind in ("scene", "render"):
        k = [r for r in ok if r["kind"] == kind]
        if k:
            secs = [r["seconds"] for r in k]
            print(json.dumps({"kind": kind, "runs": len(k), "total_s": round(sum(secs), 1),
                              "mean_s": round(sum(secs) / len(secs), 1), "max_s": max(secs),
                              "queued_s": round(sum(r["queued_seconds"] for r in k), 1),
                              "max_rss_mb": max(r["rss_mb"] for r in k)}))
    print(json.dumps({"stage_runs": len(rows), "failed": len(rows) - len(ok)}))


def check():
    blender = detect_blender({})
    expr = ("import bpy,json;p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';"
            "p.get_devices();print('JOBCHECK'+json.dumps({'blender':bpy.app.version_string,"
            "'metal':[d.name for d in p.devices if d.type=='METAL']}))")
    out = subprocess.run([blender, "-b", "--factory-startup", "--disable-autoexec", "--python-expr", expr],
                         capture_output=True, text=True).stdout
    info = json.loads(out.split("JOBCHECK", 1)[1].splitlines()[0])
    mem = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip()
    emit(**info, blender_bin=blender, memory_gb=round(int(mem) / 2**30) if mem else None,
         gpu_slots=GPU_SLOTS, blender_slots=BLENDER_SLOTS, profiles=sorted(PROFILES))


def main():
    parser = argparse.ArgumentParser(description="Perhaps asset job runner")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    p = sub.add_parser("validate"); p.add_argument("jobs", nargs="+")
    p = sub.add_parser("run"); p.add_argument("job"); p.add_argument("--only", nargs="+", default=())
    p.add_argument("--force", action="store_true", help="rerun selected stages even if unchanged")
    p = sub.add_parser("batch"); p.add_argument("jobs", nargs="+"); p.add_argument("--workers", type=int, default=2)
    p = sub.add_parser("status"); p.add_argument("ids", nargs="*")
    p = sub.add_parser("report"); p.add_argument("ids", nargs="*")
    args = parser.parse_args()
    try:
        if args.command == "check":
            check()
        elif args.command == "validate":
            for f in args.jobs:
                validate(json.loads(Path(f).read_text()), inputs_may_be_pending=True)
                emit(job=f, status="valid")
        elif args.command == "run":
            sys.exit(0 if run_job(args.job, args.only, args.force) else 1)
        elif args.command == "batch":
            sys.exit(0 if batch(args.jobs, args.workers) else 1)
        elif args.command == "status":
            status(args.ids)
        else:
            report(args.ids)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        emit(status="error", error=str(exc))
        sys.exit(2)


if __name__ == "__main__":
    main()
