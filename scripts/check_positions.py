import json, pathlib

roster_path = pathlib.Path(r'C:\Users\sewon\Documents\고려대학교\26-1\ssg\ddddddd\ssg_project_data_for_teammates_20260614\data\raw\mlb\roster_status\mlb_roster_status_raw_20260612.json')
d = json.loads(roster_path.read_text(encoding='utf-8'))
people = d.get('people', {})

# 타자 상위 현실 후보
hitter_ids = [
    669911, 666134, 671286, 656180, 687952,
    663609, 669234, 666211, 681546, 678225,
    666624, 683770, 642215, 628451, 666185,
    667452, 680862, 669261, 666150, 664059,
]

print('타자 후보 포지션 + 배팅 + 출신국:')
print(f'{"ID":>8}  {"이름":35} {"POS":5} {"BAT":4} {"국가":15}')
print('-' * 80)
for pid in hitter_ids:
    p = people.get(str(pid), {})
    pos = p.get('primaryPosition', {}).get('abbreviation', '?')
    name = p.get('fullName', 'UNKNOWN')
    bat = p.get('batSide', {}).get('code', '?')
    nation = p.get('birthCountry', '?')
    flag = '**한국인**' if nation == 'South Korea' else ''
    print(f'{pid:>8}  {name:35} {pos:5} {bat:4} {nation:15} {flag}')

print()
# 선발 상위 현실 후보
starter_ids = [
    687003, 686730, 682989, 605218, 663765,
    681867, 646242, 677961, 680951, 671162,
    605335, 471911, 674370, 664192, 621389,
]

print('선발 후보 포지션 + 투구 핸드 + 출신국:')
print(f'{"ID":>8}  {"이름":35} {"POS":5} {"HAND":5} {"국가":15}')
print('-' * 80)
for pid in starter_ids:
    p = people.get(str(pid), {})
    pos = p.get('primaryPosition', {}).get('abbreviation', '?')
    name = p.get('fullName', 'UNKNOWN')
    hand = p.get('pitchHand', {}).get('code', '?')
    nation = p.get('birthCountry', '?')
    print(f'{pid:>8}  {name:35} {pos:5} {hand:5} {nation:15}')
