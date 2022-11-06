def get_slots(intent_request):
    return intent_request["sessionState"]["intent"]["slots"]


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        return slots[slotName]["value"]["interpretedValue"]
    else:
        return None


def get_session_attributes(intent_request):
    sessionState = intent_request["sessionState"]
    if "sessionAttributes" in sessionState:
        return sessionState["sessionAttributes"]
    return {}


def lambda_handler(event, context):
    print(f"イベント：{event}")
    intent = event["sessionState"]["intent"]["name"]
    slots = get_slots(event)
    session_attributes = get_session_attributes(event)
    print(f"セッション属性:{session_attributes}")
    print(event["invocationSource"])
    print(f"インテント名: {intent}")
    if intent == "welcome":
        user_name = get_slot(event, "user_name")
        if user_name is not None:
            print("elicit intent")
            response = {
                "sessionState": {
                    "dialogAction": {"type": "ElicitIntent"},  # intent待機状態に
                    "intent": {"name": "welcome", "slots": slots},
                    "sessionAttributes": {"user_name": user_name},
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": f"こんにちは！　{user_name}さん。ご要件はなんですか？",
                    }
                ],
            }

        else:
            print("Delegate!!")
            response = {
                "sessionState": {
                    "dialogAction": {"type": "Delegate"},  # lexに委譲（質問し直す）
                    "sessionAttributes": session_attributes,
                }
            }
        return response
    elif intent == "reserve_book":
        book_genre = get_slot(event, "book_genre")
        print(f"book genre is {book_genre}")
        book_genre_country = get_slot(event, "book_genre_country")
        book_genre_origin = get_slot(event, "book_genre_origin")
        book_name = get_slot(event, "book_name")
        is_confirmed = (
            event["sessionState"]["intent"]["confirmationState"] == "Confirmed"
        )
        if book_name is not None and is_confirmed is True:
            print("accept confirmation!")
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},  # 会話終了
                    "intent": {"name": "reserve_book", "state": "Fulfilled"},
                    "sessionAttributes": session_attributes,
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": f"ありがとうございました！ {session_attributes['user_name']}さん!",
                    }
                ],
            }
        elif book_name is not None and is_confirmed is False:
            print("send confirmation!")
            return {
                "sessionState": {
                    "dialogAction": {"type": "ConfirmIntent"},  # 確認させる
                    "intent": {
                        "name": "reserve_book",
                        "state": "InProgress",
                        "slots": slots,
                    },
                    "sessionAttributes": session_attributes,
                }
            }
        if book_genre is None:
            print("ジャンル選択")
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",  # 質問させる
                        "slotToElicit": "book_genre",
                    },
                    "intent": {
                        "name": "reserve_book",
                        "state": "InProgress",
                        "slots": slots,
                    },
                    "sessionAttributes": session_attributes,
                },
                "messages": [
                    {
                        "contentType": "ImageResponseCard",
                        "imageResponseCard": {
                            "title": "ジャンルを選択してください",
                            "imageUrl": "https://w7.pngwing.com/pngs/392/371/png-transparent-book-library-five-flat-books-angle-text-comic-book.png",
                            "buttons": [
                                {"text": "フィクション", "value": "フィクション"},
                                {"text": "ノンフィクション", "value": "ノンフィクション"},
                            ],
                        },
                    }
                ],
            }
        if (book_genre_country is not None) or (book_genre_origin is not None):
            print("elicit book_name!!!")
            return {
                "sessionState": {
                    "dialogAction": {"type": "ElicitSlot", "slotToElicit": "book_name"},
                    "intent": {
                        "name": "reserve_book",
                        "state": "InProgress",
                        "slots": slots,
                    },
                    "sessionAttributes": session_attributes,
                }
            }
        elif book_genre == "フィクション":
            print("elicit book_genre_country!!")
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "book_genre_country",
                    },
                    "intent": {
                        "name": "reserve_book",
                        "state": "InProgress",
                        "slots": slots,
                    },
                    "sessionAttributes": session_attributes,
                }
            }
        elif book_genre == "ノンフィクション":
            print("elicit book_genre_origin!!")
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "book_genre_origin",
                    },
                    "intent": {
                        "name": "reserve_book",
                        "state": "InProgress",
                        "slots": slots,
                    },
                    "sessionAttributes": session_attributes,
                }
            }
        print("delegate !!")
        return {
            "sessionState": {
                "dialogAction": {"type": "Delegate"},
                "intent": {"name": "reserve_book", "slots": slots},
                "sessionAttributes": session_attributes,
            }
        }

    raise Exception("Intent with name " + intent + " not supported")
