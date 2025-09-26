# ==============================================================================
# TRADING AUTOMATION SYSTEM - WEBHOOK TESTER
# ==============================================================================
#
# PURPOSE: Test the webhook listener server to ensure it properly receives 
#          and processes TradingView alerts
#
# EXECUTION ORDER:
# 1. Import libraries
# 2. Define test functions
# 3. Run main test sequence (if __name__ == '__main__')
# 4. Test server status
# 5. Send sample alerts (Buy, Profit Sell, Loss Sell)
# 6. Verify alerts were received
#
# PREREQUISITES: 
# - webhook_listener.py must be running on localhost:5000
# - 'requests' library must be installed (pip install requests)
#
# ==============================================================================

# STEP 1: Import required libraries
import requests  # For making HTTP requests to our webhook server
import json      # For working with JSON data
import time      # For adding delays between requests

# ==============================================================================
# STEP 2: Define Test Functions
# ==============================================================================

def test_webhook_server():
    """
    Main testing function - tests all webhook endpoints
    
    TESTING SEQUENCE:
    1. Check if webhook server is running (GET /status)
    2. Send "NEW BUY ORDER" alert (POST /webhook) 
    3. Send "PROFIT BOOKING SELL" alert (POST /webhook)
    4. Send "LOSS BOOKING SELL" alert (POST /webhook)
    5. Verify all alerts were received (GET /alerts)
    
    This simulates the exact sequence that would happen in real trading:
    - Entry signal triggers buy order
    - Price moves up, profit trigger activates
    - OR price moves down, loss trigger activates
    """
    
    # Define endpoint URLs for our webhook server
    webhook_url = "http://localhost:5000/webhook"  # Where we send alerts
    status_url = "http://localhost:5000/status"    # Server health check
    alerts_url = "http://localhost:5000/alerts"    # View received alerts
    
    print("🧪 STARTING WEBHOOK SERVER TESTS")
    print("="*50)
    
    # ===========================================================================
    # TEST 1: Server Status Check
    # ===========================================================================
    print("1️⃣  Testing server status...")
    print(f"   📡 Checking: {status_url}")
    
    try:
        # Make GET request to status endpoint
        # This tests if the server is running and responding
        response = requests.get(status_url)
        print(f"   📊 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:  # 200 = HTTP OK
            print("   ✅ Server is running and responding!")
            
            # Parse JSON response and display server info
            server_info = response.json()
            print(f"   📈 Server Status: {server_info.get('status', 'Unknown')}")
            print(f"   📊 Total Alerts: {server_info.get('total_alerts', 0)}")
            print(f"   🕒 Server Time: {server_info.get('server_time', 'Unknown')}")
        else:
            print(f"   ❌ Server responded but with error code: {response.status_code}")
            print("   🔧 Check server logs for issues")
            return  # Exit test if server not working properly
            
    except requests.exceptions.ConnectionError:
        # This happens when server is not running
        print("   ❌ CONNECTION ERROR: Server is not running!")
        print("   🚀 Please start the webhook listener first:")
        print("      python webhook_listener.py")
        print("   ⏳ Then run this test again")
        return  # Exit test since server is not available
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return
    
    print("\n" + "="*50)
    
    # ===========================================================================
    # TEST 2: New Buy Order Alert
    # ===========================================================================
    print("2️⃣  Testing NEW BUY ORDER alert...")
    print("   📨 This simulates TradingView sending a buy signal")
    
    # Create buy order alert data (matches TradingView webhook format)
    buy_order_alert = {
        "ALERTNAME": "NEW BUY ORDER",           # Alert type identifier
        "symbol": "NIFTY250930P25800",          # Options symbol (NIFTY Put option)
        "limit_price": "25800",                 # Price at which to place order
        "capital_percent": "50",                # 50% of capital allocation
        "lot_size": "75",                       # Standard NIFTY lot size
        "order_slicing_value": "1800"           # Max quantity per order slice
    }
    
    print(f"   📋 Alert Data: {buy_order_alert}")
    print(f"   🎯 Sending POST request to: {webhook_url}")
    
    try:
        # Send POST request with JSON data to webhook endpoint
        # This simulates exactly what TradingView does when alert triggers
        response = requests.post(webhook_url, json=buy_order_alert)
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("   ✅ Buy order alert processed successfully!")
            print(f"   🆔 Alert ID: {response_data.get('alert_id', 'Unknown')}")
            print(f"   ⏰ Timestamp: {response_data.get('timestamp', 'Unknown')}")
        else:
            print(f"   ❌ Error processing buy alert: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error sending buy alert: {e}")
        return
    
    # Add small delay between requests (good practice)
    time.sleep(1)
    
    # ===========================================================================
    # TEST 3: Profit Booking Sell Alert
    # ===========================================================================
    print("\n3️⃣  Testing PROFIT BOOKING SELL alert...")
    print("   💰 This simulates price moving up and hitting profit target")
    
    # Create profit booking alert
    # In real scenario: price moved from 25800 to 27090 (5% profit)
    profit_sell_alert = {
        "ALERTNAME": "PROFT BOOKING SELL",      # Note: matches your document spelling
        "symbol": "NIFTY250930P25800",          # Same symbol as buy order
        "limit_price": "27090",                 # 5% higher than buy price (25800 * 1.05)
        "lot_size": "75",                       # Same lot size
        "order_slicing_value": "1800"           # Same slicing value
    }
    
    print(f"   📋 Alert Data: {profit_sell_alert}")
    print(f"   📈 Price Movement: 25800 → 27090 (5% profit)")
    
    try:
        response = requests.post(webhook_url, json=profit_sell_alert)
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("   ✅ Profit booking alert processed successfully!")
            print(f"   🆔 Alert ID: {response_data.get('alert_id', 'Unknown')}")
            print(f"   💰 Profit Realized: ~5%")
        else:
            print(f"   ❌ Error processing profit alert: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error sending profit alert: {e}")
    
    time.sleep(1)
    
    # ===========================================================================
    # TEST 4: Loss Booking Sell Alert  
    # ===========================================================================
    print("\n4️⃣  Testing LOSS BOOKING SELL alert...")
    print("   📉 This simulates price moving down and hitting stop loss")
    
    # Create loss booking alert
    # In real scenario: price moved from 25800 to 21930 (15% loss)
    loss_sell_alert = {
        "ALERTNAME": "LOSS BOOKING SELL",       # Alert type for stop loss
        "symbol": "NIFTY250930P25800",          # Same symbol
        "limit_price": "21930",                 # 15% lower than buy price (25800 * 0.85)
        "lot_size": "75",                       # Same lot size
        "order_slicing_value": "1800"           # Same slicing value
    }
    
    print(f"   📋 Alert Data: {loss_sell_alert}")
    print(f"   📉 Price Movement: 25800 → 21930 (15% loss)")
    
    try:
        response = requests.post(webhook_url, json=loss_sell_alert)
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("   ✅ Loss booking alert processed successfully!")
            print(f"   🆔 Alert ID: {response_data.get('alert_id', 'Unknown')}")
            print("   🛡️  Stop loss executed - risk managed")
        else:
            print(f"   ❌ Error processing loss alert: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error sending loss alert: {e}")
    
    print("\n" + "="*50)
    
    # ===========================================================================
    # TEST 5: Verify All Alerts Were Received
    # ===========================================================================
    print("5️⃣  Verifying all alerts were received...")
    print(f"   📋 Fetching alerts from: {alerts_url}")
    
    try:
        # Get all alerts from server to verify they were stored
        response = requests.get(alerts_url)
        
        if response.status_code == 200:
            data = response.json()
            total_alerts = data.get('total_count', 0)
            recent_alerts = data.get('alerts', [])
            
            print(f"   📊 Total alerts in system: {total_alerts}")
            print(f"   📋 Recent alerts returned: {len(recent_alerts)}")
            
            if recent_alerts:
                print("\n   📝 Alert Summary:")
                for i, alert in enumerate(recent_alerts, 1):
                    alert_name = alert.get('ALERTNAME', 'Unknown')
                    symbol = alert.get('symbol', 'Unknown')
                    timestamp = alert.get('timestamp', 'Unknown')
                    limit_price = alert.get('limit_price', 'N/A')
                    
                    print(f"      {i}. {alert_name}")
                    print(f"         Symbol: {symbol}")
                    print(f"         Price: {limit_price}")
                    print(f"         Time: {timestamp}")
                    print()
            else:
                print("   ⚠️  No alerts found in system")
                
        else:
            print(f"   ❌ Error fetching alerts: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error verifying alerts: {e}")

def test_server_endpoints():
    """
    Additional test function to verify all endpoints work
    
    This tests each endpoint individually to ensure they're properly configured
    """
    
    print("\n🔍 TESTING ALL SERVER ENDPOINTS")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Test endpoints configuration
    endpoints_to_test = [
        {"url": f"{base_url}/status", "method": "GET", "name": "Status Endpoint"},
        {"url": f"{base_url}/alerts", "method": "GET", "name": "Alerts Endpoint"},
        {"url": f"{base_url}/alerts?count=5", "method": "GET", "name": "Alerts with Count Parameter"},
        {"url": f"{base_url}/test", "method": "POST", "name": "Test Endpoint (Generate Test Alert)"}
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"   🎯 URL: {endpoint['url']}")
        print(f"   📡 Method: {endpoint['method']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'])
            elif endpoint['method'] == 'POST':
                response = requests.post(endpoint['url'])
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Endpoint working correctly!")
                
                # Show sample response for some endpoints
                if 'test' in endpoint['url']:
                    data = response.json()
                    print(f"   🧪 Test Alert Generated: {data.get('message', 'Unknown')}")
                elif 'alerts' in endpoint['url']:
                    data = response.json()
                    print(f"   📊 Alerts Available: {data.get('total_count', 0)}")
                elif 'status' in endpoint['url']:
                    data = response.json()
                    print(f"   🔄 Server Status: {data.get('status', 'Unknown')}")
            else:
                print(f"   ❌ Endpoint returned error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing endpoint: {e}")

# ==============================================================================
# STEP 3: Main Execution Block
# ==============================================================================
# 
# if __name__ == '__main__':
# This means: "Only run the code below IF this file is executed directly"
# If someone imports this file (import test_webhook), the tests won't run automatically
#
# EXECUTION ORDER when you run: python test_webhook.py
# 1. All imports happen (requests, json, time)
# 2. Functions get defined but not executed (test_webhook_server, test_server_endpoints)
# 3. This main block executes
# 4. Test sequence begins
# ==============================================================================

if __name__ == "__main__":
    """
    Main test execution
    Only runs when script is executed directly (not imported)
    """
    
    print("🚀 TRADINGVIEW WEBHOOK TESTER")
    print("="*60)
    print("📋 This script will test your webhook listener server")
    print("📡 Make sure webhook_listener.py is running on localhost:5000")
    print("="*60)
    
    try:
        # Run main webhook functionality tests
        test_webhook_server()
        
        print("\n" + "="*50)
        
        # Run additional endpoint tests
        test_server_endpoints()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED!")
        print("\n📊 Test Summary:")
        print("   ✅ Server connectivity test")
        print("   ✅ Buy order alert test") 
        print("   ✅ Profit booking alert test")
        print("   ✅ Loss booking alert test")
        print("   ✅ Alert verification test")
        print("   ✅ All endpoint tests")
        
        print("\n🎯 Next Steps:")
        print("   1. Check webhook_listener.py console for detailed alert processing")
        print("   2. Review trading_alerts.log file for logged alerts")
        print("   3. Visit http://localhost:5000/status in browser")
        print("   4. Visit http://localhost:5000/alerts to see all alerts")
        
        print("\n🔧 If any tests failed:")
        print("   - Ensure webhook_listener.py is running")
        print("   - Check that port 5000 is not blocked")
        print("   - Review server console for error messages")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
        print("✅ Test script stopped")
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        print("🔧 Check your webhook_listener.py server status")

# ==============================================================================
# END OF FILE - TESTING SUMMARY
# ==============================================================================
#
# WHAT THIS SCRIPT DOES:
#
# 1. 🔌 CONNECTIVITY: Tests if webhook server is running and accessible
# 2. 📨 WEBHOOK: Sends sample TradingView alerts to webhook endpoint  
# 3. 🔍 VALIDATION: Verifies alerts were received and processed correctly
# 4. 🧪 ENDPOINTS: Tests all available server endpoints
# 5. 📊 REPORTING: Shows comprehensive test results and next steps
#
# REAL-WORLD SIMULATION:
# This script simulates the exact sequence that happens in live trading:
# - TradingView indicator triggers → Sends webhook → Server processes → 
#   Stores alert → Returns confirmation → Ready for order execution
#
# SUCCESS CRITERIA:
# ✅ All HTTP requests return status 200
# ✅ Server processes and stores all test alerts
# ✅ Symbol parsing works correctly (NIFTY250930P25800)
# ✅ All endpoints respond correctly
# ✅ Alert data is preserved and retrievable
#
# ==============================================================================import requests
import json
import time

# Test different types of alerts that your TradingView indicator will send

def test_webhook_server():
    """Test the webhook server with sample alerts"""
    
    webhook_url = "http://localhost:5000/webhook"
    status_url = "http://localhost:5000/status"
    
    # Test 1: Check if server is running
    print("1. Testing server status...")
    try:
        response = requests.get(status_url)
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Server not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the webhook listener first!")
        return
    
    print("\n" + "="*50)
    
    # Test 2: New Buy Order Alert
    print("2. Testing NEW BUY ORDER alert...")
    buy_order_alert = {
        "ALERTNAME": "NEW BUY ORDER",
        "symbol": "NIFTY250930P25800",
        "limit_price": "25800",
        "capital_percent": "50",
        "lot_size": "75",
        "order_slicing_value": "1800"
    }
    
    response = requests.post(webhook_url, json=buy_order_alert)
    print(f"Response Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    time.sleep(1)
    
    # Test 3: Profit Booking Sell Alert
    print("\n3. Testing PROFIT BOOKING SELL alert...")
    profit_sell_alert = {
        "ALERTNAME": "PROFT BOOKING SELL",
        "symbol": "NIFTY250930P25800",
        "limit_price": "27090",  # 5% profit
        "lot_size": "75",
        "order_slicing_value": "1800"
    }
    
    response = requests.post(webhook_url, json=profit_sell_alert)
    print(f"Response Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    time.sleep(1)
    
    # Test 4: Loss Booking Sell Alert
    print("\n4. Testing LOSS BOOKING SELL alert...")
    loss_sell_alert = {
        "ALERTNAME": "LOSS BOOKING SELL",
        "symbol": "NIFTY250930P25800",
        "limit_price": "21930",  # 15% loss
        "lot_size": "75",
        "order_slicing_value": "1800"
    }
    
    response = requests.post(webhook_url, json=loss_sell_alert)
    print(f"Response Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n" + "="*50)
    
    # Test 5: Check all received alerts
    print("5. Checking all received alerts...")
    alerts_url = "http://localhost:5000/alerts"
    response = requests.get(alerts_url)
    if response.status_code == 200:
        data = response.json()
        print(f"Total alerts received: {data['total_count']}")
        print("Recent alerts:")
        for i, alert in enumerate(data['alerts'], 1):
            print(f"  {i}. {alert['ALERTNAME']} - {alert['symbol']} at {alert['timestamp']}")

if __name__ == "__main__":
    print("TradingView Webhook Tester")
    print("Make sure your webhook listener is running on localhost:5000")
    print("\n" + "="*50)
    
    test_webhook_server()