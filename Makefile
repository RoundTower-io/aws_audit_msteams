#
build:
	lambda-uploader --publish  ./audit \
	                --extra-file ./common.py \
	                --config ./audit/lambda.json


default: build

