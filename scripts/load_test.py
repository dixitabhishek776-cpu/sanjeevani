#!/usr/bin/env python3
"""Bounded, read-only load smoke test for an owned staging service.
Usage: python scripts/load_test.py https://staging.example.com 50 10
Args: URL, total requests (<=2000), concurrency (<=50)
"""
import asyncio, sys, time, statistics
import httpx

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
count = min(max(int(sys.argv[2]) if len(sys.argv) > 2 else 50, 1), 2000)
concurrency = min(max(int(sys.argv[3]) if len(sys.argv) > 3 else 10, 1), 50)

async def one(client, sem, i):
    async with sem:
        t=time.perf_counter()
        try:
            r=await client.get(base+"/livez")
            return r.status_code, (time.perf_counter()-t)*1000, None
        except Exception as exc:
            return 0, (time.perf_counter()-t)*1000, type(exc).__name__

async def main():
    sem=asyncio.Semaphore(concurrency)
    limits=httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(timeout=10, limits=limits) as client:
        started=time.perf_counter()
        results=await asyncio.gather(*(one(client,sem,i) for i in range(count)))
        elapsed=time.perf_counter()-started
    ok=[lat for status,lat,err in results if status==200]
    errors=[(status,err) for status,lat,err in results if status!=200]
    ok_sorted=sorted(ok)
    def pct(p):
        if not ok_sorted: return None
        idx=min(len(ok_sorted)-1, max(0, int(len(ok_sorted)*p)-1))
        return round(ok_sorted[idx],2)
    report={
        "url":base,"requests":count,"concurrency":concurrency,"elapsed_s":round(elapsed,3),
        "throughput_rps":round(count/elapsed,2) if elapsed else None,
        "success":len(ok),"errors":len(errors),
        "p50_ms":pct(.50),"p95_ms":pct(.95),"p99_ms":pct(.99),
        "mean_ms":round(statistics.mean(ok),2) if ok else None,
        "error_samples":errors[:10],
    }
    print(report)
    if len(ok)!=count: raise SystemExit(1)

if __name__=="__main__": asyncio.run(main())
