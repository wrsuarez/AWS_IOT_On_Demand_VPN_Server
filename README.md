# OnDemandVPNServer
Create a VPN server on demand and terminate when needed.

CloudFormation Templates are forthcoming but for now here's the install process:

1. Create an AWS account
2. Create a Security Group that allows port 1194 inbound from 0.0.0.0/0 and SSH in only from your trusted IP (like your house)
3. Create an SNS Topic for notifications. Subscribe to the topic with your email address
4. Create an IAM_Profile that allows S3 Read and Write
5. Create two S3 buckets, one for holding the VPN config file, one for holding the generated VPN keys
6. Create an SSH Key, download, and stash it somewhere safe. You shouldn't ever need it unless you need to SSH to the instance for some reason and troubleshoot something
7. Upload the included OpenVPN config file (or one that you've created) to the config S3 bucket
8. Create a new Lambda function with the following environemnt variables populated with your values:
  SNS_TOPIC_ARN = The TopicARN you created in step 3.
  IAM_PROFILE = The IAM EC2 Role you created in step 4.
  OPENVPN_KEY_BUCKET_NAME = The key bucket you created in step 5.
  OPENVPN_CONFIG_BUCKET_NAME = The config bucket you created in step 5.
  AMI_ID = The AMI of the instance you want to launch. All testing was done with the Amazon Linux AMI
  SECURITY_GROUP_ID = The SecurityGroupID you created in step 2.
  INSTANCE_TYPE = The type of instance to use. t2.nano or t2.micro should work fine
  KEY_NAME = The name of the key you created in step 6. 
  
 9. Create a new IOT device following Amazon's setup instructions for the IOT button
 10. Create a rule for the IOT button to the Lambda function you created in step 8.
 
 
 Enjoy VPN goodness
