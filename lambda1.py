import json
import base64

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    try:
        body = json.loads(event['body'])
        
        # Validate inputs
        if not all([body.get('email'), body.get('filename'), body.get('fileContent')]):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Just validate base64 (don't actually decode)
        try:
            if len(body['fileContent']) % 4:
                # Add padding if needed
                body['fileContent'] += '=' * (4 - len(body['fileContent']) % 4)
            base64.b64decode(body['fileContent'], validate=True)
        except:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid file content'})
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Validation successful (simulated upload)',
                'email': body['email'],
                'filename': body['filename']
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Processing error',
                'details': str(e)
            })
        }