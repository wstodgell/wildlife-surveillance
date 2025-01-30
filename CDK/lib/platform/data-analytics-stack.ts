import * as glue from 'aws-cdk-lib/aws-glue';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';

export class DataAnalyticsStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const bucketName = cdk.Fn.importValue('DynamoDbBucketName'); // Use the exportName from DataIngestionStack

    const s3OutputBucket = s3.Bucket.fromBucketName(this, 'OutputBucket', bucketName);


    // IAM Role for Glue Crawler
    const glueCrawlerRole = new iam.Role(this, 'GlueCrawlerRole', {
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
    });

    // Grant necessary permissions to the Glue Crawler Role
    s3OutputBucket.grantRead(glueCrawlerRole);
    glueCrawlerRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole'));

    // Glue Database for the crawler
    const glueDatabase = new glue.CfnDatabase(this, 'GlueDatabase', {
      catalogId: this.account,
      databaseInput: {
        name: 'gps_data_analytics_db',
      },
    });

    new glue.CfnCrawler(this, 'GlueS3Crawler', {
        role: glueCrawlerRole.roleArn,
        databaseName: glueDatabase.ref,
        targets: {
          s3Targets: [
            {
              path: `s3://${s3OutputBucket.bucketName}/gps_data/`, // Point to the gps_data folder
            },
            {
              path: `s3://${s3OutputBucket.bucketName}/env_data/`, // Point to the env_data folder
            },
          ],
        },
        name: 'S3ResultsCrawler',
        tablePrefix: 'processed_', // Optional table prefix
      });
  }
}
