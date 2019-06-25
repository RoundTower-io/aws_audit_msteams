# aws_audit_msteams

# What is it?
An AWS Lambda function that posts information about running resources to MS Teams channels

# Why is it needed? 
It is needed to keep track of resources running on AWS.  This is meant for use in lab environments or on AWS accounts with multiple users.  
Frequently, resources like ec2 instances are started and promptly forgotten about.  Sometimes weeks will pass before someone notices 
the active resource and stops it.  This tool is meant to keep that from happening.  It will post to MS Teams a list of active resources and serve 
as a reminder to stop anything unnecessary.

# Why use an AWS Lambda function?
To borrow from the AWS documentation, lambdas are an excellent way to "run your code in response to events and automatically manages the underlying compute resources for you".  There are no servers to set up.  It "just works" without having to worry about configuring any complex infrastructure.  

In our case the lambda runs in response to a timer trigger.  The lambda is driven (generally daily) to detect, document, and report running assets on our AWS environment. The report output is sent to an MS Teams channel.   

# What are the pre-reqs?

You need to install the ["AWS Serverless Application Model(SAM)"][3]

# How do you update it?
The easiest way to update the lambda function is via an IDE.  [There are several supported by SAM][4].  


# What other things are needed to setup the Lambda Function?
## AWS IAM
There needs to be an IAM ["Execution Role"][2] defined to allow our lambda role to execute. This
example uses lambda_s3_monitor. There are 2 sections within `lambda_s3_monitor`.  One sets s3 permissions and the other defines runtime logging.

1. Follow the steps in Creating a Role for an AWS Service (AWS Management Console) in the IAM User Guide to create an IAM role (execution role). As you follow the steps to create a role, note the following:
2. In Role Name, use a name that is unique within your AWS account (for example, lambda_aws_audit_execution_role).
3. In Select Role Type, choose AWS Service Roles, and then choose AWS Lambda. This grants the AWS Lambda service permissions to assume the role.
4. In Attach Policy, choose `AWSLambdaBasicExecutionRole`, `AmazonEC2ReadOnlyAccess` and `AmazonWorkSpacesAdmin`
5. Copy the `Role ARN` (at the top of the page) and paste it in the `Role` field of the `lambda.json` file. This will associate your role with your lambda function.
    ```
    Example 
      "role": "arn:aws:iam::123456789012:role/lambda_aws_audit_execution_role",
    ```


[1]: https://github.com/rackerlabs/lambda-uploader
[2]: https://docs.aws.amazon.com/lambda/latest/dg/intro-permission-model.html#lambda-intro-execution-role
[3]: https://docs.aws.amazon.com/serverless-application-model/index.html
[4]: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html
