import glob, os, sys, time, json
import orjson, fastsimdjson

try:
    import simdjson as pysimdjson
except ImportError:
    pysimdjson = None
try:
    import jiter
except ImportError:
    jiter = None

DATA = os.environ.get("JSONDIR", "simdjson-data/jsonexamples")
FILES = sys.argv[1:] or sorted(glob.glob(os.path.join(DATA, "*.json")))

def bench(fn, data, min_time=0.3):
    fn(data)
    n = 1
    while True:
        t0 = time.perf_counter()
        for _ in range(n):
            fn(data)
        dt = time.perf_counter() - t0
        if dt > 0.05:
            break
        n *= 2
    best = float("inf")
    reps = max(3, int(min_time / dt))
    for _ in range(min(reps, 15)):
        t0 = time.perf_counter()
        for _ in range(n):
            fn(data)
        best = min(best, (time.perf_counter() - t0) / n)
    return best

if __name__ == "__main__":
  jiter_head = f" {'jiter us':>10s}" if jiter else ""
  print(f"{'file':38s} {'KB':>7s} {'json us':>10s} {'orjson us':>10s}{jiter_head} {'fast us':>10s} {'speedup':>8s}")
  for f in FILES:
      data = open(f, "rb").read()
      try:
          ref = orjson.loads(data)
      except Exception:
          continue
      got = fastsimdjson.loads(data)
      if got != ref:
          print("MISMATCH", f)
      tj = bench(json.loads, data)
      to = bench(orjson.loads, data)
      jiter_col = f" {bench(jiter.from_json, data)*1e6:10.1f}" if jiter else ""
      tf = bench(fastsimdjson.loads, data)
      print(f"{os.path.basename(f):38s} {len(data)/1024:7.0f} {tj*1e6:10.1f} {to*1e6:10.1f}{jiter_col} {tf*1e6:10.1f} {to/tf:8.2f}")
