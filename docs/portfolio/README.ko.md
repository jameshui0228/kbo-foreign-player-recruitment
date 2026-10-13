# 공개 결과 확인 예제

**한국어** | [English](README.md)

원자료나 인증정보 없이, 저장소에 포함된 **최종 후보 CSV와 검증 CSV**를 읽어 결과를 확인합니다. Python 3.10 이상과 표준 라이브러리만 사용하며 네트워크 요청을 하지 않습니다.

## 실행

저장소 루트에서 실행합니다.

```bash
python3 scripts/portfolio_demo.py
python3 scripts/portfolio_demo.py --check
python3 -m unittest discover -s tests -v
```

첫 번째 명령은 타자·투수 접촉 후보 각 3명과 검증 표를 출력합니다. 두 번째 명령은 공개 문서·그림이 현재 CSV와 일치하는지 확인합니다. 세 번째 명령은 이 공개 예제의 테스트를 실행합니다.

[실행 결과 문서](results.ko.md) · [검증 그림](validation.svg) · [전체 분석 소개](../../README.ko.md)

## 재현하는 범위

- 결과 표의 필수 컬럼, 후보 순위와 AUC 범위를 확인합니다.
- 저장된 학습 적합도와 선수 단위 검증 결과를 구분해 보여줍니다.
- `--write`를 사용하면 공개 CSV로부터 결과 문서와 그림을 다시 생성합니다.
- **원자료 수집, 모델 재학습, AUC 재계산은 하지 않습니다.** 원표의 분석 방법은 [최종 검증 기록](../final_report_last_validation_v1.md)을 참고하세요.

후보와 시장 정보의 기준 시점은 2026년 6월입니다. 이 예제의 성공을 현재 영입 가능성이나 모델의 미래 예측력 검증으로 해석하지 않습니다.
