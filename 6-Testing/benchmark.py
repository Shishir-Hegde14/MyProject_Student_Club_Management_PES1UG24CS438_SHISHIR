import argparse
import json
import logging
import os
import platform
import statistics
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '5-Code'))
from app import create_app
from werkzeug.serving import make_server
from waitress import create_server


def summary(results, limit):
    times = sorted(r[0] for r in results)
    return {'requests':len(results),'successful':sum(r[1] for r in results),
            'median_ms':round(statistics.median(times),2),'p95_ms':round(times[max(0,int(len(times)*.95)-1)],2),
            'max_ms':round(max(times),2),'target_ms':limit,
            'within_target':sum(t < limit for t in times),
            'target_met':all(ok and t < limit for t,ok in results)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='6-Testing/results/performance.json')
    parser.add_argument('--server', choices=['waitress','werkzeug'],default='waitress')
    args=parser.parse_args()
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('waitress').setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory() as folder:
        app=create_app({'DATABASE':str(Path(folder)/'load.sqlite3'),'SECRET_KEY':'benchmark-only'})
        p=app.extensions['portal']
        with p.db(True) as con:
            con.execute("INSERT INTO clubs VALUES(1,'Load test club',10000000)")
            for i,role in [(1,'lead'),(2,'coordinator'),(3,'finance'),(4,'dean'),(6,'checkin')]:
                con.execute('INSERT INTO users VALUES(?,?,?,?,?)',(i,f'user{i}','not-used',role,1 if i==1 else None))
            con.executemany('INSERT INTO users VALUES(?,?,?,?,?)',[(i,f'user{i}','not-used','student',None) for i in range(100,600)])
        e=p.create_event(1,'Benchmark event',(date.today()+timedelta(days=7)).isoformat(),'Hall',1000,[('Equipment','1000')])
        p.submit(1,e)
        for i in [2,3,4]: p.review(i,e,'approve')
        tokens=[p.token(p.ticket(i,p.register(i,e))) for i in range(100,200)]
        if args.server=='waitress':
            server=create_server(app,host='127.0.0.1',port=0,threads=16,connection_limit=1024,backlog=1024)
            serve,port=server.run,server.effective_port
        else:
            server=make_server('127.0.0.1',0,app,threaded=True)
            serve,port=server.serve_forever,server.server_port
        thread=threading.Thread(target=serve,daemon=True)
        thread.start()
        base=f'http://127.0.0.1:{port}'
        signer=app.session_interface.get_signing_serializer(app)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def cookie(user): return 'session='+signer.dumps({'user_id':user,'csrf':'load-test'})
        def request(path,user,data=None):
            start=time.perf_counter()
            try:
                req=urllib.request.Request(base+path,data=urllib.parse.urlencode(data).encode() if data else None,headers={'Cookie':cookie(user)})
                with opener.open(req,timeout=60) as response:
                    body=response.read()
                    ok=response.status==200 and (b'Entry accepted' in body if data else b'Events' in body)
            except Exception:
                ok=False
            return (time.perf_counter()-start)*1000,ok
        barrier=threading.Barrier(500)
        def page(user):
            barrier.wait(timeout=60)
            return request('/',user)
        with ThreadPoolExecutor(max_workers=500) as pool:
            pages=list(pool.map(page,range(100,600)))
        baseline=[]
        for token in tokens[:50]:
            baseline.append(request('/checkin',6,{'csrf':'load-test','event_id':e,'token':token}))
        def scan(token): return request('/checkin',6,{'csrf':'load-test','event_id':e,'token':token})
        with ThreadPoolExecutor(max_workers=20) as pool:
            peak=list(pool.map(scan,tokens[50:]))
        server.close() if args.server=='waitress' else server.shutdown()
        result={'run_at_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
                'platform':platform.platform(),'logical_cpus':os.cpu_count(),
                'server':args.server,
                'method':'Loopback HTTP against '+args.server+'; 500 distinct pre-authenticated users released together. Server HTML response time, not browser paint or WAN latency. QR check-in POST includes CSRF, authorization and database update.',
                'page_500_concurrent':summary(pages,2000),'checkin_sequential':summary(baseline,100),
                'checkin_20_workers':summary(peak,100)}
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))


if __name__=='__main__': main()
