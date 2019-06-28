# What is it?
An AWS Lambda function that posts information about running resources to MS Teams channels

# Why is it needed? 
It is needed to keep track of resources running on AWS.  This is meant for use in lab environments or on AWS accounts with multiple users.  

Frequently, resources like ec2 instances are started - and promptly forgotten about.  Sometimes weeks will pass before someone notices 
the active resource and stops it.  This tool is meant to keep that from happening.  It will post to MS Teams a list of active resources and serve 
as a reminder to stop anything unnecessary.

# Why use an AWS Lambda function?
To borrow from the AWS documentation, lambdas are an excellent way to "run your code in response to events and automatically manages the underlying compute resources for you".  There are no servers to set up.  It "just works" without having to worry about configuring any complex infrastructure.  

In our case the lambda runs in response to a timer trigger.  The lambda is driven (generally daily) to detect, document, and report running assets on our AWS environment. The report output is sent to an MS Teams channel.   

# What are the pre-reqs?
1. [Git][11] 
1. The [AWS Command Line Interface][6]
1. The ["AWS Serverless Application Model(SAM)"][3] Python module.
1. [Docker][7]. This is used for local running and debugging  
1. An IDE. [There are several supporting SAM][4]. We used [PyCharm][5] 

# How do I use PyCharm with it?
1. [Install PyCharm][8]
1. Install the [AWS Toolkit Plugin for PyCharm][9]
1. [Clone a copy of this repo][10] using PyCharm
1. Follow [these directions][12] for using the toolkit

# What else is needed on AWS to support it?
1. An AWS [Cloudwatch Event][13] to "drive" the lambda function. The idea is to have a cron-like event kick off the report. 
1. An AWS [IAM role][14] that defines the permissions your function has 
1. An AWS [Systems Manager Parameter Store][15]. This will be where you keep the MS Teams webhook URL

# What needs to be done on Microsoft Teams?
1. Create a [webhook][16] for the channel you want output to go to. 
1. Store the webhook URL in the Systems Manager Parameter Store (above).


[3]: https://docs.aws.amazon.com/serverless-application-model/index.html
[4]: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html
[5]: https://www.jetbrains.com/pycharm/
[6]: https://aws.amazon.com/cli/
[7]: https://www.docker.com/products/docker-desktop
[8]: https://www.jetbrains.com/help/pycharm/installation-guide.html?section=Windows
[9]: https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/setup-toolkit.html
[10]: https://www.jetbrains.com/help/pycharm/manage-projects-hosted-on-github.html
[11]: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
[12]: https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/building-lambda.html
[13]: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html
[14]: https://docs.aws.amazon.com/lambda/latest/dg/access-control-identity-based.html
[15]: https://aws.amazon.com/blogs/compute/sharing-secrets-with-aws-lambda-using-aws-systems-manager-parameter-store/
[16]: https://docs.microsoft.com/en-us/outlook/actionable-messages/send-via-connectors
