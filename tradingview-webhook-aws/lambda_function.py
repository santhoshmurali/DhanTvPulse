import json
import boto3
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TradingAlerts')

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        http_method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', '/')
        
        if path == '/webhook' and http_method == 'POST':
            return handle_webhook(event, context)
        elif path == '/status' and http_method == 'GET':
            return handle_status(event, context)
        elif path == '/test' and http_method == 'POST':
            return handle_test(event, context)
        else:
            return create_error_response(404, "Endpoint not found")
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def handle_webhook(event, context):
    try:
        if 'body' not in event or not event['body']:
            return create_error_response(400, "No data received")
        
        try:
            body = event['body']
            alert_data = json.loads(body)
        except json.JSONDecodeError as e:
            return create_error_response(400, "Invalid JSON format")
        
        logger.info(f"Processing TradingView alert: {alert_data}")
        processed_alert = process_trading_alert(alert_data)
        alert_id = store_alert_in_db(processed_alert)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'status': 'success',
                'message': 'TradingView alert received and processed',
                'alert_id': alert_id,
                'timestamp': processed_alert['timestamp'],
                'alert_name': processed_alert['alert_name'],
                'symbol': processed_alert['symbol']
            })
        }
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return create_error_response(500, f"Processing error: {str(e)}")

def process_trading_alert(alert_data):
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    return {
        'timestamp': timestamp,
        'processed': True,
        'alert_name': alert_data.get('ALERTNAME', 'UNKNOWN'),
        'symbol': alert_data.get('symbol', ''),
        'limit_price': alert_data.get('limit_price', '0'),
        'capital_percent': alert_data.get('capital_percent', '0'),
        'lot_size': alert_data.get('lot_size', '0'),
        'order_slicing_value': alert_data.get('order_slicing_value', '0'),
        'total_quantity': alert_data.get('total_quantity', '0'),
        'raw_data': alert_data
    }

def store_alert_in_db(alert_data):
    try:
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{abs(hash(alert_data['timestamp'])) % 10000}"
        
        db_item = {
            'AlertID': alert_id,
            'Timestamp': alert_data['timestamp'],
            'AlertName': alert_data['alert_name'],
            'Symbol': alert_data['symbol'],
            'LimitPrice': alert_data['limit_price'],
            'CapitalPercent': alert_data['capital_percent'],
            'LotSize': alert_data['lot_size'],
            'OrderSlicingValue': alert_data['order_slicing_value'],
            'TotalQuantity': alert_data['total_quantity'],
            'Processed': alert_data['processed'],
            'RawData': alert_data.get('raw_data', {}),
            'TTL': int((datetime.utcnow().timestamp() + (30 * 24 * 3600)))
        }
        
        table.put_item(Item=db_item)
        logger.info(f"Alert stored with ID: {alert_id}")
        return alert_id
        
    except Exception as e:
        logger.error(f"Error storing alert: {str(e)}")
        return f"storage_error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

def handle_status(event, context):
    try:
        response = table.scan(Select='COUNT')
        total_alerts = response.get('Count', 0)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'status': 'running',
                'message': 'AWS Lambda TradingView Webhook Handler is operational',
                'total_alerts': total_alerts,
                'server_time': datetime.utcnow().isoformat() + 'Z'
            })
        }
    except Exception as e:
        return create_error_response(500, f"Status check failed: {str(e)}")

def handle_test(event, context):
    try:
        test_alert = {
            'ALERTNAME': 'TEST ALERT',
            'symbol': 'NIFTY250930P25800',
            'limit_price': '25800',
            'capital_percent': '50',
            'lot_size': '75',
            'order_slicing_value': '1800',
            'total_quantity': '3750',
            'test_mode': True
        }
        
        processed_alert = process_trading_alert(test_alert)
        alert_id = store_alert_in_db(processed_alert)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'status': 'test_success',
                'message': 'Test alert generated and processed successfully',
                'alert_id': alert_id,
                'timestamp': processed_alert['timestamp']
            })
        }
    except Exception as e:
        return create_error_response(500, f"Test failed: {str(e)}")

def create_error_response(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'error': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    }