import boto3
import os
import time


#  Using an AWS IOT Button
#  On a single click create a new VPN server, assign an elastic IP address, upload the created OpenVPN key to the defined
#  bucket, and email the user with the IP address of the server
#
#  On a double click tear down the resources

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')

#Check the button click event
    if event['clickType'] == "DOUBLE":
        print("Shutting down VPN server")
        ec2_resources = boto3.resource('ec2')

#Get instances that are running
        instances = ec2_resources.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        for instance in instances:
            if instance.tags:

#Check if the instance has the VPNServer tag
                if "VPNServer" in instance.tags[0]['Value']:

#Get the allocation ID for the EIP assigned to the instance
                    eip = ec2_client.describe_addresses(Filters=[{'Name':'instance-id','Values':[instance.id]}])

#Release the EIP
                    ec2_client.release_address(AllocationId=eip['Addresses'][0]['AllocationId'])

#Terminate the instance
                    ec2_client.terminate_instances(InstanceIds=[instance.id])

#If its a single click event start building the VPN Server
    else:
#Set up the user data to install open, pull in the config, and start the services, upload the VPN key to the specified S3 bucket
# A seperate Lambda function will send me the URL of the key to download it
        user_data_script = """#!/bin/bash
         yum install -y openvpn
         modprobe iptable_nat
         echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
         iptables -t nat -A POSTROUTING -s 10.4.0.1/2 -o eth0 -j MASQUERADE
         cd /etc/openvpn
         openvpn --genkey --secret ovpn.key
         aws s3 cp s3://""" + os.environ['OPENVPN_CONFIG_BUCKET_NAME'] + """/openvpn.conf /etc/openvpn
         aws s3 cp /etc/openvpn/ovpn.key s3://""" + os.environ['OPENVPN_KEY_BUCKET_NAME'] + """/
         service openvpn start
         """
#Create the instance
        result = ec2_client.run_instances(
            ImageId=os.environ['AMI_ID'],
            MinCount=1,
            MaxCount=1,
            KeyName=os.environ['KEY_NAME'],
            SecurityGroupIds=[os.environ['SECURITY_GROUP_ID']],
            UserData=user_data_script,
            InstanceType=os.environ['INSTANCE_TYPE'],
            Monitoring={'Enabled':False},
            IamInstanceProfile={'Name':os.environ['IAM_PROFILE']}
        )
        instanceID = result['Instances'][0]['InstanceId']
        print(result['Instances'][0]['InstanceId'])

#Allocate an elastic IP
        eip = ec2_client.allocate_address(Domain='vpc')
        print(eip['AllocationId'])

#Check to see if the instance is running before trying to assign the elastic IP, if it isn't wait 1 minute
        state = ec2_client.describe_instances(InstanceIds=[instanceID])
        if state['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
            time.sleep(60)

#Assign the EIP to the instance
        try:
            ec2_client.associate_address(InstanceId=instanceID,AllocationId=eip['AllocationId'],AllowReassociation=True)
            print(eip['PublicIp'])
        except:
            ec2_client.terminate_instances(InstanceIds=[instanceID])
            ec2_client.release_address(AllocationId=eip['AllocationId'])
            print("Failed to associate address to instance, terminating all resources")

#Tag the instance with VPNServer
        ec2_client.create_tags(Resources=[instanceID],Tags=[{'Key':'Name','Value':'VPNServer'}])

#Optionally use a DNS Record for the static IP eliminating the need to change your VPN client config each time the serveris provisioned

        if os.environ['HOSTED_ZONE_ID']:
            route53_client = boto3.client('route53')
            route53_client.change_resource_record_sets(
                HostedZoneId = os.environ['HOSTED_ZONE_ID'],
                ChangeBatch = {
                    'Changes' : [
                        {
                            'Action' : 'UPSERT',
                            'ResourceRecordSet' : {
                                'Name' : os.environ['DNS_NAME'],
                                'Type' : 'A',

                            }
                        }
                    ]
                }
            )

#Notify me the VPN Server is up and send me the public IP
        sns_client = boto3.client('sns')
        sns_client.publish(TopicArn=os.environ['SNS_TOPIC_ARN'],Message="VPN IP: " + eip['PublicIp'] + "DNS Name: " + os.environ['DNS_NAME'])

