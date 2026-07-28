# -*- coding: utf-8 -*-
"""인구 정규화 + 인구 통제 편상관/회귀 (2026-06-30)
입력(정보공개청구/): 정전_시군구_3중_merged_2026-06-22.csv, 0630_시군구별+주민등록인구.csv
목적: raw 3중 상관의 '큰 동네 효과'를 제거한 진짜 관계 추정
"""
import csv, numpy as np, os
BASE = r"C:/cross_the_street/docs/research/_data-center/기획서_꾸러미/정보공개청구"

# 1) 인구 파싱: 새 파일 = 남/여 × 5세별 × 연도(2020-2025), '계'·총인구 행 없음 → 직접 합산
#    분모 = 2020~2025 평균(분석 기간 일치). key -> (총인구, 고령65+)
SIDO_SUF=('특별시','광역시','특별자치시','특별자치도','도')
OLD={'65 - 69세','70 - 74세','75 - 79세','80 - 84세','85 - 89세','90 - 94세','95 - 99세','100+'}
pop={}; old={}; cur=None
with open(os.path.join(BASE,'OPEN_0630_KOSIS_시군구주민등록인구_2020-2025.csv'),encoding='cp949',newline='') as fh:
    r=csv.reader(fh); hdr=next(r)
    yi=[i for i,h in enumerate(hdr) if '년' in h]   # 2020~2025 연도 열
    for row in r:
        if not row or len(row)<=max(yi): continue
        name=row[0]
        if name=='전국': continue
        if name.endswith(SIDO_SUF): cur=name; continue   # 시도 행 → 컨텍스트만
        key=f'{cur} {name}'
        vals=[int(row[i]) for i in yi if row[i].strip().isdigit()]
        if not vals: continue
        v=sum(vals)/len(vals)    # 2020-2025 평균
        pop[key]=pop.get(key,0)+v
        if row[1] in OLD: old[key]=old.get(key,0)+v
print('인구 시군구 수:',len(pop))

# 2) merged 로드 + 인구 병합
rows=[]
with open(os.path.join(BASE,"DERIVED_0630_정전_시군구_3중_merged_v2.csv"),encoding='utf-8-sig',newline='') as fh:
    for d in csv.DictReader(fh):
        k=d['key']
        if k not in pop: continue
        rows.append({'key':k,'정전건수':float(d['정전건수']),'정전호수':float(d['정전호수'] or 0),
            '온열':float(d['온열발생']),'중증률':float(d['중증률'] or 0),'전력':float(d['전력GWh'] or 0),
            '인구':pop[k],'고령':old.get(k,0)})
print('인구까지 매칭된 시군구:',len(rows),'/ merged 대비')

import numpy as np
def arr(c): return np.array([r[c] for r in rows],dtype=float)
인구=arr('인구'); 정전=arr('정전건수'); 호수=arr('정전호수'); 온열=arr('온열'); 전력=arr('전력'); 고령=arr('고령')

# 3) 율 변환
온열률=온열/인구*1e5            # 10만명당
온열률고령=온열/고령*1e5         # 고령10만명당
정전율=정전/인구*1e4            # 1만명당 정전건수
호수율=호수/인구               # 1인당 정전호수(노출)

def r(a,b): return np.corrcoef(a,b)[0,1]
print('\\n=== [A] raw(원자료) 상관 ===')
print(f'정전건수 vs 온열   r={r(정전,온열):.2f}')
print(f'전력     vs 온열   r={r(전력,온열):.2f}')
print(f'정전건수 vs 전력   r={r(정전,전력):.2f}')
print(f'인구     vs 온열   r={r(인구,온열):.2f}   (← 큰 동네 효과 크기)')
print(f'인구     vs 정전   r={r(인구,정전):.2f}')
print(f'인구     vs 전력   r={r(인구,전력):.2f}')

print('\\n=== [B] 율(인구 정규화) 상관 ===')
print(f'정전율(만명당) vs 온열률(10만명당)  r={r(정전율,온열률):.2f}')
print(f'전력          vs 온열률             r={r(전력,온열률):.2f}')
print(f'정전율        vs 전력               r={r(정전율,전력):.2f}')

# 4) 편상관 (인구 통제)
def pcorr(x,y,z):
    rxy,rxz,ryz=r(x,y),r(x,z),r(y,z)
    return (rxy-rxz*ryz)/np.sqrt((1-rxz**2)*(1-ryz**2))
print('\\n=== [C] 인구 통제 편상관 r(·,·|인구) ===')
print(f'정전 vs 온열 | 인구  r={pcorr(정전,온열,인구):.2f}')
print(f'전력 vs 온열 | 인구  r={pcorr(전력,온열,인구):.2f}')
print(f'정전 vs 전력 | 인구  r={pcorr(정전,전력,인구):.2f}')

# 5) 다중회귀 (표준화) 온열 ~ 인구 + 정전 + 전력
def z(a): return (a-a.mean())/a.std()
X=np.column_stack([np.ones(len(인구)),z(인구),z(정전),z(전력)])
beta,_,_,_=np.linalg.lstsq(X,z(온열),rcond=None)
yhat=X@beta; ss_res=((z(온열)-yhat)**2).sum(); ss_tot=((z(온열)-z(온열).mean())**2).sum()
print('\\n=== [D] 표준화 다중회귀: 온열 ~ 인구+정전+전력 ===')
print(f'  β(인구)={beta[1]:+.2f}  β(정전)={beta[2]:+.2f}  β(전력)={beta[3]:+.2f}   R²={1-ss_res/ss_tot:.2f}')
print('  (표준화 β = 다른 변수 통제 후 독립 기여. |β| 클수록 영향 큼)')

# 6) 인구 걷어낸 진짜 위험 시군구 (온열률 상위, 인구≥5만)
big=[(rows[i]['key'],온열률[i],온열[i],인구[i],정전율[i],전력[i],rows[i]['중증률']) for i in range(len(rows)) if 인구[i]>=50000]
print('\\n=== [E] 온열 발생률(10만명당) Top 15  [인구≥5만] — 큰 동네 효과 제거 ===')
for k,rate,n,p,jr,e,sv in sorted(big,key=lambda x:-x[1])[:15]:
    print(f'  {rate:>5.0f}/10만  (발생{int(n):>4}, 인구{int(p):>7,})  정전율{jr:>4.1f}  전력{e:>6,.0f}  중증{sv:>4.1f}%  {k}')

# 저장
import csv as _c
with open(os.path.join(BASE,'DERIVED_0630_정전_3중_인구정규화.csv'),'w',encoding='utf-8-sig',newline='') as fh:
    w=_c.writer(fh); w.writerow(['key','인구','고령','온열','온열률10만','온열률고령10만','정전건수','정전율만명','전력GWh','중증률'])
    for i in range(len(rows)):
        w.writerow([rows[i]['key'],int(인구[i]),int(고령[i]),int(온열[i]),round(온열률[i],1),
            round(온열률고령[i],1),int(정전[i]),round(정전율[i],2),round(전력[i],0),rows[i]['중증률']])
print('\\n저장: DERIVED_0630_정전_3중_인구정규화.csv')
print('DONE-NORM')
