# ==============================================================================
# TRADING AUTOMATION SYSTEM - WEBHOOK LISTENER (PORT 80)
# ==============================================================================
# 
# NOTE: Running on port 80 requires administrator/root privileges
# 
# Windows: Run Command Prompt as Administrator
# Mac/Linux: Run with sudo: sudo python webhook_listener_port80.py
#
# ==============================================================================

from flask import Flask, request, jsonify
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_alerts.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

class AlertProcessor:
    def __init__(self):
        self.alerts_received = []
        print("📊 AlertProcessor initialized - Ready to receive alerts!")
    
    def process_alert(self, alert_data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_data['timestamp'] = timestamp
        alert_data['processed'] = False
        
        self.alerts_received.append(alert_data)
        logging.info(f"New Alert Received: {alert_data}")
        self.print_alert_details(alert_data)
        
        return alert_data
    
    def print_alert_details(self, alert_data):
        print("\n" + "="*50)
        print(f"🚨 ALERT RECEIVED AT: {alert_data.get('timestamp', 'Unknown')}")
        print("="*50)
        print(f"📋 Alert Name: {alert_data.get('ALERTNAME', 'Not specified')}")
        print(f"📈 Symbol: {alert_data.get('symbol', 'Not specified')}")
        print(f"💰 Limit Price: {alert_data.get('limit_price', 'Not specified')}")
        print(f"📊 Capital %: {alert_data.get('capital_percent', 'Not specified')}")
        print(f"📦 Lot Size: {alert_data.get('lot_size', 'Not specified')}")
        print(f"🔪 Order Slicing Value: {alert_data.get('order_slicing_value', 'Not specified')}")
        print("="*50)
        
        if 'symbol' in alert_data and alert_data['symbol']:
            self.parse_symbol_info(alert_data['symbol'])
    
    def parse_symbol_info(self, symbol):
        try:
            print(f"🔍 Parsing Symbol: {symbol}")
            
            index_name = ""
            expiry_date = ""
            option_type = ""
            strike_price = ""
            
            if 'P' in symbol:
                parts = symbol.split('P')
                if len(parts) == 2:
                    prefix = parts[0]
                    strike_price = parts[1]
                    option_type = "PUT"
            elif 'C' in symbol:
                parts = symbol.split('C')
                if len(parts) == 2:
                    prefix = parts[0]
                    strike_price = parts[1]
                    option_type = "CALL"
            
            if len(prefix) >= 6:
                index_name = prefix[:-6]
                expiry_date = prefix[-6:]
            
            print(f"📊 Parsed Symbol Components:")
            print(f"   🏛️  Index: {index_name}")
            print(f"   📅 Expiry: {expiry_date} (YYMMDD format)")
            print(f"   📈 Type: {option_type}")
            print(f"   💲 Strike: {strike_price}")
            
        except Exception as e:
            print(f"❌ Error parsing symbol: {e}")
    
    def get_all_alerts(self):
        return self.alerts_received
    
    def get_recent_alerts(self, count=5):
        return self.alerts_received[-count:] if self.alerts_received else []

alert_processor = AlertProcessor()

@app.route('/webhook', methods=['POST'])
def webhook():
    print("\n🌐 Webhook endpoint called - Processing incoming request...")
    
    try:
        alert_data = request.get_json()
        print(f"📨 Raw data received: {alert_data}")
        
        if not alert_data:
            print("❌ No data received in request")
            return jsonify({'error': 'No data received'}), 400
        
        print("✅ Valid JSON data received, processing alert...")
        processed_alert = alert_processor.process_alert(alert_data)
        
        print(f"✅ Alert processed successfully - Total alerts: {len(alert_processor.alerts_received)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Alert received and processed',
            'alert_id': len(alert_processor.alerts_received),
            'timestamp': processed_alert['timestamp']
        }), 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(error_msg)
        
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    print("📊 Status endpoint called")
    
    return jsonify({
        'status': 'running',
        'message': 'TradingView Webhook Listener is operational',
        'total_alerts': len(alert_processor.alerts_received),
        'server_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'endpoints_available': ['/webhook', '/status', '/alerts', '/test']
    }), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    count = request.args.get('count', type=int, default=10)
    print(f"📋 Alerts endpoint called - Requesting {count} recent alerts")
    
    alerts = alert_processor.get_recent_alerts(count)
    
    return jsonify({
        'alerts': alerts,
        'alerts_returned': len(alerts),
        'total_count': len(alert_processor.alerts_received),
        'message': f'Returning {len(alerts)} most recent alerts'
    }), 200

@app.route('/test', methods=['POST'])
def test_webhook():
    print("🧪 Test endpoint called - Generating test alert...")
    
    test_alert = {
        'ALERTNAME': 'TEST ALERT',
        'symbol': 'NIFTY250930P25800',
        'limit_price': '25800',
        'capital_percent': '50',
        'lot_size': '75',
        'order_slicing_value': '1800',
        'test_mode': True
    }
    
    print(f"🧪 Processing test alert: {test_alert}")
    processed_alert = alert_processor.process_alert(test_alert)
    
    return jsonify({
        'status': 'test_success',
        'message': 'Test alert generated and processed',
        'test_alert': processed_alert,
        'total_alerts_now': len(alert_processor.alerts_received)
    }), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING TRADINGVIEW WEBHOOK LISTENER - PORT 80")
    print("="*60)
    print("⚠️  IMPORTANT: This requires administrator/root privileges!")
    print("   Windows: Run as Administrator")
    print("   Mac/Linux: Run with sudo")
    print("\n📡 Server Information:")
    print("   🌐 Server URL: http://localhost")
    print("   📥 Webhook Endpoint: http://localhost/webhook")
    print("   📊 Status Check: http://localhost/status")
    print("   📋 View Alerts: http://localhost/alerts")
    print("   🧪 Test Endpoint: http://localhost/test")
    print("\n📝 Log File: trading_alerts.log")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Run on port 80 (requires admin privileges)
        app.run(
            host='0.0.0.0',
            port=80,           # Standard HTTP port
            debug=True
        )
        
    except PermissionError:
        print("\n❌ PERMISSION DENIED!")
        print("🔧 Solutions:")
        print("   Windows: Run Command Prompt as Administrator")
        print("   Mac/Linux: Run with sudo: sudo python webhook_listener_port80.py")
        print("   Alternative: Use ngrok with original port 5000 version")
        
    except OSError as e:
        if "Address already in use" in str(e):
            print("\n❌ PORT 80 ALREADY IN USE!")
            print("🔧 Solutions:")
            print("   1. Stop other web servers (Apache, IIS, etc.)")
            print("   2. Use ngrok with original port 5000 version (Recommended)")
        else:
            print(f"\n❌ Error: {e}")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutdown requested by user")
        print("✅ Webhook listener stopped successfully")
        
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("🔧 Recommended: Use ngrok solution instead")