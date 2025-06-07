import mysql.connector
import boto3
import os
import json
import requests

def lambda_handler(event, context):
    print("Iniciando execução...")

    # Buscar currículo do MySQL
    conn = mysql.connector.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE']
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM curriculos ORDER BY id DESC LIMIT 1")
    curriculo = cursor.fetchone()
    cursor.close()
    conn.close()

    if not curriculo:
        print("Nenhum currículo encontrado.")
        return

    competencias_curriculo = curriculo.get('competencias', '').split(',')
    experiencia = curriculo.get('experiencia', '')

    print(f"Currículo encontrado: {curriculo['nome']}")

    # Buscar vagas no DynamoDB (mock, se não funcionar não tem problema)
    dynamodb = boto3.resource('dynamodb')
    try:
        table = dynamodb.Table('vagas')
        response = table.scan()
        vagas = response.get('Items', [])
    except Exception as e:
        print(f"Erro no DynamoDB: {e}")
        vagas = []  # Em caso de erro, continue com lista vazia

    # Prompt para o Gemini
    prompt = (
        "Você é um sistema que analisa um currículo e identifica vagas com competências semelhantes.\n"
        "Retorne SOMENTE uma lista JSON no formato: [{'id': '001', 'cargo': '...'}]\n\n"
        f"Currículo:\n{json.dumps({'nome': curriculo['nome'], 'competencias': competencias_curriculo, 'experiencia': experiencia}, ensure_ascii=False)}\n\n"
        f"Vagas:\n{json.dumps(vagas, ensure_ascii=False)}"
    )

    # Chamada ao Gemini
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent",
            params={"key": os.environ['GEMINI_API_KEY']},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 300}
            },
            timeout=20
        )
        response.raise_for_status()
        resposta = response.json()
        texto_resposta = resposta.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        print("Resposta do Gemini:")
        print(texto_resposta)
    except requests.RequestException as e:
        print(f"Erro ao chamar o Gemini: {e}")
        return {'statusCode': 500, 'body': str(e)}

    # Tentar enviar resposta por SNS
    try:
        sns = boto3.client('sns')
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject=f"Vagas compatíveis com {curriculo['nome']}",
            Message=texto_resposta
        )
        print("Email enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar email via SNS: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps({'resposta_gemini': texto_resposta})
    }
