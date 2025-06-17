import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path = require('path');
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';

export class EtlOrchestrationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const lambdaPath = 'lib/platform/lambdas/etl_orchestration';

    const lambdaRole = new iam.Role(this, 'LambdaGlueRole', {
    assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
    ]
    });

    lambdaRole.addToPolicy(new iam.PolicyStatement({
    actions: [
        'glue:StartCrawler',
        'glue:GetCrawler',
        'glue:GetCrawlerMetrics',
        'glue:StartJobRun',
        'glue:GetJobRun',
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents'
    ],
  resources: ['*'] // You can restrict this later
}));


    const startCrawlerFn = new lambda.Function(this, 'StartCrawlerFn', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'start_crawler.handler',
        code: lambda.Code.fromAsset(lambdaPath),
        role: lambdaRole,
    });

    const waitCrawlerFn = new lambda.Function(this, 'WaitCrawlerFn', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'wait_for_crawler.handler',
        code: lambda.Code.fromAsset(lambdaPath),
        role: lambdaRole,
    });

    const startJobFn = new lambda.Function(this, 'StartJobFn', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'start_job.handler',
        code: lambda.Code.fromAsset(lambdaPath),
        role: lambdaRole,
    });

    const waitJobFn = new lambda.Function(this, 'WaitJobFn', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'wait_for_job.handler',
        code: lambda.Code.fromAsset(lambdaPath),
        role: lambdaRole,
    });


  }
}