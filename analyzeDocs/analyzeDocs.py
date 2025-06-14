import json
import os
import boto3
import logging

# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB and SNS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
DYNAMO_TABLE = os.environ.get('DYNAMO_TABLE', 'VagasCompetencias')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    logger.info("Lambda C started.")
    
    # Step 1: Get resume text from payload
    try:
        resume_text = event.get('pdf_text') or ''
        logger.info("Received resume text.")
    except Exception as e:
        logger.error(f"Failed to parse resume text: {e}")
        resume_text = ''

    # Step 2: Collect unique competencias from DynamoDB
    competencias_set = set()
    try:
        table = dynamodb.Table(DYNAMO_TABLE)
        response = table.scan()
        for item in response.get('Items', []):
            competencias = item.get('competencias', [])
            competencias_set.update(competencias)
        logger.info(f"Collected {len(competencias_set)} unique competencias.")
    except Exception as e:
        logger.error(f"Error reading DynamoDB: {e}")
        competencias_set = set()
    
    # Step 3: Simulate AI processing (log that it would happen here)
    logger.info("Skipping Gemini call. This is where resume analysis would happen.")
    
    # Step 4: Simulate matching competencias (mock example)
    found_competencias = list(competencias_set)[:5]  # mock: pretend we found the first 5
    logger.info(f"Mocked found competencias: {found_competencias}")
    
    # Step 5: Query DynamoDB again for matching vacancies
    matching_vacancies = []
    try:
        for item in response.get('Items', []):
            if any(comp in item.get('competencias', []) for comp in found_competencias):
                matching_vacancies.append(item)
        logger.info(f"Found {len(matching_vacancies)} matching job vacancies.")
    except Exception as e:
        logger.error(f"Error filtering jobs: {e}")
    
    # Step 6: Publish summary to SNS
    try:
        summary = {
            "resume_snippet": resume_text[:200] + "...",
            "competencias_found": found_competencias,
            "vacancies_matched": len(matching_vacancies)
        }
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Resume Processing Summary",
            Message=json.dumps(summary, indent=2)
        )
        logger.info("Published summary to SNS.")
    except Exception as e:
        logger.error(f"Error sending to SNS: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Lambda completed', 'found': found_competencias})
    }
