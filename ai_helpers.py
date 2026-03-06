def compute_performance_insight(score):
    """
    Returns a dictionary with label and risk for the given performance score.
    Replace this with a real ML model call for production.
    """
    if score >= 85:
        return {"label": "Excellent", "risk": "Low"}
    if score >= 70:
        return {"label": "Good", "risk": "Low"}
    if score >= 50:
        return {"label": "Fair", "risk": "Medium"}
    if score >= 40:
        return {"label": "Needs Attention", "risk": "High"}
    return {"label": "Critical", "risk": "Very High"}