import random


def get_slots(intent_request):
    return intent_request["sessionState"]["intent"]["slots"]


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        return slots[slotName]["value"]["interpretedValue"]
    else:
        return None


def get_none_slot_list(d):
    return [k for k, v in d.items() if v is None]


def get_session_attributes(intent_request):
    sessionState = intent_request["sessionState"]
    if "sessionAttributes" in sessionState:
        return sessionState["sessionAttributes"]
    return {}


def elicit_slot(intent_request, session_attributes, slot):
    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "slot",
                    "contextAttributes": {"last": slot},
                    "timeToLive": {"timeToLiveInSeconds": 20, "turnsToLive": 20},
                }
            ],
            "dialogAction": {"slotToElicit": slot, "type": "ElicitSlot"},
            "intent": {
                "name": intent_request["sessionState"]["intent"]["name"],
                "slots": intent_request["sessionState"]["intent"]["slots"],
            },
            "sessionAttributes": session_attributes,
        },
        # 'messages': [ message ] if message != None else None, ### ユーザーへの応答はLEXに委譲
        "requestAttributes": intent_request["requestAttributes"]
        if "requestAttributes" in intent_request
        else None,
    }


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request["sessionState"]["intent"]["state"] = fulfillment_state
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {"type": "Close"},
            "intent": intent_request["sessionState"]["intent"],
        },
        "messages": [message],
        "sessionId": intent_request["sessionId"],
        "requestAttributes": intent_request["requestAttributes"]
        if "requestAttributes" in intent_request
        else None,
    }


def lambda_handler(event, context):
    print(event)
    # 何の段か（インテント名）を取得
    intent_name = event["sessionState"]["intent"]["name"]
    slots = get_slots(event)
    none_list = get_none_slot_list(slots)

    if none_list != []:  # Noneのslotがまだ残っている場合（Initialize or validation）、ランダムで出題する
        slot = random.choice(none_list)
        # initialだったら、slotをランダムに選択して、Lexに聞いてもらう
        session_attributes = get_session_attributes(event)
        return elicit_slot(event, session_attributes, slot)
    else:
        # Nullのスロットがない（fulfilled）場合、集計スクリプト
        text = ""
        n_correct = 0
        for i in range(1, len(get_slots(event)) + 1):
            # ユーザー解答を取得
            ans = int(get_slot(event, str(intent_name) + str(i)))
            if int(intent_name) * i == ans:  # 正解
                text = text + f"{intent_name} かける {i} は {ans} ◯ <br/>"
                n_correct += 1
            else:  # 不正解
                text = (
                    text
                    + f"{intent_name} かける {i} は {ans} × せいかいは{int(intent_name) * i} <br/>"
                )
        text = f"せいかいは {n_correct} こでした！！！！！ <br/>" + text

        message = {"contentType": "CustomPayload", "content": text}
        fulfillment_state = "Fulfilled"
        session_attributes = get_session_attributes(event)
        return close(event, session_attributes, fulfillment_state, message)
