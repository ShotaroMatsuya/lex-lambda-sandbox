import json
import logging
import os
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """
    try:
        return func()
    except KeyError:
        return None


def build_validation_result(is_valid, violated_slot, message_content):
    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


def validate_value(location, check_in_date, nights, room_type):
    valid_cities = ["東京", "大阪", "北海道", "沖縄"]

    if not location:
        return build_validation_result(False, "Location", "地区を入力してください")

    if location.lower() not in valid_cities:
        return build_validation_result(
            False,
            "Location",
            "現在滞在可能な地区は {} のみとなっています。".format(", ".join(valid_cities)),
        )

    if not check_in_date:
        return build_validation_result(False, "CheckInDate", "チェックイン日時を教えて下さい")

    if not nights:
        return build_validation_result(False, "Nights", "何泊しますか？")

    if not room_type:
        return build_validation_result(False, "RoomType", "部屋の種別を教えて下さい。")

    return build_validation_result(True, None, None)


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


def elicit_slot(
    intent_request,
    session_attributes,
    intent_name,
    slots,
    slot_to_elicit,
    message,
    response_card,
):
    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "slot",
                    "contextAttributes": {"last": slot_to_elicit},
                    "timeToLive": {"timeToLiveInSeconds": 20, "turnsToLive": 20},
                }
            ],
            "dialogAction": {"slotToElicit": slot_to_elicit, "type": "ElicitSlot"},
            "intent": {
                "name": intent_name,
                "slots": slots,
            },
            "sessionAttributes": session_attributes,
        },
        "messages": [response_card] if response_card is not None else [message],
        "requestAttributes": intent_request["requestAttributes"]
        if "requestAttributes" in intent_request
        else None,
    }


def confirm_intent(
    intent_request, session_attributes, intent_name, slots, message, response_card
):
    return {
        "sessionState": {
            "dialogAction": {"type": "ConfirmIntent"},
            "intent": {
                "name": intent_name,
                "slots": slots,
            },
            "sessionAttributes": session_attributes,
        },
        "messages": [response_card] if response_card is not None else [message],
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


def delegate(session_attributes, intent_name, slots):
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {"type": "Delegate"},
            "intent": {"name": intent_name, "slots": slots},
        }
    }


def build_response_card(title, subtitle, options):
    buttons = None
    if options is not None:
        buttons = []
        for i in range(min(5, len(options))):
            buttons.append(options[i])

    return {
        "contentType": "ImageResponseCard",
        "content": "一つ選択してください",
        "imageResponseCard": {"title": title, "subtitle": subtitle, "buttons": buttons},
    }


def build_options(slot):
    if slot == "Location":
        return [
            {"text": "東京（TOKYO）", "value": "東京"},
            {"text": "大阪 (OSAKA)", "value": "大阪"},
            {"text": "北海道 (Hokkaido)", "value": "北海道"},
            {"text": "沖縄（Okinawa）", "value": "沖縄"},
        ]
    elif slot == "Nights":
        return [
            {"text": "3泊4日", "value": 3},
            {"text": "5泊6日", "value": 5},
            {"text": "7泊8日", "value": 7},
        ]
    elif slot == "RoomType":
        return [
            {"text": "King", "value": "キング"},
            {"text": "Queen", "value": "クイーン"},
            {"text": "Deluxe", "value": "デラックス"},
        ]


def book_hotel(intent_request):
    slots = get_slots(intent_request)
    location = get_slot(intent_request, "Location")
    check_in_date = get_slot(intent_request, "CheckInDate")
    nights = get_slot(intent_request, "Nights")
    room_type = get_slot(intent_request, "RoomType")
    source = intent_request["invocationSource"]
    output_session_attributes = get_session_attributes(intent_request)

    booking_map = json.loads(
        try_ex(lambda: output_session_attributes["bookingMap"]) or "{}"
    )
    print(booking_map)
    print(source)
    if source == "DialogCodeHook":
        print("case 0")
        validation_result = validate_value(location, check_in_date, nights, room_type)
        print("validation_result; {}".format(validation_result))
        if not validation_result["isValid"]:
            print("case1")
            slots[validation_result["violatedSlot"]] = None
            response = elicit_slot(
                intent_request,
                output_session_attributes,
                intent_request["sessionState"]["intent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
                build_response_card(
                    "{}を選んでください。".format(validation_result["violatedSlot"]),
                    validation_result["message"]["content"],
                    build_options(validation_result["violatedSlot"]),
                ),
            )
            return response

        if not location:
            print("case 2")
            return elicit_slot(
                intent_request,
                output_session_attributes,
                intent_request["sessionState"]["intent"]["name"],
                intent_request["currentIntent"]["slots"],
                "Location",
                {
                    "contentType": "PlainText",
                    "content": "どの地区での滞在を希望しますか？",
                },
                build_response_card(
                    "地区",
                    "どの地区での滞在を希望しますか？",
                    build_options("Location"),
                ),
            )
        if location and not check_in_date:
            return delegate(
                output_session_attributes,
                intent_request["sessionState"]["intent"]["name"],
                slots,
            )

        if location and check_in_date and not nights:
            return elicit_slot(
                intent_request,
                output_session_attributes,
                intent_request["sessionState"]["intent"]["name"],
                intent_request["currentIntent"]["slots"],
                "Nights",
                {
                    "contentType": "PlainText",
                    "content": "何泊滞在したいですか？",
                },
                build_response_card(
                    "滞在期間",
                    "何泊滞在したいですか？",
                    build_options("Nights"),
                ),
            )
        if location and check_in_date and nights and not room_type:
            return elicit_slot(
                intent_request,
                output_session_attributes,
                intent_request["sessionState"]["intent"]["name"],
                intent_request["currentIntent"]["slots"],
                "RoomType",
                {
                    "contentType": "PlainText",
                    "content": "部屋の種別を選んでください",
                },
                build_response_card(
                    "部屋種別",
                    "部屋の種別を選んでください",
                    build_options("RoomType"),
                ),
            )
        return delegate(
            output_session_attributes,
            intent_request["sessionState"]["intent"]["name"],
            slots,
        )
    elif source == "FulfillmentCodeHook":
        hotel_map = {
            "location": location,
            "nights": nights,
            "room_type": room_type,
            "check_in_date": check_in_date,
        }
        output_session_attributes["BookHotel"] = json.dumps(hotel_map)
        return close(
            intent_request,
            output_session_attributes,
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "ありがとうございました。あなたの予約を受け付けました。<br/>場所：{}ホテル、 チェックイン:{}、 滞在期間：{}、部屋種別：{}".format(
                    location, check_in_date, nights, room_type
                ),
            },
        )


def dispatch(intent_request):
    logger.debug(
        "dispatch sessionId={}, intentName={}".format(
            intent_request["sessionId"],
            intent_request["sessionState"]["intent"]["name"],
        )
    )

    intent_name = intent_request["sessionState"]["intent"]["name"]

    # Dispatch to your bot's intent handlers
    if intent_name == "BookHotel":
        return book_hotel(intent_request)
    raise Exception("Intent with name " + intent_name + " not supported")


def lambda_handler(event, context):
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    logger.debug("event.bot.name={}".format(event["bot"]["name"]))
    logger.debug("event: {}".format(event))

    return dispatch(event)
