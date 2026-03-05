def score_text(text):
    return "Human", 80.0from transformers import pipeline

# load AI detector model
detector = pipeline("text-classification",
                    model="roberta-base-openai-detector")

def score_text(text):
    result = detector(text)[0]

    if result["label"] == "Fake":
        ai_score = result["score"]
        human_score = 1 - ai_score
    else:
        human_score = result["score"]
        ai_score = 1 - human_score

    return {
        "ai_probability": round(ai_score * 100, 2),
        "human_probability": round(human_score * 100, 2)
    }