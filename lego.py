#!/usr/bin/python3

import re
import sys
import json
import requests

BASE_URL = "https://www.legombrinq.com.br/"
PRODUCT_SEARCH_URI = "api/catalog_system/pub/products/search/"
ITEM_SEARCH_URI = "api/checkout/pub/orderForms/simulation"

LEGO_CODE = sys.argv[1]

POSTAL_CODE = sys.argv[2]

lego_code_response = requests.get(BASE_URL+str(LEGO_CODE))
search_results = re.findall('productid="([0-9]+)"', lego_code_response.text)
if len(search_results) > 1:
    print("Produto não encontrado")
    exit()
else:
    product_id = int(search_results[0])

lego_product_search = requests.get(BASE_URL+PRODUCT_SEARCH_URI, params={"fq":"productId:{}".format(product_id)})
item_id = lego_product_search.json()[0]["items"][0]["itemId"]

payload = {"items":[{"id": item_id,"quantity": 1,"seller": 1}],"postalCode": "{}".format(POSTAL_CODE),"country": "BRA"}
lego_item_search = requests.post(BASE_URL+ITEM_SEARCH_URI, data=json.dumps(payload), headers={"Content-Type": "application/json"}).json()
slas = lego_item_search["logisticsInfo"][0]["slas"]

if len(slas) > 0:
    for sla in slas:
        channel = sla["deliveryChannel"]
        if channel == "delivery":
            print("Disponivel para envio em até {} dias úteis".format(re.search('([0-9]+)bd', sla["shippingEstimate"])[1]))
        elif channel == "pickup-in-point":
            store = sla["pickupStoreInfo"]
            address = "{}, {} - {} - CEP: {} {}/{}".format(store["address"]["street"], store["address"]["number"], store["address"]["neighborhood"], store["address"]["postalCode"], store["address"]["city"], store["address"]["state"])
            print("Disponivel para retirada na {}".format(store["friendlyName"]))
            print("https://www.google.com/maps/place/{}".format(address.replace(" ", "+")))

        print()
else:
    print("Produto indisponivel no CEP informado. Procurando em outras lojas LEGO...")
    with open("stores.json", "r") as lego_stores_file:
        lego_stores = json.load(lego_stores_file)
        stores = []
        for lego_store in lego_stores["stores"]:
            payload = {"items":[{"id": item_id,"quantity": 1,"seller": 1}],"postalCode": "{}".format(lego_store["address"]["postalCode"]),"country": "BRA"}
            lego_item_search = requests.post(BASE_URL+ITEM_SEARCH_URI, data=json.dumps(payload), headers={"Content-Type": "application/json"}).json()
            slas = lego_item_search["logisticsInfo"][0]["slas"]

            if len(slas) > 0:
                for sla in slas:
                    channel = sla["deliveryChannel"]
                    if channel == "pickup-in-point":
                        store = sla["pickupStoreInfo"]
                        stores.append(store)

        if len(stores) > 0:
            stores = list({store["friendlyName"]:store for store in stores}.values())
            for store in stores:
                address = "{}, {} - {} - CEP: {} {}/{}".format(store["address"]["street"], store["address"]["number"], store["address"]["neighborhood"], store["address"]["postalCode"], store["address"]["city"], store["address"]["state"])
                print("Disponivel para retirada na {}".format(store["friendlyName"]))
                print("https://www.google.com/maps/place/{}".format(address.replace(" ", "+")))
                print()

        else:
            print("Produto indisponivel")