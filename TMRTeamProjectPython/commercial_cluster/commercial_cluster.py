import glob
import os

import matplotlib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

os.environ["OMP_NUM_THREADS"] = "2"

# ✅ 한글 폰트 설정 (Windows 기준)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ✅ 폴더 설정
DATA_DIR = 'C:/Users/user/Downloads/업종별_병합결과'
SAVE_DIR = 'C:/Users/user/Downloads/업종별_병합결과_클로스터링'
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ 사용할 feature
selected_features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액',
    '지하철_역_수', '대학교_수', '관공서_수'
]

# ✅ 클러스터 요약 모으기
summary_list = []

# ✅ 모든 업종 파일 처리
for file_path in glob.glob(os.path.join(DATA_DIR, '*.csv')):
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    print(f"🔍 처리 중: {filename}")

    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except Exception as e:
        print(f"❌ 오류: {e}")
        continue

    if not all(col in df.columns for col in selected_features):
        print(f"⚠️ {filename} → 필요한 컬럼 없음, 건너뜀")
        continue

    df_selected = df[selected_features].fillna(0)

    # ✅ 표준화
    scaler = StandardScaler()
    X = scaler.fit_transform(df_selected)

    # ✅ 클러스터링
    kmeans = KMeans(n_clusters=5, random_state=42)
    df['cluster'] = kmeans.fit_predict(X)

    # ✅ 클러스터링 결과 저장
    result_path = os.path.join(SAVE_DIR, f'{name_without_ext}_클러스터링.csv')
    df.to_csv(result_path, index=False, encoding='utf-8-sig')
    print(f"📁 저장 완료: {result_path}")
