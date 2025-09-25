# ============================================
# 한글 폰트 설정 + 상관 계수 계산 + 산점도 그리기
# (Windows 폰트 경로 기준: Malgun Gothic)
# ============================================
import os
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from scipy.stats import pearsonr

from CorrelationAnalyzer.RandomForest import correlation_features, df_train_feat


# 0) 한글 폰트 설정 (경고: DejaVu Sans에서 한글 글리프 누락 해결)
def setup_korean_font():
    # 마이너스 기호가 네모로 보이지 않게 설정
    rcParams["axes.unicode_minus"] = False

    system = platform.system()
    added = False

    if system == "Windows":
        # Windows 기본 한글 폰트: Malgun Gothic
        candidates = [
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\malgunsl.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
            r"C:\Windows\Fonts\batang.ttc",
        ]
        for fp in candidates:
            if os.path.exists(fp):
                try:
                    font_manager.fontManager.addfont(fp)
                    added = True
                except Exception:
                    pass
        rcParams["font.family"] = "Malgun Gothic" if added else "Segoe UI"
    elif system == "Darwin":
        # macOS
        mac_candidates = [
            "/System/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        ]
        for fp in mac_candidates:
            if os.path.exists(fp):
                try:
                    font_manager.fontManager.addfont(fp)
                    added = True
                except Exception:
                    pass
        rcParams["font.family"] = "AppleGothic" if added else "Arial"
    else:
        # Linux (나눔/Noto가 설치되어 있으면 사용)
        linux_candidates = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        ]
        for fp in linux_candidates:
            if os.path.exists(fp):
                try:
                    font_manager.fontManager.addfont(fp)
                    added = True
                except Exception:
                    pass
        rcParams["font.family"] = "NanumGothic" if added else "DejaVu Sans"

setup_korean_font()

# ============================================
# 1) 타깃과 피처 준비
#    - df_train_feat, correlation_features 가 이미 메모리에 있다고 가정
# ============================================
target = '당월_매출_금액'
feats = [c for c in correlation_features if c in df_train_feat.columns] + [target]
feats = list(dict.fromkeys(feats))  # 중복 제거

# 숫자화 및 결측 처리
sub = df_train_feat[feats].copy()
for c in feats:
    sub[c] = pd.to_numeric(sub[c], errors='coerce')
sub = sub.dropna(subset=[target])

# ============================================
# 2) 타깃 대비 피어슨 상관계수 계산
# ============================================
corr_series = sub.corr(numeric_only=True)[target].drop(labels=[target], errors='ignore').dropna()

# 절대값 기준 상위 N개 피처 선택(부호는 유지)
TOP_N = 6
top_features = corr_series.abs().sort_values(ascending=False).head(TOP_N).index.tolist()

# 상위 30개 출력(선택)
print("=== 타깃('{}') 대비 상관계수 TOP 30 (부호 유지) ===".format(target))
print(
    corr_series.loc[
        corr_series.abs().sort_values(ascending=False).head(30).index
    ].sort_values(key=lambda s: s.abs(), ascending=False)
)

cols = min(3, len(top_features))  # 한 행에 최대 3개
rows = int(np.ceil(len(top_features) / cols))
plt.figure(figsize=(6 * cols, 4 * rows))

for i, f in enumerate(top_features, 1):
    tmp = sub[[f, target]].dropna()
    x = tmp[f].values
    y = tmp[target].values

    # 피어슨 r, p-value 계산
    try:
        r, p = pearsonr(x, y)
    except Exception:
        r, p = np.nan, np.nan

    ax = plt.subplot(rows, cols, i)
    ax.scatter(x, y, s=8, alpha=0.5)
    ax.set_xlabel(f)            # 한글 컬럼명 표시
    ax.set_ylabel(target)       # 한글 타깃명 표시
    ax.set_title(f"{f} vs {target}\nPearson r={r:.3f}, p={p:.3g}")

plt.tight_layout()
plt.show()
