# ==============================================================================
# TRADING AUTOMATION SYSTEM - WEBHOOK LISTENER
# ==============================================================================
# 
# EXECUTION ORDER:
# 1. Import libraries and configure logging
# 2. Create Flask app instance 
# 3. Define AlertProcessor class (data processing logic)
# 4. Create AlertProcessor instance
# 5. Define route handlers (URL endpoints with @app.route decorators)
# 6. Start Flask server (if __name__ == '__main__')
#
# ==============================================================================

# STEP 1: Import required libraries
from flask import Flask, request, jsonify  # Flask: web framework, request: HTTP data, jsonify: JSON responses
import json                                 # For JSON data manipulation
from datetime import datetime              # For timestamps
import logging                            # For logging alerts and errors

# STEP 2: Configure logging system
# This sets up logging to both file and console simultaneously
logging.basicConfig(
    level=logging.INFO,                    # Log INFO level and above (INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format: timestamp - level - message
    handlers=[
        logging.FileHandler('trading_alerts.log'),        # Save logs to file
        logging.StreamHandler()                           # Also print to console
    ]
)

# STEP 3: Create Flask application instance
# Flask(__name__) creates a web application instance
# __name__ helps Flask locate templates, static files, etc.
app = Flask(__name__)

# STEP 4: Define AlertProcessor class
# This class handles all alert processing logic - receiving, storing, parsing
class AlertProcessor:
    """
    AlertProcessor handles incoming trading alerts from TradingView
    
    Main responsibilities:
    - Store incoming alerts with timestamps
    - Parse symbol information (e.g., NIFTY250930P25800 -> Index, Expiry, Type, Strike)
    - Format and display alert details
    - Maintain history of all alerts
    """
    
    def __init__(self):
        """
        Initialize the AlertProcessor
        Creates an empty list to store all incoming alerts
        """
        self.alerts_received = []  # List to store all alerts - acts like a database
        print("📊 AlertProcessor initialized - Ready to receive alerts!")
    
    def process_alert(self, alert_data):
        """
        Main method to process incoming alert from TradingView
        
        EXECUTION FLOW:
        1. Add timestamp to alert data
        2. Store alert in alerts_received list  
        3. Log the alert to file and console
        4. Print formatted alert details
        5. Return processed alert
        
        Args:
            alert_data (dict): Raw alert data from TradingView webhook
            
        Returns:
            dict: Processed alert data with timestamp
        """
        
        # Add current timestamp to the alert
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_data['timestamp'] = timestamp      # When alert was received
        alert_data['processed'] = False          # Flag for future processing
        
        # Store the alert in our "database" (list)
        self.alerts_received.append(alert_data)
        
        # Log to both file and console using the logging system
        logging.info(f"New Alert Received: {alert_data}")
        
        # Print formatted details for immediate visibility
        self.print_alert_details(alert_data)
        
        return alert_data  # Return processed alert
    
    def print_alert_details(self, alert_data):
        """
        Print formatted alert details to console for immediate visibility
        
        Args:
            alert_data (dict): Alert data to format and display
        """
        
        # Print decorative header
        print("\n" + "="*50)
        print(f"🚨 ALERT RECEIVED AT: {alert_data.get('timestamp', 'Unknown')}")
        print("="*50)
        
        # Print each field with fallback to 'Not specified' if missing
        print(f"📋 Alert Name: {alert_data.get('ALERTNAME', 'Not specified')}")
        print(f"📈 Symbol: {alert_data.get('symbol', 'Not specified')}")
        print(f"💰 Limit Price: {alert_data.get('limit_price', 'Not specified')}")
        print(f"📊 Capital %: {alert_data.get('capital_percent', 'Not specified')}")
        print(f"📦 Lot Size: {alert_data.get('lot_size', 'Not specified')}")
        print(f"🔪 Order Slicing Value: {alert_data.get('order_slicing_value', 'Not specified')}")
        print("="*50)
        
        # If symbol exists, try to parse it (e.g., NIFTY250930P25800)
        if 'symbol' in alert_data and alert_data['symbol']:
            self.parse_symbol_info(alert_data['symbol'])
    
    def parse_symbol_info(self, symbol):
        """
        Parse options symbol into components
        
        Symbol format: NIFTY250930P25800
        - NIFTY: Index name
        - 250930: Expiry date (YYMMDD)
        - P: Option type (P=PUT, C=CALL)
        - 25800: Strike price
        
        Args:
            symbol (str): Symbol string to parse
        """
        try:
            print(f"🔍 Parsing Symbol: {symbol}")
            
            # Initialize variables for parsed components
            index_name = ""
            expiry_date = ""
            option_type = ""
            strike_price = ""
            
            # Find option type by looking for 'P' (PUT) or 'C' (CALL)
            if 'P' in symbol:
                # Split on 'P' to separate prefix and strike
                parts = symbol.split('P')
                if len(parts) == 2:  # Should have exactly 2 parts after split
                    prefix = parts[0]        # Everything before 'P'
                    strike_price = parts[1]   # Everything after 'P'
                    option_type = "PUT"
            elif 'C' in symbol:
                # Split on 'C' for CALL options
                parts = symbol.split('C')
                if len(parts) == 2:
                    prefix = parts[0]
                    strike_price = parts[1]
                    option_type = "CALL"
            
            # Extract index name and expiry from prefix
            # Assumption: Last 6 digits of prefix are expiry date (YYMMDD)
            if len(prefix) >= 6:
                index_name = prefix[:-6]    # Everything except last 6 characters
                expiry_date = prefix[-6:]   # Last 6 characters
            
            # Display parsed information
            print(f"📊 Parsed Symbol Components:")
            print(f"   🏛️  Index: {index_name}")
            print(f"   📅 Expiry: {expiry_date} (YYMMDD format)")
            print(f"   📈 Type: {option_type}")
            print(f"   💲 Strike: {strike_price}")
            
        except Exception as e:
            # If parsing fails, show error but don't crash
            print(f"❌ Error parsing symbol: {e}")
            print(f"   Symbol format might be different than expected")
    
    def get_all_alerts(self):
        """
        Return all received alerts
        
        Returns:
            list: All alerts stored in alerts_received
        """
        return self.alerts_received
    
    def get_recent_alerts(self, count=5):
        """
        Return most recent alerts (useful for API endpoints)
        
        Args:
            count (int): Number of recent alerts to return
            
        Returns:
            list: Last 'count' alerts, or all if fewer than 'count' exist
        """
        return self.alerts_received[-count:] if self.alerts_received else []

# STEP 5: Create AlertProcessor instance
# This creates a single instance that will handle all alerts throughout the application lifetime
alert_processor = AlertProcessor()

# ==============================================================================
# STEP 6: Define Flask Route Handlers (URL Endpoints)
# ==============================================================================
# 
# @app.route() is a DECORATOR that tells Flask:
# - Which URL path should trigger this function
# - Which HTTP methods are allowed (GET, POST, etc.)
# - When someone visits the URL, execute the decorated function
#
# DECORATOR EXPLANATION:
# A decorator is a function that wraps another function to extend its behavior
# @app.route('/webhook', methods=['POST']) does this:
#   1. Takes the function below it (webhook)  
#   2. Registers it with Flask as a handler for POST requests to '/webhook'
#   3. When POST request comes to /webhook, Flask calls the webhook function
# ==============================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    MAIN WEBHOOK ENDPOINT - This is where TradingView sends alerts
    
    DECORATOR EXPLANATION:
    @app.route('/webhook', methods=['POST']) tells Flask:
    - Listen for requests to URL: http://localhost:5000/webhook
    - Only accept POST methods (not GET, PUT, DELETE)
    - When POST request arrives, execute this webhook() function
    
    EXECUTION FLOW:
    1. TradingView sends POST request with JSON alert data
    2. Flask receives request and calls this function
    3. Extract JSON data from request
    4. Validate data exists
    5. Process alert using AlertProcessor
    6. Return success/error response to TradingView
    
    Returns:
        JSON response with status and alert info
    """
    
    print("\n🌐 Webhook endpoint called - Processing incoming request...")
    
    try:
        # Extract JSON data from the incoming request
        # request.get_json() reads the POST body and converts JSON to Python dict
        alert_data = request.get_json()
        print(f"📨 Raw data received: {alert_data}")
        
        # Validate that we actually received data
        if not alert_data:
            print("❌ No data received in request")
            return jsonify({'error': 'No data received'}), 400  # HTTP 400 = Bad Request
        
        print("✅ Valid JSON data received, processing alert...")
        
        # Process the alert using our AlertProcessor instance
        processed_alert = alert_processor.process_alert(alert_data)
        
        print(f"✅ Alert processed successfully - Total alerts: {len(alert_processor.alerts_received)}")
        
        # Return success response to TradingView (important for webhook confirmation)
        return jsonify({
            'status': 'success',
            'message': 'Alert received and processed',
            'alert_id': len(alert_processor.alerts_received),  # Unique ID for this alert
            'timestamp': processed_alert['timestamp']
        }), 200  # HTTP 200 = Success
        
    except Exception as e:
        # If anything goes wrong, log error and return error response
        error_msg = f"Error processing webhook: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(error_msg)
        
        return jsonify({'error': str(e)}), 500  # HTTP 500 = Internal Server Error

@app.route('/status', methods=['GET'])
def status():
    """
    STATUS ENDPOINT - Check if server is running and get basic stats
    
    DECORATOR EXPLANATION:
    @app.route('/status', methods=['GET']) tells Flask:
    - Listen for GET requests to: http://localhost:5000/status
    - When GET request arrives, execute this status() function
    
    This is useful for:
    - Health checks
    - Monitoring server status
    - Getting basic statistics
    
    Returns:
        JSON with server status and stats
    """
    
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
    """
    ALERTS ENDPOINT - View received alerts (with optional count parameter)
    
    DECORATOR EXPLANATION:
    @app.route('/alerts', methods=['GET']) tells Flask:
    - Listen for GET requests to: http://localhost:5000/alerts
    - Optional query parameter: ?count=10 (http://localhost:5000/alerts?count=10)
    
    Usage examples:
    - GET /alerts -> Returns last 10 alerts
    - GET /alerts?count=5 -> Returns last 5 alerts  
    - GET /alerts?count=20 -> Returns last 20 alerts
    
    Returns:
        JSON with recent alerts and total count
    """
    
    # Extract 'count' parameter from URL query string, default to 10
    # Example: /alerts?count=5 -> count = 5
    count = request.args.get('count', type=int, default=10)
    print(f"📋 Alerts endpoint called - Requesting {count} recent alerts")
    
    # Get recent alerts using AlertProcessor
    alerts = alert_processor.get_recent_alerts(count)
    
    return jsonify({
        'alerts': alerts,
        'alerts_returned': len(alerts),
        'total_count': len(alert_processor.alerts_received),
        'message': f'Returning {len(alerts)} most recent alerts'
    }), 200

@app.route('/test', methods=['POST'])
def test_webhook():
    """
    TEST ENDPOINT - Generate a test alert to verify system works
    
    DECORATOR EXPLANATION:
    @app.route('/test', methods=['POST']) tells Flask:
    - Listen for POST requests to: http://localhost:5000/test
    - When called, generates a fake alert for testing
    
    This is useful for:
    - Testing the system without TradingView
    - Debugging alert processing logic
    - Demonstrating functionality
    
    Returns:
        JSON with test alert details
    """
    
    print("🧪 Test endpoint called - Generating test alert...")
    
    # Create a sample alert that matches TradingView format
    test_alert = {
        'ALERTNAME': 'TEST ALERT',
        'symbol': 'NIFTY250930P25800',
        'limit_price': '25800',
        'capital_percent': '50',
        'lot_size': '75',
        'order_slicing_value': '1800',
        'test_mode': True  # Flag to identify test alerts
    }
    
    print(f"🧪 Processing test alert: {test_alert}")
    
    # Process the test alert just like a real one
    processed_alert = alert_processor.process_alert(test_alert)
    
    return jsonify({
        'status': 'test_success',
        'message': 'Test alert generated and processed',
        'test_alert': processed_alert,
        'total_alerts_now': len(alert_processor.alerts_received)
    }), 200

# ==============================================================================
# STEP 7: Main Application Entry Point
# ==============================================================================
# 
# if __name__ == '__main__': 
# This special Python construct means:
# "Only run the code below IF this file is executed directly"
# "Don't run it if this file is imported as a module in another file"
#
# EXECUTION ORDER when you run: python webhook_listener.py
# 1. All imports happen first (Step 1)
# 2. Logging gets configured (Step 2) 
# 3. Flask app gets created (Step 3)
# 4. AlertProcessor class gets defined (Step 4)
# 5. AlertProcessor instance gets created (Step 5)
# 6. All route handlers get registered with Flask (Step 6)
# 7. This main block executes (Step 7)
# 8. Flask server starts and listens for requests
# ==============================================================================

if __name__ == '__main__':
    """
    Main application startup
    This block only runs when the script is executed directly
    """
    
    # Print startup information
    print("\n" + "="*60)
    print("🚀 STARTING TRADINGVIEW WEBHOOK LISTENER")
    print("="*60)
    print("📊 System Components:")
    print("   ✅ Flask Web Server")
    print("   ✅ AlertProcessor (Alert Handler)")
    print("   ✅ Logging System (File + Console)")
    print("   ✅ Symbol Parser (Options Symbols)")
    print("\n📡 Server Information:")
    print("   🌐 Server URL: http://localhost:5000")
    print("   📥 Webhook Endpoint: http://localhost:5000/webhook")
    print("   📊 Status Check: http://localhost:5000/status")
    print("   📋 View Alerts: http://localhost:5000/alerts")
    print("   🧪 Test Endpoint: http://localhost:5000/test")
    print("\n📝 Log File: trading_alerts.log")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Start the Flask development server
        # host='0.0.0.0' means accept connections from any IP address
        # port=5000 means listen on port 5000
        # debug=True enables:
        #   - Automatic restart when code changes
        #   - Detailed error messages  
        #   - Debug mode indicators
        app.run(
            host='0.0.0.0',    # Accept connections from any IP (not just localhost)
            port=5000,         # Listen on port 5000
            debug=True         # Enable debug mode for development
        )
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\n🛑 Server shutdown requested by user")
        print("✅ Webhook listener stopped successfully")
        print("📊 Final Statistics:")
        print(f"   Total alerts received: {len(alert_processor.alerts_received)}")
        print("   Log file saved: trading_alerts.log")
        print("\n👋 Goodbye!")
        
    except Exception as e:
        # Handle any other errors during server startup
        print(f"\n❌ Error starting server: {e}")
        print("🔧 Common solutions:")
        print("   - Check if port 5000 is already in use")
        print("   - Try running with administrator/sudo privileges")
        print("   - Check firewall settings")

# ==============================================================================
# END OF FILE - EXECUTION SUMMARY
# ==============================================================================
#
# WHEN THIS SCRIPT RUNS:
# 
# 1. 🏁 START: Python reads entire file and executes imports
# 2. ⚙️  SETUP: Logging, Flask app, AlertProcessor class definition
# 3. 🎯 REGISTER: All @app.route decorators register URL handlers with Flask
# 4. 🚀 LAUNCH: Main block starts Flask server on localhost:5000
# 5. 👂 LISTEN: Server waits for HTTP requests on registered endpoints
# 6. 🔄 PROCESS: When request comes in, appropriate handler function executes
# 7. 📨 RESPOND: Handler returns JSON response back to client
# 8. 🔁 REPEAT: Server continues listening until stopped with Ctrl+C
#
# FLASK REQUEST FLOW:
# Request comes in → Flask checks URL → Finds matching @app.route → 
# Calls decorated function → Function processes → Returns response → 
# Flask sends response back to client
#
# ==============================================================================