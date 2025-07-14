from flask import Flask, request, jsonify, Response
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
import numpy as np
import pickle

app = Flask(__name__)

# intent label 목록 (기타 제거)
intent_labels = ["매출_조회", "인구_조회", "상권_위험도"]

# ✅ 모델 로드
model = tf.keras.models.load_model("intent_model.keras")

# ✅ tokenizer 로드
with open("tokenizer.pickle", "rb") as handle:
    tokenizer = pickle.load(handle)

# ✅ intent 예측 함수
def predict_intent(text, threshold=0.1):
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=10, padding='post')  # 학습 시 maxlen과 동일하게
    pred = model.predict(padded)
    confidence = float(np.max(pred))
    class_idx = int(np.argmax(pred))

    if confidence < threshold:
        return "지원하지 않는 서비스입니다.", confidence

    return intent_labels[class_idx], confidence

# ✅ Flask 라우팅
@app.route("/predict", methods=["GET"])
def predict():
    question = request.args.get("text", "")

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    intent, confidence = predict_intent(question)

    return Response(
        json.dumps({"intent": intent, "confidence": round(confidence, 4)}, ensure_ascii=False),
        content_type="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)