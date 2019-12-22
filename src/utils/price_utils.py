import logging


def adjusted_price_from_tuple(t):
    return adjusted_price(t[0],t[1],t[2])


def adjusted_price(rp,wp,pp):
    profit = rp - wp
    agent_profit = float(profit * pp) / 100
    company_profit = float(profit * (100 - pp)) / 100
    modified_price = wp + company_profit
    return modified_price


#print adjusted_price_from_tuple((15,10,10))