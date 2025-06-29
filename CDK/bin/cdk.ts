#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { EcrStack } from '../lib/iot/ecr-stack';
import { EcsStack } from '../lib/iot/ecs-stack';
import { IotCodeStack } from '../lib/iot/iot-stack';
import { DataIngestionStack } from '../lib/platform/data-ingestion-stack';
import { FileGatewayStack } from '../lib/platform/file-gateway-stack';
import { ClinicIngestionStack } from '../lib/platform/clinic-ingestion-stack';
import { ConfigurationStack } from '../lib/configuration-stack';
import { DataAnalyticsStack } from '../lib/platform/data-analytics-stack';
import { AuthStack } from '../lib/platform/auth-stack';
import { AmplifyStack } from '../lib/platform/amplify-stack';
import { EtlOrchestrationStack } from '../lib/platform/etl-orchestration-stack';

const app = new cdk.App();


// *** PLATFORM
new ConfigurationStack(app, 'ConfigurationStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

// Instantiate the EcrStack
new EcrStack(app, 'EcrStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

// Instantiate the EcsStack
new EcsStack(app, 'EcsStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new IotCodeStack(app, 'IotCodeStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

// *** PLATFORM
new DataIngestionStack(app, 'DataIngestionStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new DataAnalyticsStack(app, 'DataAnalyticsStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new AuthStack(app, 'AuthStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new AmplifyStack(app, 'AmplifyStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

/*
new EtlOrchestrationStack(app, 'EtlOrchestrationStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});
*/
/*
new ClinicIngestionStack(app, 'ClinicIngestionStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new FileGatewayStack(app, 'FileGatewayStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});
*/