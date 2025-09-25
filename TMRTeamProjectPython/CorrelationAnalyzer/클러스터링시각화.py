# =========================================================
# 클러스터링 부분만 분리해서 시각화 (PCA 2D/3D)하는 스크립트
# - 네가 올린 코드의 파일/경로/selected_features를 그대로 사용
# - 군집(k=5)만 계산해서 산점도로 저장
# - seaborn 없이 matplotlib만 사용
# - 필요 시 한글 폰트 경로를 주석대로 설정
# =========================================================
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# ==========================
# 프로젝트 경로/파일 설정
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "src", "main", "resources", "seoul_data_merge")
)

TRAIN_FILES = [
    "서울_데이터_병합_20221.csv",
    "서울_데이터_병합_20222.csv",
    "서울_데이터_병합_20223.csv",
    "서울_데이터_병합_20224.csv",
    "서울_데이터_병합_20231.csv",
    "서울_데이터_병합_20232.csv",
    "서울_데이터_병합_20233.csv",
    "서울_데이터_병합_20234.csv",
    "서울_데이터_병합_20241.csv",
    "서울_데이터_병합_20242.csv",
    "서울_데이터_병합_20243.csv",
    "서울_데이터_병합_20244.csv"
]
TEST_FILE = "서울_데이터_병합_20251.csv"

# ==========================
# 클러스터링에 쓸 피처 목록
# ==========================
selected_features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_금액',
    '지하철_역_수', '대학교_수', '관공서_수'
]

# ==========================
# 유틸 함수
# ==========================
def read_csv_any(path: str) -> pd.DataFrame:
    # UTF-8 우선, 실패 시 CP949 시도
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")

def unify_columns(df: pd.DataFrame) -> pd.DataFrame:
    # 컬럼 공백 제거 및 중복 제거
    df = df.rename(columns=lambda c: str(c).strip())
    return df.loc[:, ~df.columns.duplicated()].copy()

def load_train_test(train_files, test_file) -> tuple[pd.DataFrame, pd.DataFrame]:
    # 학습/테스트 로드
    train_list = []
    for fn in train_files:
        p = os.path.join(DATA_DIR, fn)
        if os.path.exists(p):
            train_list.append(read_csv_any(p))
    if not train_list:
        raise FileNotFoundError("학습용 CSV(20221~20244)가 없습니다.")

    test_path = os.path.join(DATA_DIR, test_file)
    if not os.path.exists(test_path):
        raise FileNotFoundError("테스트 CSV(20251)가 없습니다.")

    df_train = unify_columns(pd.concat(train_list, ignore_index=True))
    df_test  = unify_columns(read_csv_any(test_path))
    return df_train, df_test

def build_cluster_labels(df_train: pd.DataFrame, df_test: pd.DataFrame, feats: list, n_clusters=5, random_state=42):
    # 공통 피처만 사용
    feats = [c for c in feats if c in df_train.columns and c in df_test.columns]
    if not feats:
        raise ValueError("클러스터링에 사용할 공통 피처가 없습니다.")

    # 결측/무한 처리
    for d in (df_train, df_test):
        d[feats] = d[feats].replace([np.inf, -np.inf], np.nan).fillna(0)

    # 스케일링
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(df_train[feats].values)
    Xte = scaler.transform(df_test[feats].values)

    # 표본 부족 시 단일 클러스터
    if Xtr.shape[0] < n_clusters:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test, feats, scaler

    # KMeans
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df_train = df_train.copy()
    df_test  = df_test.copy()
    df_train['cluster'] = km.fit_predict(Xtr)
    df_test['cluster']  = km.predict(Xte)
    return df_train, df_test, feats, scaler

def pca_transform(X: np.ndarray, n_components=2, random_state=42):
    # PCA 변환
    pca = PCA(n_components=n_components, random_state=random_state)
    Z = pca.fit_transform(X)
    evr = pca.explained_variance_ratio_
    return Z, evr

# 한글 폰트가 깨질 경우에만 사용(환경에 맞게 경로 수정)
# import matplotlib.font_manager as fm
# font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
# if os.path.exists(font_path):
#     fm.fontManager.addfont(font_path)
#     plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

def plot_clusters_2d(X2: np.ndarray, labels: np.ndarray, evr: np.ndarray, title: str, save_path: str | None = None, alpha=0.7):
    # 2D 산점도
    plt.figure(figsize=(8, 6))
    uniq = np.unique(labels)
    for k in uniq:
        m = labels == k
        plt.scatter(X2[m, 0], X2[m, 1], s=18, alpha=alpha, label=f"cluster {int(k)}")

    plt.xlabel(f"PC1 ({evr[0]*100:.1f}%)")
    plt.ylabel(f"PC2 ({evr[1]*100:.1f}%)")
    plt.title(title)
    plt.legend(loc="best", frameon=False)
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_clusters_3d(X3: np.ndarray, labels: np.ndarray, evr: np.ndarray, title: str, save_path: str | None = None, alpha=0.7, elev=22, azim=50):
    # 3D 산점도
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    uniq = np.unique(labels)
    for k in uniq:
        m = labels == k
        ax.scatter(X3[m, 0], X3[m, 1], X3[m, 2], s=14, alpha=alpha, label=f"cluster {int(k)}")

    ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)")
    ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)")
    ax.set_zlabel(f"PC3 ({evr[2]*100:.1f}%)")
    ax.view_init(elev=elev, azim=azim)
    plt.title(title)
    ax.legend(loc="best")

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

# ==========================
# 메인: 클러스터링만 수행하고 시각화 저장
# ==========================
if __name__ == "__main__":
    # 1) 데이터 로드
    df_train_raw, df_test_raw = load_train_test(TRAIN_FILES, TEST_FILE)

    # 2) 클러스터 라벨 생성
    df_train_clu, df_test_clu, feats_used, scaler = build_cluster_labels(
        df_train_raw, df_test_raw, selected_features, n_clusters=5, random_state=42
    )

    # 3) 시각화용 행렬 준비(Train/Test 각각)
    Xtr = scaler.transform(df_train_clu[feats_used].replace([np.inf, -np.inf], np.nan).fillna(0).values)
    Xte = scaler.transform(df_test_clu[feats_used].replace([np.inf, -np.inf], np.nan).fillna(0).values)
    ytr = df_train_clu['cluster'].astype(int).values
    yte = df_test_clu['cluster'].astype(int).values

    # 4) PCA 2D
    Xtr_2d, evr2_tr = pca_transform(Xtr, n_components=2, random_state=42)
    Xte_2d, evr2_te = pca_transform(Xte, n_components=2, random_state=42)

    # 5) PCA 3D
    Xtr_3d, evr3_tr = pca_transform(Xtr, n_components=3, random_state=42)
    Xte_3d, evr3_te = pca_transform(Xte, n_components=3, random_state=42)

    # 6) 저장 경로
    out_dir = os.path.join(BASE_DIR, "plots")
    os.makedirs(out_dir, exist_ok=True)

    # 7) 그리기/저장
    plot_clusters_2d(Xtr_2d, ytr, evr2_tr, title="Train Clusters (PCA 2D)", save_path=os.path.join(out_dir, "train_clusters_2d.png"))
    plot_clusters_2d(Xte_2d, yte, evr2_te, title="Test Clusters (PCA 2D)",  save_path=os.path.join(out_dir, "test_clusters_2d.png"))

    plot_clusters_3d(Xtr_3d, ytr, evr3_tr, title="Train Clusters (PCA 3D)", save_path=os.path.join(out_dir, "train_clusters_3d.png"))
    plot_clusters_3d(Xte_3d, yte, evr3_te, title="Test Clusters (PCA 3D)",  save_path=os.path.join(out_dir, "test_clusters_3d.png"))

    # 8) 요약 출력
    print(f"[OK] 클러스터링 시각화 저장 완료 → {out_dir}")
    print(f"- 사용 피처 개수: {len(feats_used)}")
    print(f"- Train 표본 수: {len(df_train_clu)}, Test 표본 수: {len(df_test_clu)}")
