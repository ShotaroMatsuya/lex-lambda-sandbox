import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def get_slots(intent_request):
    return intent_request["currentIntent"]["slots"]


def close(session_attributes, fulfillment_state, message):
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }
    return response


def ec2_start(intent_request):
    instance_id = get_slots(intent_request)["InstanceId"]
    ec2 = boto3.resource("ec2")
    response = ec2.Instance(instance_id).start()
    print(response)

    if (
        response["ResponseMetadata"]["HTTPStatusCode"] == 200
        and response["StartingInstances"][0]["CurrentState"]["Name"] == "pending"
    ):
        return close(
            intent_request["sessionAttributes"],
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "your Instance {} is successfully started".format(
                    instance_id
                ),
            },
        )
    else:
        return close(
            intent_request["sessionAttributes"],
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "I am unable to start the Instance {}".format(instance_id),
            },
        )


def ec2_stop(intent_request):
    instance_id = get_slots(intent_request)["InstanceId"]
    ec2 = boto3.resource("ec2")
    response = ec2.Instance(instance_id).stop()
    print(response)

    if (
        response["ResponseMetadata"]["HTTPStatusCode"] == 200
        and response["StoppingInstances"][0]["CurrentState"]["Name"] == "stopping"
    ):
        return close(
            intent_request["sessionAttributes"],
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "your Instance {} is successfully stopped".format(
                    instance_id
                ),
            },
        )
    else:
        return close(
            intent_request["sessionAttributes"],
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "I am unable to stop the Instance {}".format(instance_id),
            },
        )


def s3_list(intent_request):

    s3 = boto3.resource("s3")
    buckets = [bucket.name for bucket in s3.buckets.all()]
    print(buckets)

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": "Here is your list of buckets in S3 : {}".format(str(buckets)),
        },
    )


def ec2_setup(intent_request):
    region = get_slots(intent_request)["Region"]
    instance_type = get_slots(intent_request)["Instance"]
    ami = get_slots(intent_request)["Ami_id"]

    ec2 = boto3.resource("ec2", region_name=region)

    instances = ec2.create_instances(
        ImageId=ami,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        KeyName="autopilot",
    )

    print(instances[0].id)

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": "your Instance is created and instance id is : {}".format(
                instances[0].id
            ),
        },
    )


def dispatch(intent_request):
    intent_name = intent_request["currentIntent"]["name"]
    print(intent_name)

    if intent_name == "instance_new":
        return ec2_setup(intent_request)
    elif intent_name == "stopinstance":
        return ec2_stop(intent_request)
    elif intent_name == "startinstance":
        return ec2_start(intent_request)
    elif intent_name == "bucketlist":
        return s3_list(intent_request)


def lambda_handler(event, context):
    logger.debug("event.bot.name={}".format(event["bot"]["name"]))
    return dispatch(event)
