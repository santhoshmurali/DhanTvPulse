# ==============================================================================
# AWS Lambda TradingView Webhook Deployment Script - Windows PowerShell
# ==============================================================================
# 
# Prerequisites:
# - AWS CLI installed and configured (aws configure)
# - Python 3.7+ installed
# - PowerShell 5.0+ (built into Windows 10/11)
# 
# Usage: 
# 1. Save as deploy.ps1
# 2. Right-click PowerShell as Administrator 
# 3. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 4. Run: .\deploy.ps1
# ==============================================================================

# Colors for output
$Red = "Red"
$Green = "Green" 
$Blue = "Blue"
$Yellow = "Yellow"

# Configuration
$ProjectName = "tradingview-webhook"
$Region = "us-east-1"
$PythonVersion = "3.9"

Write-Host "🚀 Starting AWS Lambda Deployment for TradingView Webhook" -ForegroundColor $Blue
Write-Host "==================================================================="

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor $Blue

# Check AWS CLI
try {
    $awsVersion = aws --version
    Write-Host "✅ AWS CLI found: $awsVersion" -ForegroundColor $Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor $Red
    exit 1
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "✅ AWS credentials configured for account: $($identity.Account)" -ForegroundColor $Green
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor $Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor $Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.7+." -ForegroundColor $Red
    exit 1
}

Write-Host "✅ All prerequisites satisfied!" -ForegroundColor $Green

# Create deployment directory
Write-Host "📁 Creating deployment package..." -ForegroundColor $Blue

$DeployDir = "deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $DeployDir | Out-Null
Set-Location $DeployDir

# Create Lambda function code
Write-Host "📝 Creating Lambda function code..." -ForegroundColor $Blue

$LambdaCode = @'
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
        elif path == '/alerts' and http_method == 'GET':
            return handle_get_alerts(event, context)
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
            if event.get('isBase64Encoded', False):
                import base64
                body = base64.b64decode(event['body']).decode('utf-8')
            else:
                body = event['body']
            alert_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return create_error_response(400, "Invalid JSON format")
        
        logger.info(f"Processing TradingView alert: {alert_data}")
        processed_alert = process_trading_alert(alert_data)
        alert_id = store_alert_in_db(processed_alert)
        
        logger.info(f"Alert processed successfully. ID: {alert_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
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
    
    processed_alert = {
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
    
    # Parse symbol if it's options format (e.g., NIFTY250930P25800)
    if 'P' in processed_alert['symbol'] or 'C' in processed_alert['symbol']:
        symbol_info = parse_options_symbol(processed_alert['symbol'])
        if symbol_info:
            processed_alert.update(symbol_info)
    
    return processed_alert

def parse_options_symbol(symbol):
    try:
        if 'P' in symbol:
            parts = symbol.split('P')
            option_type = "PUT"
        elif 'C' in symbol:
            parts = symbol.split('C')
            option_type = "CALL"
        else:
            return None
            
        if len(parts) == 2:
            prefix = parts[0]
            strike_price = parts[1]
            
            if len(prefix) >= 6:
                index_name = prefix[:-6]
                expiry_date = prefix[-6:]
                
                return {
                    'index_name': index_name,
                    'expiry_date': expiry_date,
                    'option_type': option_type,
                    'strike_price': strike_price,
                    'symbol_parsed': True
                }
    except Exception as e:
        logger.error(f"Error parsing symbol {symbol}: {str(e)}")
    
    return None

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
            'TTL': int((datetime.utcnow().timestamp() + (30 * 24 * 3600)))  # 30 days expiration
        }
        
        # Add parsed symbol info if available
        if 'symbol_parsed' in alert_data:
            db_item['SymbolParsed'] = True
            db_item['IndexName'] = alert_data.get('index_name', '')
            db_item['ExpiryDate'] = alert_data.get('expiry_date', '')
            db_item['OptionType'] = alert_data.get('option_type', '')
            db_item['StrikePrice'] = alert_data.get('strike_price', '')
        
        table.put_item(Item=db_item)
        logger.info(f"Alert stored in DynamoDB with ID: {alert_id}")
        return alert_id
        
    except Exception as e:
        logger.error(f"Error storing alert in DynamoDB: {str(e)}")
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
                'server_time': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0.0'
            })
        }
    except Exception as e:
        return create_error_response(500, f"Status check failed: {str(e)}")

def handle_get_alerts(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        count = min(int(query_params.get('count', 10)), 50)
        
        response = table.scan(Limit=count)
        alerts = []
        
        for item in response.get('Items', []):
            alert = {
                'alert_id': item.get('AlertID', ''),
                'timestamp': item.get('Timestamp', ''),
                'alert_name': item.get('AlertName', ''),
                'symbol': item.get('Symbol', ''),
                'limit_price': item.get('LimitPrice', ''),
                'processed': item.get('Processed', False)
            }
            alerts.append(alert)
        
        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'alerts': alerts[:count],
                'alerts_returned': len(alerts[:count]),
                'total_count': response.get('Count', 0),
                'message': f'Returning {len(alerts[:count])} most recent alerts'
            })
        }
    except Exception as e:
        return create_error_response(500, f"Failed to retrieve alerts: {str(e)}")

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
        
        logger.info("Processing test alert")
        processed_alert = process_trading_alert(test_alert)
        alert_id = store_alert_in_db(processed_alert)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'status': 'test_success',
                'message': 'Test alert generated and processed successfully',
                'alert_id': alert_id,
                'timestamp': processed_alert['timestamp'],
                'symbol_parsed': processed_alert.get('symbol_parsed', False)
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
'@

# Write Lambda function to file
$LambdaCode | Out-File -FilePath "lambda_function.py" -Encoding UTF8

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor $Blue

# Create ZIP file (requires PowerShell 5.0+)
Compress-Archive -Path "lambda_function.py" -DestinationPath "lambda_function.zip" -Force

Write-Host "✅ Deployment package created: lambda_function.zip" -ForegroundColor $Green

# Step 1: Create DynamoDB Table
Write-Host "🗄️  Creating DynamoDB table..." -ForegroundColor $Blue

try {
    $tableExists = aws dynamodb describe-table --table-name TradingAlerts --region $Region 2>$null
    if ($tableExists) {
        Write-Host "⚠️  DynamoDB table 'TradingAlerts' already exists" -ForegroundColor $Yellow
    }
} catch {
    Write-Host "📝 Creating new DynamoDB table..." -ForegroundColor $Blue
    aws dynamodb create-table --table-name TradingAlerts --attribute-definitions AttributeName=AlertID,AttributeType=S --key-schema AttributeName=AlertID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ DynamoDB table created successfully" -ForegroundColor $Green
        Write-Host "⏳ Waiting for table to be active..." -ForegroundColor $Blue
        aws dynamodb wait table-exists --table-name TradingAlerts --region $Region
        Write-Host "✅ Table is now active" -ForegroundColor $Green
    } else {
        Write-Host "❌ Failed to create DynamoDB table" -ForegroundColor $Red
        exit 1
    }
}

# Step 2: Create IAM Role
Write-Host "👤 Setting up IAM role..." -ForegroundColor $Blue

$RoleName = "$ProjectName-lambda-role"
$PolicyName = "$ProjectName-lambda-policy"

# Get account ID
$AccountId = (aws sts get-caller-identity | ConvertFrom-Json).Account

$TrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$LambdaPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TradingAlerts"
    }
  ]
}
"@

# Save policies to temp files
$TrustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8
$LambdaPolicy | Out-File -FilePath "lambda-policy.json" -Encoding UTF8

# Check if role exists
try {
    aws iam get-role --role-name $RoleName 2>$null | Out-Null
    Write-Host "⚠️  IAM role '$RoleName' already exists" -ForegroundColor $Yellow
} catch {
    Write-Host "📝 Creating IAM role..." -ForegroundColor $Blue
    aws iam create-role --role-name $RoleName --assume-role-policy-document file://trust-policy.json
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ IAM role created" -ForegroundColor $Green
    }
}

# Create and attach policy
$PolicyArn = "arn:aws:iam::$AccountId`:policy/$PolicyName"

try {
    aws iam get-policy --policy-arn $PolicyArn 2>$null | Out-Null
    Write-Host "⚠️  IAM policy already exists" -ForegroundColor $Yellow
} catch {
    Write-Host "📝 Creating IAM policy..." -ForegroundColor $Blue
    aws iam create-policy --policy-name $PolicyName --policy-document file://lambda-policy.json
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ IAM policy created" -ForegroundColor $Green
    }
}

# Attach policy to role
aws iam attach-role-policy --role-name $RoleName --policy-arn $PolicyArn
Write-Host "✅ Policy attached to role" -ForegroundColor $Green

# Step 3: Create Lambda Function
Write-Host "⚡ Creating Lambda function..." -ForegroundColor $Blue

$FunctionName = "$ProjectName-handler"
$RoleArn = "arn:aws:iam::$AccountId`:role/$RoleName"

# Wait for role propagation
Write-Host "⏳ Waiting for IAM role propagation..." -ForegroundColor $Blue
Start-Sleep -Seconds 15

try {
    aws lambda get-function --function-name $FunctionName --region $Region 2>$null | Out-Null
    Write-Host "⚠️  Lambda function '$FunctionName' already exists. Updating code..." -ForegroundColor $Yellow
    aws lambda update-function-code --function-name $FunctionName --zip-file fileb://lambda_function.zip --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Lambda function code updated" -ForegroundColor $Green
    }
} catch {
    Write-Host "📝 Creating new Lambda function..." -ForegroundColor $Blue
    aws lambda create-function --function-name $FunctionName --runtime python3.9 --role $RoleArn --handler lambda_function.lambda_handler --zip-file fileb://lambda_function.zip --timeout 30 --memory-size 256 --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Lambda function created successfully" -ForegroundColor $Green
    } else {
        Write-Host "❌ Failed to create Lambda function" -ForegroundColor $Red
        Write-Host "💡 This might be due to IAM role propagation. Try running the script again in 2-3 minutes." -ForegroundColor $Yellow
        exit 1
    }
}

# Step 4: Test Lambda Function
Write-Host "🧪 Testing Lambda function..." -ForegroundColor $Blue

$TestPayload = @"
{
  "httpMethod": "POST",
  "path": "/test",
  "body": "{\"test\": true}"
}
"@

$TestPayload | Out-File -FilePath "test-payload.json" -Encoding UTF8

$TestResult = aws lambda invoke --function-name $FunctionName --payload file://test-payload.json response.json --region $Region

if ($LASTEXITCODE -eq 0) {
    $Response = Get-Content response.json | ConvertFrom-Json
    Write-Host "✅ Lambda function test successful!" -ForegroundColor $Green
    Write-Host "Response: $($Response.body)" -ForegroundColor $Blue
} else {
    Write-Host "⚠️  Lambda test had issues, but function is created" -ForegroundColor $Yellow
}

# Cleanup temporary files
Remove-Item -Path "trust-policy.json", "lambda-policy.json", "test-payload.json", "response.json" -ErrorAction SilentlyContinue

Write-Host "✅ Core AWS resources deployed successfully!" -ForegroundColor $Green
Write-Host "=================================================================="
Write-Host "📋 Deployment Summary:" -ForegroundColor $Blue
Write-Host "DynamoDB Table: " -NoNewline; Write-Host "TradingAlerts" -ForegroundColor $Green
Write-Host "Lambda Function: " -NoNewline; Write-Host "$FunctionName" -ForegroundColor $Green
Write-Host "IAM Role: " -NoNewline; Write-Host "$RoleName" -ForegroundColor $Green
Write-Host ""
Write-Host "🔗 AWS Console Links:" -ForegroundColor $Blue
Write-Host "DynamoDB: https://console.aws.amazon.com/dynamodb/home?region=$Region#tables:selected=TradingAlerts"
Write-Host "Lambda: https://console.aws.amazon.com/lambda/home?region=$Region#/functions/$FunctionName"
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor $Yellow
Write-Host "1. Create API Gateway (we'll do this next)"
Write-Host "2. Get your webhook URL"
Write-Host "3. Test with TradingView"
Write-Host ""
Write-Host "🎉 Phase 1 Complete! Ready for API Gateway setup." -ForegroundColor $Green

# Return to original directory
Set-Location ..

# Clean up deployment directory (optional)
# Remove-Item -Path $DeployDir -Recurse -Force

Write-Host ""
Write-Host "💾 Deployment files saved in: $DeployDir" -ForegroundColor $Blue
Write-Host "🚀 Run this script completed successfully!" -ForegroundColor $Green
'@

$WindowsDeploymentScript | Out-File -FilePath "deploy.ps1" -Encoding UTF8
