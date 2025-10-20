import os, re, sys, json
ROOT = sys.argv[1] if len(sys.argv)>1 else "."
findings = []
pat_secrets = re.compile(r'(api_key|token|password|secret)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}', re.I)
pat_userpath = re.compile(r'[A-Z]:\\Users\\[^\\]+', re.I)
pat_fromhub = re.compile(r'^FROM\s+python:', re.I)

for dirpath,_,filenames in os.walk(ROOT):
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
        except:
            continue
        if pat_secrets.search(txt):
            findings.append({"file": fp, "issue": "possible_secret_literal"})
        if pat_userpath.search(txt):
            findings.append({"file": fp, "issue": "windows_user_path"})
        if fn.lower()=="dockerfile" and pat_fromhub.search(txt):
            findings.append({"file": fp, "issue": "dockerhub_base_image"})
print(json.dumps(findings, indent=2))
