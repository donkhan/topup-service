import logging

uimap = {}
uimap['countryid'] = 'countryId'
uimap['operatorid'] = 'operatorId'
uimap['product_list'] = 'productList'
uimap['retail_price_list'] = 'retailPriceList'
uimap['wholesale_price_list'] = 'wholeSalePriceList'
uimap['destination_currency'] = 'destinationCurrency'
uimap['destination_msisdn'] = 'mobileNo'
uimap['service_fee_list'] = 'serviceFeeList'


def parse_property(content):
    lines = content.split("\r\n")
    dict={}
    for line in lines:
        pair=line.split("=")
        if len(pair) == 2:
            key = pair[0]
            if uimap.has_key(key):
                key = uimap[key]
            if pair[0].find("price_list") >= 0 or pair[0].find("fee_list") >= 0:
                dict[key] = map(float,pair[1].split(","))
            elif pair[0].find("product_list") >= 0:
                dict[key] = pair[1].split(",")
            else:
                dict[key] = pair[1]
    return dict