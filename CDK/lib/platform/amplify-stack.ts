import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as amplify from 'aws-cdk-lib/aws-amplify';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class AmplifyStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ✅ Retrieve GitHub OAuth Token from AWS Secrets Manager
    const githubToken = secretsmanager.Secret.fromSecretNameV2(this, 'GitHubToken', 'GITHUB_OAUTH_TOKEN');

    // ✅ Create an AWS Amplify App (Connects to GitHub)
    const amplifyApp = new amplify.CfnApp(this, 'MyAmplifyApp', {
      name: 'WildlifeSurveillanceApp', // Change the name as needed
      repository: 'https://github.com/wstodgell/WildlifeSurveillancev2.git', // Your correct GitHub repo
      oauthToken: githubToken.secretValue.unsafeUnwrap(), // Extract secret token securely
    });

    // ✅ Define the Branch (Amplify Will Deploy from "main" Branch)
    const amplifyBranch = new amplify.CfnBranch(this, 'MainBranch', {
      appId: amplifyApp.attrAppId,
      branchName: 'main', // Make sure this is the correct branch name
    });

    // ✅ Output Amplify App ID for reference
    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.attrAppId,
      description: 'AWS Amplify App ID',
    });

    // ✅ Output Amplify Console URL
    new cdk.CfnOutput(this, 'AmplifyConsoleUrl', {
      value: `https://us-east-1.console.aws.amazon.com/amplify/home#/d${amplifyApp.attrAppId}`,
      description: 'AWS Amplify Console URL',
    });
  }
}
