from flask import Flask, request, render_template, redirect, url_for, session,jsonify
import json
from functools import wraps
from datetime import datetime
import uuid
import os
import time
from datetime import datetime
import json
from typing import Dict
from modules.send_signup_email import send_sign_up_email, generate_otp
from modules.signupEmailBody import Sign_up_email_body_template
app = Flask(__name__)
app.secret_key = '1729'
from flask import Flask, render_template, request, jsonify
from web3 import Web3
import json
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
UPLOAD_FOLDER = os.path.join('database', 'uploads')
# Load contract ABI and address
with open('database/contract_abi.json', 'r') as f:
    contract_abi = json.load(f)
contract_address = "0xE10C431b9619a4E6D3b14a4CbD2e626b1c438229"
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

from werkzeug.utils import secure_filename
DATABASE_DIR = 'database'
POOLS_FILE = os.path.join(DATABASE_DIR, 'pools.json')
USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')

def load_pools():
        if os.path.exists(POOLS_FILE) and os.path.getsize(POOLS_FILE) > 0:
            with open(POOLS_FILE, 'r') as f:
                return json.load(f)
        return []

def load_users():
        if os.path.exists(USERS_FILE) and os.path.getsize(USERS_FILE) > 0:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return {}

def save_pools(pools_data):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        with open(POOLS_FILE, 'w') as f:
            json.dump(pools_data, f, indent=4)
UPLOAD_FOLDER = 'static/pool_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/pools', methods=['GET', 'POST'])
def manage_pools():
    if request.method == 'GET':
        pools_data = load_pools()
        return jsonify({'pools': pools_data})
    
    elif request.method == 'POST':
        # Handle image upload
        if 'image' not in request.files:
            return jsonify({'error': 'No image file'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Create unique filename using timestamp
            unique_filename = f"{int(time.time())}_{filename}"
            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Get other form data
            data = request.form
            pools_data = load_pools()
            users = load_users()
            
            creator_username = session.get('username')
            creator_details = users.get(creator_username, {})
            
            new_pool = {
                'id': str(uuid.uuid4()),
                'name': data['name'],
                'category': data['category'],
                'location': data['location'],
                'description': data['description'],
                'coordinates': json.loads(data['coordinates']),
                'targetAmount': float(data.get('targetAmount', 0)),
                'currentAmount': 0,
                'imageUrl': f"/static/pool_images/{unique_filename}",  # Store the image path
                'creator': {
                    'username': creator_username,
                    'wallet_address': creator_details.get('wallet_address'),
                    'email': creator_details.get('email')
                },
                'createdAt': datetime.now().isoformat(),
                'status': 'active',
                'transactions': []
            }
            
            pools_data.append(new_pool)
            save_pools(pools_data)
            
            return jsonify({'success': True, 'pool': new_pool})




@app.route('/donate', methods=['POST'])
def donate():
    data = request.json
    donor_address = data['donor_address']
    amount = data['amount']
    
    try:
        tx_hash = contract.functions.donate().transact({
            'from': donor_address,
            'value': amount
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({'success': True, 'transaction_hash': tx_hash.hex()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Constants
DATABASE_DIR = 'database'
USER_FILE = os.path.join(DATABASE_DIR, 'users.json')

def load_users() -> Dict:
    """
    Load users from JSON file with enhanced error handling
    Returns a dictionary of user data
    """
    # Ensure database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)
    
    try:
        # Check if file exists and is not empty
        if os.path.exists(USER_FILE) and os.path.getsize(USER_FILE) > 0:
            with open(USER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize with empty data if file doesn't exist
            save_users({})
            return {}
            
    except json.JSONDecodeError:
        # Handle corrupted JSON file
        backup_file = f"{USER_FILE}.backup"
        os.rename(USER_FILE, backup_file)
        return {}
    
    except Exception as e:
        print(f"Error loading users: {str(e)}")
        return {}

def save_users(users: Dict) -> bool:
    """
    Save users to JSON file with pretty formatting
    Returns True if successful, False otherwise
    """
    try:
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, sort_keys=True, ensure_ascii=False)
        return True
        
    except Exception as e:
        print(f"Error saving users: {str(e)}")
        return False

@app.route('/check_transaction/<tx_hash>', methods=['GET'])
def check_transaction(tx_hash):
    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        # Get transaction details
        tx_details = w3.eth.get_transaction(tx_hash)
        
        return jsonify({
            'status': 'confirmed' if receipt else 'pending',
            'block_number': receipt.blockNumber if receipt else None,
            'gas_used': receipt.gasUsed if receipt else None,
            'from': tx_details['from'],
            'to': tx_details['to']
        })
    except Exception as e:
        return jsonify({'error': str(e)})
# Example usage:
def get_user(username: str) -> Dict:
    """
    Get a specific user's data
    """
    users = load_users()
    return users.get(username, {})

def update_user(username: str, data: Dict) -> bool:
    """
    Update a specific user's data
    """
    users = load_users()
    users[username] = data
    return save_users(users)
@app.route('/get_contract_config')
def get_contract_config():
    with open('contracts/contract_config.json', 'r') as f:
        config = json.load(f)
    return jsonify(config)
@app.route('/fund-management')
def fund_management():
    return render_template('fundManagement.html')
@app.route('/')
@login_required
def home():
    return render_template('dashboard.html', username=session['username'])
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users = load_users()
    user_data = users[session['username']]
    wallet_address = user_data.get('wallet_address')
    
    return render_template('dashboard.html', 
                         wallet_address=wallet_address,
                         user_data=user_data)

@app.route('/register_beneficiary', methods=['POST'])
def register_beneficiary():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    users = load_users()
    user_data = users[session['username']]
    wallet_address = user_data.get('wallet_address')
    
    data = request.json
    location = data['location']
    
    # Update user role in database
    user_data['role'] = 'beneficiary'
    user_data['location'] = location
    users[session['username']] = user_data
    save_users(users)
    
    # Register on blockchain
    try:
        tx_hash = contract.functions.registerBeneficiary(location).transact({
            'from': wallet_address
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({'success': True, 'transaction_hash': tx_hash.hex()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']  # Can be username, email, or wallet address
        password = request.form['password']
        users = load_users()
        
        # Find user by any identifier
        user_found = None
        for username, user_data in users.items():
            if (username == identifier or 
                user_data.get('email') == identifier or 
                user_data.get('wallet_address') == identifier):
                user_found = user_data
                session_username = username
                break
        
        if user_found and user_found['password'] == password:
            session['username'] = session_username
            print(session)
            return redirect(url_for('view_pools_page'))
            
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        
        session['signup_data'] = {
            'username': username,
            'email': email
        }
        
        otp = generate_otp()
        body = Sign_up_email_body_template(username, otp)
        session['signup_otp'] = otp
        
        send_sign_up_email(email, username, os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'), body)
        return redirect(url_for('verify_email'))
    
    return render_template('sign_up_step_1.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        if 'otp' in request.form:
            entered_otp = request.form['otp']
            stored_otp = session.get('signup_otp')
            
            if entered_otp == stored_otp:
                session['email_verified'] = True
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Invalid OTP'}), 400
        
        elif 'password' in request.form and session.get('email_verified'):
            user_data = session.get('signup_data', {})
            user_data['password'] = request.form['password']
            session['signup_data'] = user_data
            return redirect(url_for('signup_step3'))
    
    return render_template('verify_email.html')

from eth_account import Account
import secrets
import jwt
from web3 import Web3

def generate_new_did():
    # Generate a new private key
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    
    # Create DID from Ethereum address
    did = f"did:ethr:{account.address}"
    return {
        'did': did,
        'private_key': private_key,
        'address': account.address
    }
from eth_account import Account
import secrets
import jwt
from web3 import Web3

# Generate unique identifier and keys for users
def generate_user_identity():
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    return {
        'unique_id': f"user:{account.address}",
        'private_key': private_key,
        'address': account.address
    }

# Create verifiable credentials
def create_credential(user_data, issuer_key):
    return jwt.encode({
        'user_id': user_data['unique_id'],
        'claims': {
            'name': user_data.get('username'),
            'email': user_data.get('email'),
            'wallet': user_data.get('wallet_address')
        }
    }, issuer_key, algorithm='HS256')

# Verify credentials
def verify_credential(token, issuer_key):
    return jwt.decode(token, issuer_key, algorithms=['HS256'])

# Your secret key for JWT
JWT_SECRET = secrets.token_urlsafe(32)

@app.route('/signup/personal-data', methods=['GET', 'POST'])
def signup_step3():
    if request.method == 'POST':
        user_data = session.get('signup_data', {})
        wallet_address = request.form['wallet_address']
        
        identity = generate_user_identity()
        credential = create_credential({
            'unique_id': identity['unique_id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'wallet_address': wallet_address
        }, JWT_SECRET)
        
        user_data.update({
            'wallet_address': wallet_address,
            'unique_id': identity['unique_id'],
            'credential': credential,
            'state': request.form['state'],
            'city': request.form['city'],
            'pincode': request.form['pincode']
        })
        
        users = load_users()
        users[user_data['username']] = {
            **user_data,
            'verified': True,
            'created_at': str(datetime.now())
        }
        save_users(users)
        
        session['credential'] = credential
        return redirect(url_for('login'))
    
    return render_template('signup_step_2.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/create-pool')
def create_pool_page():
    return render_template('create_pools.html')

@app.route('/view-pools')
def view_pools_page():
    return render_template('view_pools.html')


@app.route('/pools/<pool_id>')
def pool_details(pool_id):
    return render_template('pool_details.html')

from flask import Flask, jsonify
import json

def load_pools():
    with open('database/pools.json', 'r') as f:
        return json.load(f)

@app.route('/api/pools/<pool_id>', methods=['GET'])
def get_pool_details(pool_id):
    try:
        with open('database/pools.json', 'r') as f:
            pools = json.load(f)
            pool = next((p for p in pools if p['id'] == pool_id), None)
            if pool:
                return jsonify(pool)
            return jsonify({'error': 'Pool not found'}), 404
    except FileNotFoundError:
        return jsonify({'error': 'Database not found'}), 500

@app.route('/api/transactions/<pool_id>', methods=['GET'])
def get_pool_transactions(pool_id):
    try:
        with open('database/pools.json', 'r') as f:
            pools = json.load(f)
            pool = next((p for p in pools if p['id'] == pool_id), None)
            if pool:
                return jsonify(pool.get('transactions', []))
            return jsonify({'error': 'Pool not found'}), 404
    except FileNotFoundError:
        return jsonify({'error': 'Database not found'}), 500
@app.route('/api/transactions', methods=['POST'])
def record_transaction():
    data = request.json
    pool_id = data['poolId']
    
    # Load pools data
    with open('database/pools.json', 'r') as f:
        pools = json.load(f)
    
    # Find the specific pool
    pool = next((p for p in pools if p['id'] == pool_id), None)
    if not pool:
        return jsonify({'error': 'Pool not found'}), 404
    
    # Location validation
    current_location = data.get('location', {})
    if current_location:
        registered_lat = float(pool['coordinates']['lat'])
        registered_lng = float(pool['coordinates']['lng'])
        
        distance = calculate_distance(
            float(current_location['latitude']), 
            float(current_location['longitude']),
            registered_lat,
            registered_lng
        )
        
        MAX_DISTANCE = 5  # 5km radius
        if distance > MAX_DISTANCE:
            return jsonify({
                'success': False,
                'message': f'Location validation failed. Distance: {distance:.2f}km from registered location'
            }), 400
    
    # Create transaction record
    transaction = {
        'from': data['from'],
        'to': pool['creator']['wallet_address'],
        'amount': float(data['amount']),
        'transactionHash': data['transactionHash'],
        'timestamp': data['timestamp'],
        'location_verified': bool(current_location)
    }
    
    # Update pool data
    if 'transactions' not in pool:
        pool['transactions'] = []
    pool['transactions'].append(transaction)
    
    # Update current amount
    pool['currentAmount'] = float(pool['currentAmount']) + float(data['amount'])
    
    # Save updated data
    with open('database/pools.json', 'w') as f:
        json.dump(pools, f, indent=4)
    
    return jsonify({
        'success': True,
        'message': 'Transaction recorded successfully',
        'location_verified': bool(current_location)
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    from math import radians, sin, cos, sqrt, atan2
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

@app.route('/pool/<pool_id>')
def get_pool(pool_id):
    with open('database/pools.json', 'r') as f:
        pools = json.load(f)
        pool = next((p for p in pools if p['id'] == pool_id), None)
    return render_template('pool_details.html', pool=pool)


@app.route('/profile')
@login_required
def profile():
    users = load_users()
    user_data = users.get(session['username'], {})
    
    # Calculate account age
    created_at = datetime.strptime(user_data['created_at'], "%Y-%m-%d %H:%M:%S.%f")
    account_age = (datetime.now() - created_at).days
    
    return render_template('profile.html', user=user_data, account_age=account_age)


if __name__ == '__main__':
    app.run(debug=True)
