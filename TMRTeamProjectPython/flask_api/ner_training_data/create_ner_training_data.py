import json


def create_ner_training_data(sentences, locations, districts, ages, genders):
    training_data = []

    for sentence in sentences:
        entities = []

        for loc in locations:
            if loc in sentence:
                start = sentence.index(loc)
                end = start + len(loc)
                entities.append((start, end, "CITY"))

        for dist in districts:
            if dist in sentence:
                start = sentence.index(dist)
                end = start + len(dist)
                entities.append((start, end, "DISTRICT"))

        for age in ages:
            if age in sentence:
                start = sentence.index(age)
                end = start + len(age)
                entities.append((start, end, "AGE"))

        for gender in genders:
            if gender in sentence:
                start = sentence.index(gender)
                end = start + len(gender)
                entities.append((start, end, "GENDER"))

        training_data.append((sentence, {"entities": entities}))

    return training_data

# ✅ JSONL 파일 저장 함수
def save_ner_training_data_to_jsonl(training_data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for text, annot in training_data:
            json_line = {
                "text": text,
                "entities": [
                    {"start": start, "end": end, "label": label}
                    for (start, end, label) in annot["entities"]
                ]
            }
            f.write(json.dumps(json_line, ensure_ascii=False) + "\n")


locations = ["대전"]
districts = ["유성구", "대덕구", "중구", "서구", "동구"]
ages = ["10대", "20대", "30대", "40대", "50대", "60대"]
genders = ["남자", "여자", "남성", "여성"]

templates = [
    "{location} {district}의 {age} {gender} 유동인구 알려줘",
    "{district} {gender} 인구는?",
    "{age} {gender} 유동인구 수 궁금해",
    "이 지역 {age} {gender} 얼마나 있어?",
    "{district}에 거주하는 {age} {gender} 인구 수는?",
    "{location} {district} {age} {gender} 비율 알려줘",
    "{district}의 유동인구 중 {gender}는 얼마나 돼?",
    "{age}대 {gender} 얼마나 있어?",
    "{district} {age}대 {gender} 유동 인원 수 보여줘",
    "해당 지역 {age} {gender} 인구수 궁금해",
    "{age} {gender} 인구 얼마나 되지?",
    "{gender} 유동인구는?",
    "{district} 인구 현황"
]
sentences = []

for tmpl in templates:
    for location in locations:
        for district in districts:
            for age in ages:
                for gender in genders:
                    sentence = tmpl.format(location=location, district=district, age=age, gender=gender)
                    sentences.append(sentence)

print("생성 문장 수:", len(sentences))  # 수천 문장도 가능

training_data = create_ner_training_data(sentences, locations, districts, ages, genders)

save_ner_training_data_to_jsonl(training_data, "ner_training_data.jsonl")