import requests
import datetime
import uuid
import os
import json
import time
from urllib.parse import quote_plus

class APIManager:
    def __init__(self):
        self.mail_api = "https://thegroup11.com/api/sendmail"
        self.api_key = "dGhlZ3JvdXAxMQ=="
        self.demo_email = "ritik.arora24@vit.edu"

        self.cashfree_app_id = "5296288378ce57f53f3d056479826925"
        self.cashfree_secret = "b6230352680a8bf32f7173d7e7a27db664dfda78"
        self.cashfree_base_url = "https://api.cashfree.com/pg"
        
        self.api_base_url = "https://thegroup11.com/api/violations"
        
        os.makedirs('violations', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
    
    def test_api_connection(self):
        try:
            print("🧪 Testing API connection...")
            
            response = requests.get(f"{self.api_base_url}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ API is working perfectly!")
                    print(f"📊 API Message: {result.get('message', 'N/A')}")
                    
                    stats_response = requests.get(f"{self.api_base_url}/stats", timeout=10)
                    if stats_response.status_code == 200:
                        stats_result = stats_response.json()
                        if stats_result.get('success'):
                            stats = stats_result.get('data', {})
                            print(f"📈 Current Stats:")
                            print(f"   Total Tolls: {stats.get('total', 0)}")
                            print(f"   Paid: {stats.get('paid', 0)}")
                            print(f"   Pending: {stats.get('pending', 0)}")
                            print(f"   Revenue: ₹{stats.get('revenue', 0)}")
                    return True
                else:
                    print(f"⚠️ API responded but with error: {result.get('error', 'Unknown')}")
            else:
                print(f"❌ API returned status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API connection test failed: {e}")
            print("💡 Make sure your API is running at: https://thegroup11.com/api/violations")
        
        return False
    
    def create_cashfree_payment_link(self, amount, license_plate, violation_id):
        try:
            order_id = f"order_{int(time.time())}"
            customer_id = f"cust_{int(time.time())}"
            
            print(f"Creating Cashfree payment session for order: {order_id}")
            
            url = "https://api.cashfree.com/pg/orders"
            headers = {
                'x-client-id': self.cashfree_app_id,
                'x-client-secret': self.cashfree_secret,
                'x-api-version': '2023-08-01',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "order_id": order_id,
                "order_amount": float(amount),
                "order_currency": "INR",
                "customer_details": {
                    "customer_id": customer_id,
                    "customer_name": f"Vehicle Owner {license_plate}",
                    "customer_email": self.demo_email,
                    "customer_phone": "9999999999"
                },
                "order_meta": {
                    "return_url": f"https://thegroup11.com/payment_success.php?order_id={order_id}&violation_id={violation_id}"
                }
            }
            
            print(f"Trying production Cashfree API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "payment_session_id" in data and data["payment_session_id"]:
                    print(f"✅ SUCCESS! Got payment session from production!")
                    return self.create_embedded_cashfree_form(data["payment_session_id"], amount, license_plate, violation_id, order_id, False)
            
            print(f"Production failed, trying sandbox...")
            sandbox_url = "https://sandbox.cashfree.com/pg/orders"
            sandbox_response = requests.post(sandbox_url, headers=headers, json=payload, timeout=30)
            
            if sandbox_response.status_code == 200:
                sandbox_data = sandbox_response.json()
                if "payment_session_id" in sandbox_data and sandbox_data["payment_session_id"]:
                    print(f"✅ SUCCESS! Got payment session from sandbox!")
                    return self.create_embedded_cashfree_form(sandbox_data["payment_session_id"], amount, license_plate, violation_id, order_id, True)
            
            print("Both APIs failed, creating fallback Cashfree form...")
            return self.create_fallback_cashfree_form(amount, license_plate, violation_id, order_id)
            
        except Exception as e:
            print(f"Error creating payment session: {e}")
            return self.create_fallback_cashfree_form(amount, license_plate, violation_id, f"FALLBACK_{violation_id}")

    def create_embedded_cashfree_form(self, payment_session_id, amount, license_plate, violation_id, order_id, is_sandbox=False):
        try:
            if is_sandbox:
                checkout_url = "https://sandbox.cashfree.com/pg/view/sessions/checkout"
            else:
                checkout_url = "https://api.cashfree.com/pg/view/sessions/checkout"
            
            browser_meta = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "screen_resolution": "1920x1080",
                "color_depth": "24",
                "timezone_offset": "-330"
            }
            
            embedded_form = f"""
        <div style="background: linear-gradient(45deg, #e8f5e8, #f0f8f0); padding: 25px; border-radius: 12px; margin: 25px 0; border: 2px solid #52c41a; text-align: center;">
            <h3 style="color: #155724; margin-bottom: 20px;">💳 SECURE PAYMENT WITH CASHFREE</h3>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #ddd;">
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">Order ID:</span>
                    <span style="color: #666; font-family: monospace;">{order_id}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">Session ID:</span>
                    <span style="color: #666; font-family: monospace;">{payment_session_id}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">Amount:</span>
                    <span style="color: #666; font-family: monospace;">₹{amount}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">Environment:</span>
                    <span style="color: #666; font-family: monospace;">{"Sandbox" if is_sandbox else "Production"}</span>
                </div>
            </div>
            
            <form method="post" action="{checkout_url}" target="_blank">
                <input type="hidden" name="payment_session_id" value="{payment_session_id}">
                <input type="hidden" name="browser_meta" value='{json.dumps(browser_meta)}'>
                <button type="submit" style="display: inline-block; width: 80%; padding: 18px; background: linear-gradient(45deg, #52c41a, #73d13d) !important; color: white !important; border: none; border-radius: 10px; font-size: 18px; font-weight: 600; cursor: pointer; text-decoration: none !important;">
                    🔒 PAY ₹{amount} WITH CASHFREE
                </button>
            </form>
            
            <div style="background: #e6f7ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #1890ff;">
                <p style="font-size: 12px; margin: 10px 0; color: #666;">
                    ✅ Secure payment powered by Cashfree<br>
                    ✅ Session valid for 30 minutes<br>
                    ✅ All card details encrypted
                </p>
            </div>
        </div>
        """
            
            print(f"✅ Created embedded Cashfree form with session: {payment_session_id}")
            return embedded_form
            
        except Exception as e:
            print(f"❌ Error creating embedded form: {e}")
            return self.create_fallback_cashfree_form(amount, license_plate, violation_id, order_id)

    def create_fallback_cashfree_form(self, amount, license_plate, violation_id, order_id):
        try:
            fallback_form = f"""
        <div style="background: linear-gradient(45deg, #fff3cd, #ffeaa7); padding: 25px; border-radius: 12px; margin: 25px 0; border: 2px solid #ffc107; text-align: center;">
            <h3 style="color: #856404; margin-bottom: 20px;">💳 CASHFREE PAYMENT</h3>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #ddd;">
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">TOLL ID:</span>
                    <span style="color: #666; font-family: monospace;">{violation_id}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">License Plate:</span>
                    <span style="color: #666; font-family: monospace;">{license_plate}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px;">
                    <span style="font-weight: 600; color: #333;">Amount:</span>
                    <span style="color: #666; font-family: monospace;">₹{amount}</span>
                </div>
            </div>
            
            <a href="https://cashfree.com/payment-gateway" target="_blank" style="display: inline-block; width: 80%; padding: 18px; background: linear-gradient(45deg, #52c41a, #73d13d) !important; color: white !important; border: none; border-radius: 10px; font-size: 18px; font-weight: 600; cursor: pointer; text-decoration: none !important;">
                🔒 PAY ₹{amount} WITH CASHFREE
            </a>
            
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #dc3545;">
                <p style="font-size: 12px; margin: 10px 0; color: #721c24;">
                    ⚠️ Payment session creation failed<br>
                    ✅ Click button to pay with Cashfree<br>
                    ✅ Use Order ID: {order_id}
                </p>
            </div>
        </div>
        """
            
            print(f"✅ Created fallback Cashfree form for order: {order_id}")
            return fallback_form
            
        except Exception as e:
            print(f"❌ Error creating fallback form: {e}")
            return f'<a href="https://cashfree.com" target="_blank" style="background: #52c41a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">PAY ₹{amount} WITH CASHFREE</a>'
    
    def create_violation_template(self):
        template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }}
            .violation-id {{ background-color: #ff5722; color: white; padding: 10px; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .amount {{ font-size: 24px; color: #d32f2f; font-weight: bold; text-align: center; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 TOLL CROSS NOTICE 🚨</h1>
                <p>Signal Line Crossing Detected</p>
            </div>
            
            <div class="violation-id">
                <strong>Toll ID: {violation_id}</strong>
            </div>
            
            <div class="details">
                <h3>📋 TOLL Details:</h3>
                <p><strong>License Plate:</strong> {license_plate}</p>
                <p><strong>Date & Time:</strong> {datetime}</p>
                <p><strong>Location:</strong> Traffic Signal Camera</p>
                <p><strong>TOLL Type:</strong> Car Rs. 1</p>
            </div>
            
            <div class="amount">
                <p>Fine Amount: ₹{amount}</p>
            </div>
            
            {payment_form}
            
            <div class="details">
                <h3>⚠️ Important Information:</h3>
                <ul>
                    <li>This toll was automatically detected by our smart camera system</li>
                    <li>Payment must be made within 15 days to avoid additional penalties</li>
                    <li>Late payment will result in doubling of the fine amount</li>
                    <li>For disputes, contact traffic police with toll ID</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>This is an automated message from Traffic Management System</p>
                <p>Smart Signal Toll Detection System</p>
                <p><strong>Toll ID: {violation_id}</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
        return template
    
    def log_violation_to_api(self, violation_id, license_plate, amount, image_path, cashfree_session_id=None):
        try:
            api_data = {
                'violation_id': violation_id,
                'license_plate': license_plate,
                'amount': amount,
                'status': 'pending',
                'image_path': image_path,
                'cashfree_session_id': cashfree_session_id,
                'location': 'Traffic Signal Camera',
                'violation_type': 'Crossing Stop Line During Red Signal',
                'camera_id': 'CAMERA_01'
            }
            
            print(f"🌐 Logging toll to LIVE API: {violation_id}")
            
            try:
                response = requests.post(
                    f"{self.api_base_url}/create",
                    json=api_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"✅ Toll logged to API successfully via JSON POST!")
                        return True
                    else:
                        print(f"❌ API returned error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"⚠️ JSON POST failed with status: {response.status_code}, trying GET method...")
            except Exception as e:
                print(f"⚠️ JSON POST failed: {e}, trying GET method...")
            
            try:
                params = {
                    'violation_id': violation_id,
                    'license_plate': license_plate,
                    'amount': amount,
                    'status': 'pending',
                    'image_path': image_path,
                    'cashfree_session_id': cashfree_session_id,
                    'location': 'Traffic Signal Camera',
                    'violation_type': 'Crossing Stop Line During Red Signal',
                    'camera_id': 'CAMERA_01'
                }
                
                params = {k: v for k, v in params.items() if v is not None}
                
                response = requests.get(
                    self.api_base_url,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"✅ Toll logged to API successfully via GET!")
                        return True
                    else:
                        print(f"❌ API returned error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ GET request failed with status: {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"❌ GET request failed: {e}")
                
        except Exception as e:
            print(f"❌ Error logging violation to API: {e}")
        
        return False
    
    def create_simple_cashfree_link(self, amount, license_plate, violation_id):
        """Create a simple Cashfree payment link instead of massive embedded form"""
        try:
            # Generate unique order ID
            order_id = f"order_{int(time.time())}"
            
            # Try to create Cashfree session (but if it fails, use fallback)
            url = "https://api.cashfree.com/pg/orders"
            headers = {
                'x-client-id': self.cashfree_app_id,
                'x-client-secret': self.cashfree_secret,
                'x-api-version': '2023-08-01',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "order_id": order_id,
                "order_amount": float(amount),
                "order_currency": "INR",
                "customer_details": {
                    "customer_id": f"cust_{int(time.time())}",
                    "customer_name": f"Vehicle Owner {license_plate}",
                    "customer_email": self.demo_email,
                    "customer_phone": "9999999999"
                },
                "order_meta": {
                    "return_url": f"https://thegroup11.com/payment_success.php?order_id={order_id}&violation_id={violation_id}"
                }
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "payment_session_id" in data:
                        # Return simple button instead of massive form
                        return f'''<div style="text-align: center; margin: 20px; padding: 20px; background: #f0f8f0; border-radius: 10px;">
                        <h3 style="color: #155724;">💳 PAY YOUR FINE</h3>
                        <p>Amount: ₹{amount}</p>
                        <a href="https://api.cashfree.com/pg/view/sessions/checkout?payment_session_id={data["payment_session_id"]}" 
                           target="_blank" style="background: #52c41a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                           🔒 PAY ₹{amount} WITH CASHFREE
                        </a>
                        <p style="font-size: 12px; margin-top: 15px;">Secure payment powered by Cashfree</p>
                        </div>'''
            except:
                pass
            
            # Simple fallback
            return f'''<div style="text-align: center; margin: 20px; padding: 20px; background: #fff3cd; border-radius: 10px;">
            <h3 style="color: #856404;">💳 PAY YOUR FINE</h3>
            <p>Amount: ₹{amount}</p>
            <a href="https://cashfree.com/payment-gateway" target="_blank" 
               style="background: #52c41a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
               🔒 PAY ₹{amount} WITH CASHFREE
            </a>
            <p style="font-size: 12px; margin-top: 15px;">Order ID: {order_id}</p>
            </div>'''
            
        except Exception as e:
            # Ultra simple fallback
            return f'<p style="text-align: center;"><a href="https://cashfree.com" target="_blank" style="background: #52c41a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">PAY ₹{amount}</a></p>'

    def create_simple_violation_template(self):
        """Create a MUCH simpler email template to avoid 414 error"""
        template = """<!DOCTYPE html>
<html>
<head><style>
body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f4f4; }}
.container {{ max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
.header {{ background: #d32f2f; color: white; padding: 15px; text-align: center; border-radius: 5px; }}
.details {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; }}
</style></head>
<body>
<div class="container">
<div class="header">
<h2>🚨 TOLL DETAILS</h2>
</div>
<div class="details">
<p><strong>License Plate:</strong> {license_plate}</p>
<p><strong>Date:</strong> {datetime}</p>
<p><strong>Fine Amount:</strong> ₹{amount}</p>
<p><strong>Toll ID:</strong> {violation_id}</p>
</div>
{payment_form}
<p style="font-size: 12px; color: #666; text-align: center;">
This toll was automatically detected. Pay within 15 days to avoid penalties.
</p>
</div>
</body>
</html>"""
        return template

    def send_violation_email(self, license_plate, img_path, amount=1):
        violation_id = str(uuid.uuid4())[:8].upper()
        
        payment_form = self.create_cashfree_payment_link(amount, license_plate, violation_id)
        
        template = self.create_violation_template()
        
        html_content = template.format(
            violation_id=violation_id,
            license_plate=license_plate,
            datetime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            amount=amount,
            payment_form=payment_form
        )
        
        self.log_violation_to_api(violation_id, license_plate, amount, img_path)
        
        subject = f"🚨 TOLL CROSSED - {license_plate} - Pay ₹{amount} - ID: {violation_id}"
        
        print(f"\n🔥 TOLL EMAIL CREATED! 🔥")
        print(f"🆔 TOLL ID: {violation_id}")
        print(f"💳 Embedded Cashfree form included in email!")
        print(f"🌐 Logged to API system!")
        
        try:
            encoded_html = quote_plus(html_content)
            encoded_subject = quote_plus(subject)
            
            url = f"{self.mail_api}?api_key={self.api_key}&to={self.demo_email}&subject={encoded_subject}&message={encoded_html}&html=1"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ TOLL email sent successfully for plate: {license_plate}")
                print(f"📬 Check your email: {self.demo_email}")
                print(f"💳 Email contains working Cashfree payment form!")
                return violation_id
            else:
                print(f"❌ Failed to send email: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"📧 Email error: {e}")
        
        return violation_id
