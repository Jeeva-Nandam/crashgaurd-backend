def revenue_trend(revenue):
    if len(revenue) < 4: # actully it is 6
        return 0, "Insufficient Data"

    # last 3 months average
    ma_current = sum(revenue[-3:]) / 3
    ma_previous = sum(revenue[-6:-3]) / 3

    if ma_previous == 0:
        return 0, "Stable"

    trend = ((ma_current - ma_previous) / ma_previous) * 100

    if trend > 5:
        label = "Growing"
    elif trend < -5:
        label = "Declining"
    else:
        label = "Stable"

    return round(trend, 2), label


def expense_trend(expenses):
    if len(expenses) < 4:
        return 0, "Insufficient Data"

    current = expenses[-1]
    previous = expenses[-4]

    if previous == 0:
        return 0, "Stable"

    trend = ((current - previous) / previous) * 100

    if trend > 5:
        label = "Rising"
    elif trend < -5:
        label = "Reducing"
    else:
        label = "Stable"

    return round(trend, 2), label


def net_cash_flow(revenue, expenses):
    return [r - e for r, e in zip(revenue, expenses)]


def burn_rate(revenue, expenses):
    losses = [e - r for r, e in zip(revenue, expenses) if e > r]
    if not losses:
        return 0
    return round(sum(losses) / len(losses), 2)


def runway_analysis(cash_on_hand, burn_rate):
    if burn_rate <= 0:
        return None, "Profitable"

    # burn_rate is monthly
    months = cash_on_hand / burn_rate

    # convert months → days
    days = months * 30

    if days < 90:
        status = "Critical"
    elif days < 180:
        status = "High Risk"
    elif days < 365:
        status = "Moderate"
    else:
        status = "Healthy"

    return round(days, 0), status

#churn rate
def calculate_churn_rate(customers):
    churn_rates = []

    for i in range(1, len(customers)):
        previous = customers[i - 1]
        current = customers[i]

        if previous == 0:
            churn_rates.append(0)
        else:
            lost = max(previous - current, 0)
            churn = (lost / previous) * 100
            churn_rates.append(round(churn, 2))

    return churn_rates