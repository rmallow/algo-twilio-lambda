from __future__ import print_function
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('numberState')

REMOVE_STRING = '%2B'
FROM_KEY = 'From'
BODY_KEY = 'Body'
PHONE_NUMBER_KEY = 'phoneNumber'
USER_STATE_KEY = 'userState'

def lambda_handler(event, context):
    message = ""
    if FROM_KEY in event:
        phoneNumber = int(event[FROM_KEY].replace(REMOVE_STRING,''))
        data = table.query(
            KeyConditionExpression=Key(PHONE_NUMBER_KEY).eq(phoneNumber)
        )
        
        state = None
        print(data)
        if data and 'Items' in data:
            items = data['Items']
            if len(items)>0 and USER_STATE_KEY in items[0]:
                state = items[0][USER_STATE_KEY]
            message = processMessage(state, event, phoneNumber)
        else:
            message = "Error Retrieving from database"
    else:
        message = "Error reading number  " + str(event) 
            
    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
           '<Response><Message><Body>' + message +'</Body></Message></Response>'


def processMessage(state, event, phoneNumber):
    endState = "Demo"
    
    retVal = "DEMO MODE"
    if state == 'Demo':
        retVal = "DEMO MODE 2"
        endState = 'Demo2'
    
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