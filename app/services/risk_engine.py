from datetime import datetime, timedelta

# def revenue_risk_score(growth):
#     avg_growth = sum(growth) / len(growth) if growth else 0
#     if avg_growth < -10:
#         return 90
#     elif -10 <= avg_growth <= 5:
#         return 55
#     else:
#         return 20
def revenue_risk_score(avg_growth):
    if avg_growth < -10:
        return 90
    elif -10 <= avg_growth <= 5:
        return 55
    else:
        return 20

def expense_risk_score(rev_growth, exp_growth):
    avg_rev = sum(rev_growth) / len(rev_growth) if rev_growth else 0
    avg_exp = sum(exp_growth) / len(exp_growth) if exp_growth else 0

    if avg_exp > avg_rev:
        return 85
    elif abs(avg_exp - avg_rev) < 3:
        return 45
    else:
        return 15


def runway_risk_score(runway_days):
    if runway_days is None:
        return 0

    months = runway_days / 30

    if months < 3:
        return 90
    elif months < 6:
        return 70
    elif months < 12:
        return 40
    else:
        return 10


def churn_risk_score(churn_rates):
    avg_churn = sum(churn_rates) / len(churn_rates)
    if avg_churn > 10:
        return 90
    elif 5 <= avg_churn <= 10:
        return 55
    else:
        return 20


def risk_label(score):
    if score < 40:
        return "LOW RISK"
    elif score < 70:
        return "MEDIUM RISK"
    return "HIGH RISK"


def predict_zero_cash_date(cash_in_hand, revenue, expenses):
    burn = expenses[-1] - revenue[-1]

    if burn <= 0:
        return None, "Company is currently profitable. No crash expected."

    runway_months = cash_in_hand / burn
    runway_days = int(runway_months * 30)

    crash_date = datetime.today() + timedelta(days=runway_days)

    return crash_date.strftime("%d %B %Y"), "Cash runway exhaustion due to continuous negative burn rate."