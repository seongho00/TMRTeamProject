from flask import Flask, request, jsonify, Response
import json

app = Flask(__name__)

# ✨ 간단한 intent 분류 함수 (추후 TensorFlow로 대체 가능)
def predict_intent(text):
    text = text.lower()
    if "매출" in text:
        return "매출_조회"
    elif "인구" in text:
        return "인구_조회"
    elif "위험" in text or "폐업" in text:
        return "상권_위험도"
    else:
        return "기타"

@app.route("/predict", methods=["GET"])
def predict():
    # 📌 GET 방식에서는 URL 쿼리 파라미터에서 값 가져오기
    question = request.args.get("text", "")

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    intent = predict_intent(question)

    # 👇 한글을 유니코드로 인코딩하지 않도록
    return Response(
        json.dumps({"intent": intent}, ensure_ascii=False),
        content_type="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)