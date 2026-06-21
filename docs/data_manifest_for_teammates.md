# Data Manifest For Teammates

이 문서는 팀원들이 프로젝트에서 어떤 데이터를 썼는지 확인하기 위한 manifest입니다.
원천 데이터 전체를 public GitHub에 그대로 올리는 대신, 파일 목록, 출처 그룹, 용량, 행 수 추정치, 공개 정책을 기록합니다.

## Summary

- Total local data/output files scanned: 431
- Total scanned size: 1,220.9 MB
- Raw data size: 693.6 MB
- Processed data size: 413.6 MB
- Git-tracked data/output size: 97.6 MB

## Policy

- `tracked_in_github`: GitHub에 올라간 schema/derived output입니다.
- `do_not_public_git`: API/대회/뉴스/PDF 등 public repo 재배포가 조심스러운 원천입니다.
- `large_or_regenerable`: 대용량 파일입니다. 필요하면 Git LFS, Release, Google Drive, 또는 재수집 스크립트를 씁니다.
- `private_or_regenerate`: public GitHub에는 올리지 않고, source log와 script로 재현하거나 private 공유합니다.

## Source Group Summary

| source group | publish policy | files | size MB |
|---|---|---:|---:|
| Baseball Savant/Statcast | large_or_regenerable | 128 | 977.0 |
| External ABS paper replication data | private_or_regenerate | 5 | 0.0 |
| Literature PDFs | do_not_public_git | 5 | 12.2 |
| MLB official/stats API | private_or_regenerate | 7 | 73.5 |
| NPB/CPBL official roster and stats outputs | tracked_in_github | 9 | 2.6 |
| NPB/CPBL official roster collection | private_or_regenerate | 2 | 0.0 |
| Naver News Search API | do_not_public_git | 6 | 14.7 |
| Other | do_not_public_git | 6 | 2.2 |
| Processed KBO labels | private_or_regenerate | 1 | 0.2 |
| Project schema | tracked_in_github | 5 | 0.0 |
| STATIZ API/local KBO snapshot | do_not_public_git | 31 | 39.7 |
| Tracked analysis output | tracked_in_github | 216 | 98.1 |
| Wikipedia templates | private_or_regenerate | 10 | 0.7 |

## Full Manifest

Full CSV: `outputs/tables/project_data_file_manifest_v1.csv`

## Practical Sharing Recommendation

팀원이 분석 흐름과 사용 데이터 종류를 확인하는 데는 이 manifest와 `docs/source_log.md`면 충분합니다.
실제 원천 파일까지 실행해야 하는 팀원에게는 `data/raw/`, `data/processed/`, `data/external/`을 Google Drive 또는 별도 private 저장소로 공유하는 편이 안전합니다.
특히 STATIZ API/공모전 데이터와 Naver API raw data는 public GitHub에 직접 올리지 않는 것을 권장합니다.
