# Data Audit

Updated: 2026-06-12 KST

## Available Data

| source | status | use |
|---|---|---|
| STATIZ API snapshot and refetches | available | KBO team/player context, 2026 current SSG diagnosis |
| STATIZ team situations | available | KBO rank comparisons by base state, inning, count, home/away |
| STATIZ SSG player situations | available | role split and context bottlenecks |
| MLB Baseball Savant 2023-2026 | available | candidate feature learning for hitter/pitcher profiles |
| Naver Search News metadata | available | external narrative mining; not a truth source by itself |
| KBO ABS research paper result data | available | ABS environment and command-model argument |
| KBO/foreign-player rule articles | available | market constraints for foreign and Asian quota slots |

## Known Data Risks

| risk | severity | mitigation |
|---|---|---|
| 2026 season partial sample | high | check historical seasons and sensitivity |
| Naver search query bias | medium | use as corroboration only |
| Candidate availability unknown | high | add roster/contract/40-man/NPB/CPBL status data |
| Asian quota first-year sample | high | treat as option-market thesis, not outcome-proven model |
| KBO pitch-location data not fully available | high | use ABS paper + Savant translation until KBO pitch data is accessible |
| Role labels are analytical | medium | review role definitions before final deck |

## Immediate Data Gaps

1. Candidate availability and contract status.
2. MiLB/NPB/CPBL/Australia candidate stats.
3. KBO foreign-player historical success labels.
4. KBO ABS pitch-location at player/team level.
5. Injury and medical risk history.
6. Visa and replacement-rule feasibility.

