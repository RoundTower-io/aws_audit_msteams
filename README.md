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

# How does this work on AWS?
1. Whenever a you commit to this repo (using [Git][11]), you will drive the pipeline (below) and update the lambda function.
1. An [AWS build pipeline][12] called "aws-audit-lambda-pipeline" creates and updates the lambda function. 
1. An AWS [IAM role][14] defines the permissions your function has 
1. The AWS [Systems Manager Parameter Store][15] is where we keep the MS Teams webhook URL. This is sensitive info, so we keep it in the secrets repository.

# What needs to be done on Microsoft Teams?
1. Create a [webhook][16] for the channel you want output to go to. 
1. Store the webhook URL in the Systems Manager Parameter Store (above).

[11]: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
[12]: https://docs.aws.amazon.com/lambda/latest/dg/build-pipeline.html
[14]: https://docs.aws.amazon.com/lambda/latest/dg/access-control-identity-based.html
[15]: https://aws.amazon.com/blogs/compute/sharing-secrets-with-aws-lambda-using-aws-systems-manager-parameter-store/
[16]: https://docs.microsoft.com/en-us/outlook/actionable-messages/send-via-connectors
