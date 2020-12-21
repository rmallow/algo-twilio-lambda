from __future__ import print_function
import boto3
from boto3.dynamodb.conditions import Key

"""
All tested incoming phone numbers started with a %2B string.
Not sure where this came from, whether it's twilio or aws api gateway
but either way using this remove var to strip that part out
"""
REMOVE_STRING = '%2B'

"""
following are keys used to acess the twilio message contents
FROM_KEY - phoneNumber that sent the message
BODY_KEY - text content of the message
"""
FROM_KEY = 'From'
BODY_KEY = 'Body'

"""
following are keys used to acess the dynamo db
PHONE_NUMBER_KEY - actual primary key for the db
USER_STATE_KEY - not a db key but called key as it's used as a dict key
"""
PHONE_NUMBER_KEY = 'phoneNumber'
USER_STATE_KEY = 'userState'

#dynamo db setup and getting the numberState table that contains the data the demo needs
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('numberState')


def lambda_handler(event, context):
    message = ""
    if FROM_KEY in event:
        phoneNumber = int(event[FROM_KEY].replace(REMOVE_STRING,''))
        data = table.query(
            KeyConditionExpression=Key(PHONE_NUMBER_KEY).eq(phoneNumber)
        )
        
        state = None
        if data and 'Items' in data:
            items = data['Items']
            message = processMessage(items, event, phoneNumber)
        else:
            message = "Error Retrieving from database"
    else:
        message = "Error reading number  " + str(event) 
    
    #return response that twilio wants with message popped into the body, if message is empty twilio will error and won't send
    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
           '<Response><Message><Body>' + message +'</Body></Message></Response>'

"""
    @brief: processes incoming message and outputs the body of the twilio response

    @param: items - query response with phoneNumber as key in numberState db table
    @param: event - contents and metadata of incoming text message, text of message is in body
    @param: phoneNumber - phoneNumber that sent the message currently being processed, filtered and stripped to usable form
"""
def processMessage(items, event, phoneNumber):
    state = None
    endState = 'Demo'
    if len(items)>0 and USER_STATE_KEY in items[0]:
        state = items[0][USER_STATE_KEY]
        endState = state
    
    retVal = ""
    
    if state is None:
        retVal = """Welcome to the Algo demo! This is intended to demonstrate a simple use case for Algo.
        \nIn this example we will be analyzing the last open day for a stock and seeing potential buy-in points.
        \nThe configuration setup can be see under demo configs at https://github.com/rmallow/algo
        \nPlease reply with just one desired stock ticker like MSFT (Microsoft) or AAPL (Apple)
        """ 
        endState = 'DemoStart'
    elif state == 'DemoStart':
        endState = 'Loop'
        retVal = "DEMO END"
    else:
        #this should be hit just when state is loop but just in case making this an else
        
    if state:
        if state != endState:
            response = table.update_item(
                Key={
                    PHONE_NUMBER_KEY: phoneNumber
                },
                UpdateExpression="set "+ USER_STATE_KEY + "=:s",
                ExpressionAttributeValues={
                    ':s': endState
                },
                ReturnValues="UPDATED_NEW"
            )
    else:
        response = table.put_item(
            Item={
                PHONE_NUMBER_KEY: phoneNumber,
                USER_STATE_KEY: endState
            }
        )
    
    return retVal