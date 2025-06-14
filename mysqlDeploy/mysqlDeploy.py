import json
import logging
import os
import mysql.connector

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Extract fields from event
    filename = event.get('filename')
    pdf_text = event.get('pdf_text')
    txt_content = event.get('txt_content')

    # MySQL connection info from env vars
    host = os.getenv('MYSQL_HOST')
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    database = os.getenv('MYSQL_DATABASE')
    port = int(os.getenv('MYSQL_PORT', 3306))

    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO resumes (filename, pdf_text, txt_content)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (filename, pdf_text, txt_content))
        conn.commit()

        logger.info("Data inserted into MySQL successfully.")

        cursor.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps('Success: Data inserted into database')
        }

    except mysql.connector.Error as err:
        logger.error(f"MySQL error: {err}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"MySQL error: {err}")
        }
