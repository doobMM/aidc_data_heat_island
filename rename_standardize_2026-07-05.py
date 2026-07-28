# -*- coding: utf-8 -*-
"""파일명 표준화 rename 스크립트 (2026-07-05)

⚠⚠⚠ 실행 금지 — 사용자 승인 후에만 실행 ⚠⚠⚠
- 다른 agent가 원본 파일명으로 이 폴더 파일을 읽는 중이다.
- 스크립트 4개(analyze_*.py)가 old 이름을 하드코딩/글롭한다.
  특히 analyze_outage_sigungu_cross의 glob "(0621) *.xlsx"는 rename 후 무효.
- 계획·매핑 근거: 스크립트_인벤토리_README_2026-07-05.md §5

사용법:
    python rename_standardize_2026-07-05.py            # dry-run (기본): 계획만 출력, 변경 없음
    python rename_standardize_2026-07-05.py --apply    # 실제 rename (사용자 승인 후에만!)

규칙: FOIA_(정보공개청구) / OPEN_(공공포털) / DERIVED_(파생) 접두어 + 기존 날짜 유지.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# old → new (스크립트_인벤토리_README_2026-07-05.md §5-2와 동일해야 함)
MAPPING = {
    # ── FOIA (정보공개청구) ──
    "0622_2020~2025 정전데이터(공공데이터 제공용)_fv.xlsx":
        "FOIA_0622_한전_정전이력_2020-2025.xlsx",
    "0522_정보공개자료(16692246).xlsx":
        "FOIA_0522_질병관리청_NEDIS온열질환_2020-2025.xlsx",
    "0608_1. 응급의료기관 현황(20~25년).xlsx":
        "FOIA_0608_응급의료기관현황_2020-2025.xlsx",          # 출처유형 [확인 필요]
    "0608_2. 응급의료기관 외의 의료기관(20년~25년).xlsx":
        "FOIA_0608_응급의료기관외_의료기관_2020-2025.xlsx",    # 출처유형 [확인 필요]

    # ── OPEN (공공포털 공개) ──
    "(0621) 2501_03_산업분류별-법정동별 전력데이터.xlsx":
        "OPEN_0621_한전_산업분류법정동전력_2501-03.xlsx",
    "(0621) 2504_06_산업분류별-법정동별 전력데이터.xlsx":
        "OPEN_0621_한전_산업분류법정동전력_2504-06.xlsx",
    "(0621) 2507_09_산업분류별-법정동별 전력데이터.xlsx":
        "OPEN_0621_한전_산업분류법정동전력_2507-09.xlsx",
    "(0621) 2510_12_산업분류별-법정동별 전력데이터.xlsx":
        "OPEN_0621_한전_산업분류법정동전력_2510-12.xlsx",
    "0520_OBS_ASOS_DD_20260520165647.csv":
        "OPEN_0520_기상청_ASOS일자료_20260520165647.csv",
    "0520_OBS_ASOS_DD_20260520171628.csv":
        "OPEN_0520_기상청_ASOS일자료_20260520171628.csv",
    "0520_국민기초생활보장수급자_및_등록장애인_20260520180503.xlsx":
        "OPEN_0520_KOSIS_기초수급자_등록장애인_20260520.xlsx",
    "0520_시군구별_장애정도별_성별_등록장애인수_20260520180030.xls":
        "OPEN_0520_KOSIS_시군구_등록장애인수_20260520.xls",
    "0520_한국전력공사_데이터센터 전기공급 현황_20231231.csv":
        "OPEN_0520_한전_DC전기공급현황_20231231.csv",
    "0520_한국전력공사_배전 정전통계종합 정보_20241231.csv":
        "OPEN_0520_한전_배전정전통계종합_20241231.csv",
    "0522_OBS_ASOS_DD_2020_summer.csv": "OPEN_0522_기상청_ASOS일자료_2020_summer.csv",
    "0522_OBS_ASOS_DD_2021_summer.csv": "OPEN_0522_기상청_ASOS일자료_2021_summer.csv",
    "0522_OBS_ASOS_DD_2022_summer.csv": "OPEN_0522_기상청_ASOS일자료_2022_summer.csv",
    "0522_OBS_ASOS_DD_2023_summer.csv": "OPEN_0522_기상청_ASOS일자료_2023_summer.csv",
    "0522_OBS_ASOS_DD_2024_summer.csv": "OPEN_0522_기상청_ASOS일자료_2024_summer.csv",
    "0522_OBS_ASOS_DD_2025_summer.csv": "OPEN_0522_기상청_ASOS일자료_2025_summer.csv",
    "0612_DSSP-IF-10089_한전정전_이벤트raw_2020-2025.csv":
        "OPEN_0612_DSSP10089_한전정전raw_2020-2025.csv",
    "0612_dssp_10089_raw_page1.json": "OPEN_0612_DSSP10089_rawpage1.json",
    "0612_dssp_10089_raw_page2.json": "OPEN_0612_DSSP10089_rawpage2.json",
    "0612_dssp_10089_raw_page3.json": "OPEN_0612_DSSP10089_rawpage3.json",
    "0614_한국전기안전공사_발변전소 검사 개선조치 전기, 기계 원인별_20190630.csv":
        "OPEN_0614_전기안전공사_발변전소검사개선_20190630.csv",
    "0614_한국전력공사_배전 고압부하 정보_20250630.csv":
        "OPEN_0614_한전_배전고압부하_20250630.csv",
    "0614_한국전력공사_변전소운전실적관리시스템_변전운전실적 권역별 부하정보_10_05_2020.csv":
        "OPEN_0614_한전_변전운전실적_권역부하_20201005.csv",
    "0614_한국전력공사_지역별수요예측(REDFOS)_수요예측권역및본부명정보_20201006.csv":
        "OPEN_0614_한전_REDFOS_수요예측권역_20201006.csv",
    "0621_한국전력공사_산업분류별 법정동별 전력사용량_20250630.csv":
        "OPEN_0621_한전_산업분류법정동전력_20250630.csv",
    "0621_한국전력공사_지역별 공급가능 변전소 정보_20240513.csv":
        "OPEN_0621_한전_공급가능변전소_20240513.csv",
    "0630_시군구별_주민등록인구.csv":
        "OPEN_0630_KOSIS_시군구주민등록인구_2020-2025.csv",
    "0630_시도_산업_종사자규모별_사업체수.xls":
        "OPEN_0630_KOSIS_시도산업_사업체수.xls",
    "0702_한국전력거래소_시간별 지역별 육지 태양광 제어횟수_20240630.csv":
        "OPEN_0702_KPX_태양광제어횟수_20240630.csv",
    "0703_한국에너지공단_에너지바우처 연도별 발급 가구수_20251231.csv":
        "OPEN_0703_에너지공단_바우처발급가구_2018-2025.csv",

    # ── DERIVED (파생) ──
    "derived_시군구_온열질환_집계.csv": "DERIVED_0614_시군구_온열질환_집계.csv",
    "derived_일별_노출_피해_2024-25.csv": "DERIVED_0614_일별_노출_피해_2024-25.csv",
    "정전_3중_인구정규화_2026-06-30.csv": "DERIVED_0630_정전_3중_인구정규화.csv",
    "정전_시군구_3중_merged_2026-06-30_v2.csv": "DERIVED_0630_정전_시군구_3중_merged_v2.csv",
    "지사_시군구_crosswalk_2026-06-30_v2.csv": "DERIVED_0630_지사_시군구_crosswalk_v2.csv",
}


def main():
    apply = "--apply" in sys.argv
    mode = "APPLY(실제 개명)" if apply else "DRY-RUN(계획만 — 변경 없음)"
    print(f"[모드] {mode} / 대상 폴더: {BASE}")
    print(f"[매핑] {len(MAPPING)}건\n")

    missing, collide, todo = [], [], []
    for old, new in MAPPING.items():
        src, dst = os.path.join(BASE, old), os.path.join(BASE, new)
        if not os.path.exists(src):
            missing.append(old)
            continue
        if os.path.exists(dst):
            collide.append(new)
            continue
        todo.append((old, new))

    for old, new in todo:
        print(f"  {old}\n    -> {new}")
    if missing:
        print(f"\n[경고] 원본 없음 {len(missing)}건 (이미 개명됐거나 이동됨):")
        for m in missing:
            print(f"  - {m}")
    if collide:
        print(f"\n[중단 사유] 대상 이름 이미 존재 {len(collide)}건:")
        for c in collide:
            print(f"  - {c}")

    if not apply:
        print("\n[dry-run 종료] 실제 개명하려면: python rename_standardize_2026-07-05.py --apply")
        print("⚠ 실행 전 스크립트_인벤토리_README_2026-07-05.md §5-3 체크리스트 확인 (다른 agent 작업·스크립트 경로 참조).")
        return

    if collide:
        print("\n[중단] 충돌 해결 전에는 --apply를 진행하지 않습니다.")
        sys.exit(1)

    log_path = os.path.join(BASE, "rename_log_2026-07-05.txt")
    with open(log_path, "a", encoding="utf-8") as log:
        for old, new in todo:
            os.rename(os.path.join(BASE, old), os.path.join(BASE, new))
            log.write(f"{old}\t{new}\n")
            print(f"[개명] {old} -> {new}")
    print(f"\n완료 {len(todo)}건. 로그: {log_path}")
    print("⚠ 후속 의무: analyze_*.py 4개의 경로 참조 + glob \"(0621) *.xlsx\" 갱신 필요.")


if __name__ == "__main__":
    main()
