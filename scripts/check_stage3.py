import pandas as pd
import json

h = pd.read_csv('outputs/tables/candidate_hitter_pool.csv')
s = pd.read_csv('outputs/tables/candidate_starter_pool.csv')

print('타자 컬럼:', list(h.columns))
print()
print('Savant 컬럼 매칭 현황:')
sav_cols_h = ['avg_ev', 'hard_hit_pct', 'xwoba', 'whiff_pct', 'chase_pct']
sav_cols_s = ['avg_velo', 'whiff_pct', 'arm_angle']
for c in sav_cols_h:
    if c in h.columns:
        n = h[c].notna().sum()
        print(f'  타자 {c}: {n}/{len(h)} 매칭')
for c in sav_cols_s:
    if c in s.columns:
        n = s[c].notna().sum()
        print(f'  선발 {c}: {n}/{len(s)} 매칭')

txns_path = r'C:\Users\sewon\Documents\고려대학교\26-1\ssg\ddddddd\ssg_project_data_for_teammates_20260614\data\raw\mlb\transactions\mlb_transactions_raw_20251001_20260613.json'
txns = json.loads(open(txns_path, encoding='utf-8').read())
id_to_name = {}
for t in txns.get('transactions', []):
    p = t.get('person', {})
    if p.get('id') and p.get('fullName'):
        id_to_name[p['id']] = p['fullName']

# also from people in roster
roster_path = r'C:\Users\sewon\Documents\고려대학교\26-1\ssg\ddddddd\ssg_project_data_for_teammates_20260614\data\raw\mlb\roster_status\mlb_roster_status_raw_20260612.json'
roster = json.loads(open(roster_path, encoding='utf-8').read())
for pid_str, pinfo in roster.get('people', {}).items():
    pid = int(pid_str)
    if pid not in id_to_name and pinfo.get('fullName'):
        id_to_name[pid] = pinfo['fullName']

print()
print('타자 상위 15명 (이름 포함):')
for _, row in h.head(15).iterrows():
    pid = int(row['mlb_id'])
    name = id_to_name.get(pid, 'UNKNOWN')
    avail = 'O' if row.get('available') else '-'
    ops = row.get('ops', 0)
    fit = row.get('ssg_fit_score', 0)
    iso = row.get('iso', 0)
    bb = row.get('bb_pct', 0)
    k = row.get('k_pct', 0)
    xw = row.get('xwoba', None)
    print(f'  [{avail}] {name} ({pid}) OPS={ops:.3f} ISO={iso:.3f} BB={bb:.1%} K={k:.1%} xwOBA={xw} fit={fit:.1f}')

print()
print('선발 상위 15명 (이름 포함):')
for _, row in s.head(15).iterrows():
    pid = int(row['mlb_id'])
    name = id_to_name.get(pid, 'UNKNOWN')
    avail = 'O' if row.get('available') else '-'
    era = row.get('era', 0)
    k9 = row.get('k9', 0)
    bb9 = row.get('bb9', 0)
    fit = row.get('ssg_fit_score', 0)
    velo = row.get('avg_velo', None)
    arm = row.get('arm_angle', None)
    print(f'  [{avail}] {name} ({pid}) ERA={era:.2f} K9={k9:.1f} BB9={bb9:.1f} velo={velo} arm={arm} fit={fit:.1f}')
