from __future__ import print_function

import json
import urllib
import boto3
import os


print('Loading function')

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))

    try:
        vpnkeyurl = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                'Key': key
            }
        )
        sns_response = sns.publish(TopicArn=os.environ['SNS_TOPIC_ARN'],Message=str(vpnkeyurl))
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
