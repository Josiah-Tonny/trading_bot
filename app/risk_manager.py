def calculate_position_size(
    capital: float, entry: float, stop_loss: float, risk_percent: float = 1
) -> dict:
    """
    Calculate position size based on risk management.
    Returns a dict with 'position_size' and possibly 'risk_amount'.
    """
    risk_amount = capital * (risk_percent / 100)
    stop_loss_distance = abs(entry - stop_loss)
    if stop_loss_distance == 0:
        return {'position_size': 0, 'risk_amount': risk_amount}
    position_size = risk_amount / stop_loss_distance
    return {'position_size': position_size, 'risk_amount': risk_amount}