import perp.constants as constants

def calculate_profit(open, close):
    is_buy = 1 if open["side"] == constants.LONG else -1 

    return is_buy * (close["px"] - open["px"]) * open["sz"]