from app.agents.emotion_agent import EmotionAnalysisAgent


def test_positive_message_scores_positive_valence():
    agent = EmotionAnalysisAgent()
    result = agent.analyze("I feel really happy and grateful today")
    assert result.valence > 0
    assert result.primary_emotion == "positive"


def test_negative_message_scores_negative_valence():
    agent = EmotionAnalysisAgent()
    result = agent.analyze("I feel so hopeless and exhausted and alone")
    assert result.valence < 0
    assert result.primary_emotion == "negative"


def test_neutral_message_scores_near_zero():
    agent = EmotionAnalysisAgent()
    result = agent.analyze("The meeting is scheduled for 3pm tomorrow")
    assert result.primary_emotion == "neutral"


def test_deviation_from_baseline_increases_with_distance():
    agent = EmotionAnalysisAgent()
    result = agent.analyze("I feel hopeless and empty", baseline_valence=0.8)
    assert result.deviation_from_baseline > 0.5
