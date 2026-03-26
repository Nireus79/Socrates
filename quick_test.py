#!/usr/bin/env python
"""Quick routing test"""
import subprocess, time, requests, sys, os
os.chdir(os.path.dirname(__file__))
env = os.environ.copy()
env['PYTHONPATH'] = f"{os.getcwd()}/backend/src:{os.getcwd()}/cli/src"

api = subprocess.Popen([sys.executable, '-m', 'socrates_api'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
time.sleep(10)

try:
    tests = [
        ("/", "Direct root"),
        ("/health", "Direct health"),
        ("/auth/csrf-token", "Auth"),
        ("/projects", "Projects"),
    ]
    
    for path, desc in tests:
        try:
            r = requests.get(f"http://localhost:8000{path}", timeout=2)
            status = "OK" if r.status_code != 404 else "FAIL"
            print(f"{desc:20} {path:30} {r.status_code} {status}")
        except Exception as e:
            print(f"{desc:20} {path:30} ERROR")

finally:
    api.terminate()
    try:
        api.wait(timeout=1)
    except:
        api.kill()
