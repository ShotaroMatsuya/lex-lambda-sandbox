def validate(slots):

    valid_cities = ["東京", "大阪", "北海道", "沖縄"]

    if not slots["Location"]:
        print("Inside Empty Location")
        return {"isValid": False, "violatedSlot": "Location"}

    if slots["Location"]["value"]["originalValue"].lower() not in valid_cities:

        print("Not Valide location")

        return {
            "isValid": False,
            "violatedSlot": "Location",
            "message": "現在滞在可能な地区は {} のみとなっています。".format(", ".join(valid_cities)),
        }

    if not slots["CheckInDate"]:

        return {
            "isValid": False,
            "violatedSlot": "CheckInDate",
        }

    if not slots["Nights"]:
        return {"isValid": False, "violatedSlot": "Nights"}

    if not slots["RoomType"]:
        return {"isValid": False, "violatedSlot": "RoomType"}

    return {"isValid": True}


def lambda_handler(event, context):
    slots = event["sessionState"]["intent"]["slots"]
    intent = event["sessionState"]["intent"]["name"]
    print(event["invocationSource"])
    print(slots)
    print(intent)

    print(event)
    validation_result = validate(slots)

    if event["invocationSource"] == "DialogCodeHook":
        if not validation_result["isValid"]:
            if "message" in validation_result:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": validation_result["violatedSlot"],
                            "type": "ElicitSlot",
                        },
                        "intent": {"name": intent, "slots": slots},
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": validation_result["message"],
                        }
                    ],
                }
            else:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": validation_result["violatedSlot"],
                            "type": "ElicitSlot",
                        },
                        "intent": {"name": intent, "slots": slots},
                    }
                }
        else:
            response = {
                "sessionState": {
                    "dialogAction": {"type": "Delegate"},
                    "intent": {"name": intent, "slots": slots},
                }
            }
    if event["invocationSource"] == "FulfillmentCodeHook":
        # Add order in Database
        print("fulfillment triggered")
        response = {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": intent, "slots": slots, "state": "Fulfilled"},
            },
            "messages": [
                {"contentType": "PlainText", "content": "ありがとうございました。あなたの予約を受け付けました。"}
            ],
        }

    return response
