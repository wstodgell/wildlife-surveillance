import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export function createIoTECS(
    scope: Construct,
    ecsPrefix: string,              //GPS
    cdkSecretID: string,             //GPSThingSecret - just a CDK construct label
    awsSecretName: string,           //IoT/GPSThing/certs - to reference the name of the secret - to get value later
    taskRoleName: string,           //GPSTaskRole - ???
    taskExecutionRole: iam.IRole,   //ecsTarkExecutionRole - so ECS can perform all require needs
    EcrRepositoryUri: string,       // EcrRepositoryUri - Uri where related image is
    cluster: cdk.aws_ecs.ICluster   //cluster for all services
  ) {

    console.log(`👀 Creating ECS: ${ecsPrefix}`);
    //Creates a new CloudWatch Log Group in AWS.  LogGroup = container for storing logs
    //This = ECS Stack
    //ECSLogGroup (identifier)
    const logGroup = new logs.LogGroup(scope, `Ecs${ecsPrefix}LogGroup`, {
      logGroupName: `/ecs/IoT-${ecsPrefix}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Ensure logs are cleaned up with stack removal
      retention: logs.RetentionDays.ONE_WEEK,   // Adjust retention period as needed
    });

    // Retrieve the secrets for TestThing and GPSThing from AWS Secrets Manager
    
    // IMPORTANT: This secret references a specific Secrets Manager entry where the device CERTIFICATES are stored.
    // These secrets are created in LATER the IoT stack using the naming pattern: `IoT/${thingName}/certs`
    // They are later retrieved at runtime by MTTQS_SETUP.PY to authenticate with AWS IoT Core.
    //
    // Example usage:
    //   cdkSecretID     = 'GPSThingSecret'         // CDK-internal ID – can be anything
    //   awsSecretName   = 'IoT/GPSThing/certs'     // Actual secret name in AWS Secrets Manager (must match exactly)
    const iotThingSecret = secretsmanager.Secret.fromSecretNameV2(scope, cdkSecretID, awsSecretName);

    // Create a Task Role for GPS task that can access GPSThing's secret
    const IoTTaskRole = new iam.Role(scope, taskRoleName, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'), // Allows ECS tasks to assume this role
      description: `Task role for ${ecsPrefix} task with permissions for Secrets Manager and IoT Publishing within python script`,
    });

    // Attach the pre-made AmazonSSMReadOnlyAccess managed policy to the GPS task role
    IoTTaskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMReadOnlyAccess"));

    // Grant the GPS task role permission to read GPSThing's secret
    iotThingSecret.grantRead(IoTTaskRole);

    // Grant permissions for CloudWatch Logs
    IoTTaskRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        "logs:CreateLogGroup", // Permission to create log groups
        "logs:CreateLogStream", // Permission to create log streams
        "logs:PutLogEvents", // Permission to put log events into log streams
        "iot:DescribeEndpoint", // Allows describing IoT endpoints
        "iot:Connect", // Allows establishing a connection to IoT Core
        "iot:Publish", // Allows publishing messages to IoT topics
        "iot:Subscribe", // Allows subscribing to IoT topics
        "iot:Receive" // Allows receiving messages from IoT topics
      ],
      resources: ["*"], // Restrict to the specific resources necessary for these actions
    }));

    // Create a Fargate Task Definition for IoT-GPS
    const FargateTaskDefinition = new ecs.FargateTaskDefinition(scope, `IoT${ecsPrefix}TaskDefinition`, {
      family: `IoT-${ecsPrefix}`, // Logical family name of this task definition
      cpu: 256, // CPU units (adjust as needed)
      memoryLimitMiB: 512, // Memory in MB (adjust as needed)
      executionRole: taskExecutionRole, // Use the execution role for pulling images and starting tasks
      taskRole: IoTTaskRole, // Task role used to interact with Secrets Manager for GPSThing
    });

    // Define the container for the GPS task, pulled from the ECR repository
    const FargateContainer = FargateTaskDefinition.addContainer(`${ecsPrefix}Container`, {
      image: ecs.ContainerImage.fromRegistry(EcrRepositoryUri), // Pulls container image from ECR
      logging: new ecs.AwsLogDriver({
        streamPrefix: `IoT-${ecsPrefix}`, // Prefix for the CloudWatch log stream
        logGroup: logGroup, // The log group where container logs will be sent
      }),
    });

     // Set networking mode for task (awsvpc)
     FargateContainer.addPortMappings({
      containerPort: 80, // Adjust if your container exposes a different port
    });

    // Add Fargate Service to the IoTCluster
    const FargateService = new ecs.FargateService(scope, `${ecsPrefix}IoTService`, {
      cluster, // The ECS cluster where the task will run
      taskDefinition: FargateTaskDefinition, // Task definition that defines the container
      assignPublicIp: true, // Ensure tasks are reachable via public IP if needed
      desiredCount: 1, // Adjust based on how many instances you want running
      enableExecuteCommand: true, // Enable ECS Exec for debugging into the container
    });

    return FargateService

  }