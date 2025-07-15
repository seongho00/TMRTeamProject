import spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding




nlp = spacy.blank("ko")  # 빈 모델
ner = nlp.add_pipe("ner")

# 라벨 등록
ner.add_label("CITY")
ner.add_label("DISTRICT")
ner.add_label("AGE")
ner.add_label("GENDER")

# 학습 시작
optimizer = nlp.begin_training()
for i in range(10):
    for text, annotations in TRAIN_DATA:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        nlp.update([example], sgd=optimizer)