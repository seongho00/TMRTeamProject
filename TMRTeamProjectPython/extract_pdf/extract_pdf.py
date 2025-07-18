import pdfplumber
import pandas as pd

# PDF 파일 열기
with pdfplumber.open("C:\\Users\\admin\\Desktop\\간단분석리포트.pdf") as pdf:
    lines = []  # 줄 단위 저장
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            for line in text.split("\n"):
                lines.append([line])  # 리스트로 저장

# DataFrame으로 변환
df = pd.DataFrame(lines, columns=["내용"])

# CSV로 저장
df.to_csv("전체_텍스트_라인별.csv", index=False, encoding='utf-8-sig')

print("✅ PDF 전체 텍스트 → CSV 변환 완료")
