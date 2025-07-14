from flask import Flask, request, jsonify, Response
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
import numpy as np
import pickle

app = Flask(__name__)

# intent label 목록
intent_labels = ["매출_조회", "인구_조회", "상권_위험도", "기타"]

# 모델 및 tokenizer 로드
model = tf.keras.models.load_model("intent_model.h5")

# tokenizer도 저장/불러오기 해야 함 (여기선 코드상 재생성)
tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=1000, oov_token="<OOV>")
tokenizer.fit_on_texts([
    "대전 유성구 매출 알려줘",
    "2023년 인구 수 알려줘",
    "폐업 위험이 높은 지역 알려줘",
    "안녕"
])

def predict_intent(text):
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=10, padding='post')  # maxlen은 학습 때와 동일
    pred = model.predict(padded)
    class_idx = np.argmax(pred)
    return intent_labels[class_idx]

@app.route("/predict", methods=["GET"])
def predict():
    # 📌 GET 방식에서는 URL 쿼리 파라미터에서 값 가져오기
    question = request.args.get("text", "")

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    intent = predict_intent(question)
    if intent == "unknown":
        return jsonify({"answer": "죄송합니다. 해당 질문은 아직 지원하지 않습니다."})


    # 👇 한글을 유니코드로 인코딩하지 않도록
    return Response(
        json.dumps({"intent": intent}, ensure_ascii=False),
        content_type="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)