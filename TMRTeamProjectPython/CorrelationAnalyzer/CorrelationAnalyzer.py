import pandas as pd
from matplotlib import pyplot as plt

# 1. 데이터 불러오기
df_paths = [
    "C:/Users/user/Downloads/서울_유동인구_매출_20241.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20242.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20243.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20244.csv"
]

# 2. 데이터 병합
dfs = []
for path in df_paths:
    df = pd.read_csv(path)
    df['행정동_코드'] = df['행정동_코드'].astype(str)
    dfs.append(df)

full_df = pd.concat(dfs, ignore_index=True)

# 3. 상관분석 결과 저장용 리스트
results = []

# 4. 행정동 단위 그룹화
grouped = full_df.groupby(['행정동_코드', '행정동_코드_명'])

# 5. 각 행정동별 상관계수 및 위험도 점수 계산
for (code, name), group in grouped:
    if len(group) >= 2 and group['총_유동인구_수'].std() != 0 and group['당월_매출_금액'].std() != 0:
        corr = group['총_유동인구_수'].corr(group['당월_매출_금액'])
        risk_score = 1 - corr if pd.notnull(corr) else None
        results.append({
            '행정동_코드': code,
            '행정동_코드_명': name,
            '상관계수': corr,
            '상관_위험도점수': risk_score
        })

# 6. 결과 DataFrame 변환 및 저장
cor_df = pd.DataFrame(results)
cor_df.to_csv("result_analyzer.csv", index=False, encoding='utf-8-sig')

# 한글 폰트 설정 (윈도우 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 상관분석 결과 불러오기
cor_df = pd.read_csv("../result_analyzer.csv")

# 위험도 점수 내림차순 정렬
cor_df = cor_df.sort_values(by='상관_위험도점수', ascending=False)

# 시각화
plt.figure(figsize=(12, 6))
plt.bar(cor_df['행정동_코드_명'], cor_df['상관_위험도점수'], color='salmon')
plt.xticks(rotation=90)
plt.xlabel('행정동명')
plt.ylabel('상관 기반 위험도 점수 (1 - 상관계수)')
plt.title('행정동별 상관분석 위험도 점수')
plt.tight_layout()
plt.show()
