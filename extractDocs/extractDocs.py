import json
import boto3
import os
import logging
import fitz  # PyMuPDF

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
textract = boto3.client('textract')
lambda_client = boto3.client('lambda')

# Set this to the name of Lambda B
TARGET_LAMBDA_B = os.getenv('TARGET_LAMBDA_B')

def lambda_handler(event, context):
    logger.info("Triggered with event: %s", json.dumps(event))

    try:
        # 1. Get file info
        bucket = event['Records'][0]['s3']['bucket']['name']
        pdf_key = event['Records'][0]['s3']['object']['key']
        filename = os.path.splitext(os.path.basename(pdf_key))[0]

        # 2. Download PDF
        pdf_obj = s3.get_object(Bucket=bucket, Key=pdf_key)
        pdf_bytes = pdf_obj['Body'].read()
        logger.info("PDF downloaded")

        # 3. Try to download optional TXT file (email content)
        txt_key = f"{filename}.txt"
        txt_content = ""
        try:
            txt_obj = s3.get_object(Bucket=bucket, Key=txt_key)
            txt_content = txt_obj['Body'].read().decode('utf-8')
            logger.info("TXT file found and read")
        except Exception as e:
            logger.warning("No matching TXT file: %s", e)

        # 4. Convert PDF pages to images using PyMuPDF
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        logger.info(f"PDF has {pdf_doc.page_count} page(s)")
        full_text = ""

        for idx in range(pdf_doc.page_count):
            page = pdf_doc.load_page(idx)
            pix = page.get_pixmap(dpi=200)  # Optional: adjust DPI for better quality
            image_bytes = pix.tobytes("png")

            textract_response = textract.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            page_text = " ".join([
                block['Text'] for block in textract_response['Blocks']
                if block['BlockType'] == 'LINE'
            ])
            logger.info(f"Extracted {len(page_text)} chars from page {idx+1}")
            full_text += page_text + "\n"

        # 5. Invoke second Lambda with the result
        payload = {
            "filename": filename,
            "pdf_text": full_text,
            "txt_content": txt_content
        }


        # Lambda B
        if TARGET_LAMBDA_B:
            lambda_client.invoke(
                FunctionName=TARGET_LAMBDA_B,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            logger.info("Data sent to Lambda B")
        else:
            logger.warning("TARGET_LAMBDA_B not set.")
            
        # Lambda C
        lambda_c_name = os.getenv('TARGET_LAMBDA_C')
        if lambda_c_name:
            lambda_client.invoke(
                FunctionName=lambda_c_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            logger.info("Data sent to Lambda C")
        else:
            logger.warning("TARGET_LAMBDA_C not set.")

        return {
            'statusCode': 200,
            'body': json.dumps('Success: Data forwarded')
        }

    except Exception as e:
        logger.error("Error: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f"Errordsfjkasgdfilho: {str(e)}")
        }
