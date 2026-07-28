# -*- coding: utf-8 -*-
"""
폭염-정전-시민건강 chain: 현재 보유 데이터만으로의 최대 분석 (2026-06-14)
입력(모두 open-go-kr): NEDIS 온열질환, ASOS 일자료 2020-25, DSSP 한전정전, 응급의료기관 현황
출력: 콘솔 findings + 파생 CSV (시군구 집계, 일별 노출-피해)
"""
import pandas as pd, numpy as np, glob, json, re
pd.set_option('display.width',220); pd.set_option('display.unicode.east_asian_width',True)
OUT={}

# ───────────────────────── 1. NEDIS 온열질환 ─────────────────────────
ne=pd.read_excel("FOIA_0522_질병관리청_NEDIS온열질환_2020-2025.xlsx",sheet_name="DB(2020-2025)발생지역기준")
ne['일자']=pd.to_datetime(ne['발생일자']); ne['연도']=ne['일자'].dt.year
ne['시군구']=(ne['발생시도'].astype(str)+' '+ne['발생시군구'].astype(str)).str.strip()
SEV=['입원:중환자실','사망']  # 중증 정의
ne['중증']=ne['진료결과'].isin(SEV)
ne['사망']=ne['진료결과'].eq('사망')
ne['고령']=ne['나이']>=65
ne['작업장']=ne['발생장소'].astype(str).str.contains('작업장',na=False)
ne['농림']=ne['발생장소'].astype(str).str.contains('논밭|밭|비닐하우스|축사|과수원|어업|해상',na=False)

print("="*60,"\n[1] NEDIS 온열질환 전국 추이")
yr=ne.groupby('연도').agg(발생=('보고번호','size'),사망=('사망','sum'),중증=('중증','sum'),고령비중=('고령','mean'))
yr['고령비중']=(yr['고령비중']*100).round(1)
print(yr.to_string())
print(f"6년 누적 {len(ne):,}건 · 사망 {ne['사망'].sum()} · 중증 {ne['중증'].sum()} · 65+ {ne['고령'].mean()*100:.1f}% · 실외 {(ne['실내외구분']=='실외').mean()*100:.1f}%")

print("\n[1b] 발생 Top 15 시군구 (raw — 인구보정 안됨)")
g=ne.groupby('시군구').agg(발생=('보고번호','size'),사망=('사망','sum'),중증=('중증','sum'),고령=('고령','mean'),작업장=('작업장','mean'))
top=g.sort_values('발생',ascending=False).head(15).copy()
top['고령%']=(top['고령']*100).round(0); top['작업장%']=(top['작업장']*100).round(0)
print(top[['발생','사망','중증','고령%','작업장%']].to_string())

print("\n[1c] 중증률(중환자+사망 / 발생) 높은 시군구 — 발생≥40 (인구 무관 취약신호)")
g['중증률']=(g['중증']/g['발생']*100); g['n']=g['발생']
sevtop=g[g['발생']>=40].sort_values('중증률',ascending=False).head(12)
print(sevtop[['발생','중증','사망','중증률']].round(1).to_string())

print("\n[1d] 서울 자치구 발생 합계 vs 전국 (대도시 노출 대비)")
seoul=ne[ne['발생시도'].str.contains('서울',na=False)]
print(f"서울 전체 {len(seoul)}건 ({len(seoul)/len(ne)*100:.1f}%) · 서울 인구는 전국 ~18%인데 발생은 이만큼")

# ───────────────────────── 2. ASOS 폭염 노출 ─────────────────────────
print("\n"+"="*60,"\n[2] ASOS 폭염 노출 (일최고≥33 폭염일 / 일최저≥25 열대야)")
asos=[]
for f in sorted(glob.glob("OPEN_0522_기상청_ASOS일자료_*_summer.csv")):
    a=pd.read_csv(f,encoding='cp949'); asos.append(a)
asos=pd.concat(asos,ignore_index=True)
asos['일시']=pd.to_datetime(asos['일시']); asos['연도']=asos['일시'].dt.year
asos['폭염일']=asos['최고기온(°C)']>=33; asos['열대야']=asos['최저기온(°C)']>=25
# 지점당 연 폭염일수
st=asos.groupby(['연도','지점명']).agg(폭염일수=('폭염일','sum'),열대야수=('열대야','sum')).reset_index()
yr2=st.groupby('연도').agg(평균폭염일수=('폭염일수','mean'),평균열대야=('열대야수','mean'))
print(yr2.round(1).to_string())
print(f"관측지점 {asos['지점명'].nunique()}곳 · 기간 5~9월")

# ───────────────── 3. 노출→피해 dose-response (전국 일별, 2024-25) ─────────────────
print("\n"+"="*60,"\n[3] 노출-피해 dose-response (전국 일별, 2024-2025)")
dd=asos[asos['연도'].isin([2024,2025])].groupby('일시').agg(전국평균최고=('최고기온(°C)','mean'),전국최고=('최고기온(°C)','max')).reset_index()
nd=ne[ne['연도'].isin([2024,2025])].groupby('일자').size().rename('온열질환').reset_index()
day=dd.merge(nd,left_on='일시',right_on='일자',how='left').fillna({'온열질환':0})
corr=day['전국평균최고'].corr(day['온열질환'])
print(f"일별 (전국평균 최고기온) vs (온열질환 발생수) 상관계수 r = {corr:.2f}  (n={len(day)}일)")
hot=day[day['전국평균최고']>=30]['온열질환'].mean(); mild=day[day['전국평균최고']<30]['온열질환'].mean()
print(f"전국평균최고 ≥30℃ 날 평균 발생 {hot:.1f}건 vs <30℃ 날 {mild:.1f}건 → {hot/max(mild,0.1):.1f}배")
day.to_csv("DERIVED_0614_일별_노출_피해_2024-25.csv",index=False,encoding='utf-8-sig')

# ───────────────────────── 4. DSSP 한전정전 교차 ─────────────────────────
print("\n"+"="*60,"\n[4] 한전정전(DSSP) × 폭염 (2024-2025 비송전=배전 정전)")
po=pd.read_csv("OPEN_0612_DSSP10089_한전정전raw_2020-2025.csv")
po['일자']=pd.to_datetime(po['IOEP_BGNG_DT'],format='%Y/%m/%d %H:%M:%S',errors='coerce')
po['date']=po['일자'].dt.normalize(); po['연도']=po['일자'].dt.year
po2=po[po['연도'].isin([2024,2025])].copy()
pday=po2.groupby('date').agg(정전건수=('SN','size'),비송전호수=('LAK_0','sum')).reset_index()
m=day.merge(pday,left_on='일시',right_on='date',how='left').fillna({'정전건수':0,'비송전호수':0})
print(f"2024-25 정전 이벤트 {len(po2)}건 · 비송전(배전) 정전 일자 {(pday['비송전호수']>0).sum()}일")
hotp=m[m['전국평균최고']>=30]['정전건수'].mean(); mildp=m[m['전국평균최고']<30]['정전건수'].mean()
print(f"≥30℃ 날 평균 정전 {hotp:.1f}건 vs <30℃ {mildp:.1f}건")
cpr=m['전국평균최고'].corr(m['정전건수'])
print(f"일별 기온 vs 정전건수 r = {cpr:.2f}  (주의: DSSP 적재 편향 가능)")

# ───────────────────────── 5. 응급의료 안전망 ─────────────────────────
print("\n"+"="*60,"\n[5] 응급의료 안전망 × 온열질환 중증")
em=pd.read_excel("FOIA_0608_응급의료기관현황_2020-2025.xlsx",sheet_name="응급의료기관 현황('25.12.31.)",header=6)
em=em.dropna(subset=['기관명'])
emc=em.groupby('지역').agg(응급기관수=('기관명','size'),응급실병상=('[응급실]일반 기준병상','sum')).reset_index()
# NEDIS 시도 단위 중증
sido=ne.groupby('발생시도').agg(발생=('보고번호','size'),중증=('중증','sum'),사망=('사망','sum'))
sido['중증률']=(sido['중증']/sido['발생']*100).round(1)
mm=sido.reset_index().merge(emc,left_on='발생시도',right_on='지역',how='left')
mm['기관당발생']=(mm['발생']/mm['응급기관수']).round(0)
print(mm[['발생시도','발생','중증률','사망','응급기관수','응급실병상','기관당발생']].sort_values('중증률',ascending=False).to_string(index=False))

# 시군구 파생 저장
g.reset_index().to_csv("DERIVED_0614_시군구_온열질환_집계.csv",index=False,encoding='utf-8-sig')
print("\n저장: DERIVED_0614_일별_노출_피해_2024-25.csv, DERIVED_0614_시군구_온열질환_집계.csv")
