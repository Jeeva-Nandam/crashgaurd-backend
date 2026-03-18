def generate_explanation(signals):
    sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)

    mapping = {
        "revenue_risk": "continuous revenue decline",
        "expense_risk": "expenses rising faster than revenue",
        "churn_risk": "increasing customer churn",
        "runway_risk": "short cash runway"
    }

    reasons = []
    for signal, _ in sorted_signals[:2]:
        reasons.append(mapping[signal])

    return "Crash risk is primarily driven by " + " and ".join(reasons) + "."


def decision_recommendations(signals):
    recs = []

    if signals["revenue_risk"] >= 60:
        recs.append("Increase revenue through upsells, pricing optimization, or prepaid plans.")

    if signals["churn_risk"] >= 60:
        recs.append("Improve retention by enhancing product value and customer engagement.")

    if signals["expense_risk"] >= 60:
        recs.append("Control expense growth and eliminate non-essential spending.")

    if signals["runway_risk"] >= 70:
        recs.append("Extend runway by reducing burn rate or raising additional capital.")

    if not recs:
        recs.append("Maintain current growth trajectory but monitor metrics monthly.")

    return recs


def improvement_projection(cash_in_hand, revenue, expenses):
    current_burn = expenses[-1] - revenue[-1]

    if current_burn <= 0:
        return "Company is already profitable. Focus on scaling."

    improved_revenue = revenue[-1] * 1.15
    reduced_expense = expenses[-1] * 0.90

    new_burn = reduced_expense - improved_revenue

    if new_burn <= 0:
        return "With 15% revenue growth and 10% cost reduction, the company becomes profitable."

    current_runway = cash_in_hand / current_burn
    new_runway = cash_in_hand / new_burn

    extension = new_runway - current_runway

    return f"Strategic improvements can extend runway by approximately {round(extension,1)} months."