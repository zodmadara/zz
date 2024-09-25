import requests
import telebot
import time
import random
from datetime import datetime, timedelta

# Initialize bot with token
token = input(': ')
bot = telebot.TeleBot(token)

# Dictionary to track last request time for each user
user_last_request = {}
request_limit_time = 5  # time limit in seconds for requests

# Helper function to safely make a request
def safe_request(url):
    try:
        return requests.get(url)
    except requests.exceptions.RequestException:
        return None

# Rate limiting check
def is_request_allowed(user_id):
    now = datetime.now()
    last_request_time = user_last_request.get(user_id)

    if last_request_time is None or (now - last_request_time) > timedelta(seconds=request_limit_time):
        user_last_request[user_id] = now
        return True
    return False

# Check if website has captcha
def check_captcha(url):
    response = safe_request(url)
    if response is None:
        return False
    if ('https://www.google.com/recaptcha/api' in response.text or
        'captcha' in response.text or
        'verifyRecaptchaToken' in response.text or
        'grecaptcha' in response.text or
        'www.google.com/recaptcha' in response.text):
        return True
    return False

# Check for multiple payment systems in the website
def check_credit_card_payment(url):
    response = safe_request(url)
    if response is None:
        return 'Error accessing the website'
    
    gateways = []
    if 'stripe' in response.text:
        gateways.append('Stripe')
    if 'Cybersource' in response.text:
        gateways.append('Cybersource')
    if 'paypal' in response.text:
        gateways.append('Paypal')
    if 'authorize.net' in response.text:
        gateways.append('Authorize.net')
    if 'Bluepay' in response.text:
        gateways.append('Bluepay')
    if 'Magento' in response.text:
        gateways.append('Magento')
    if 'woo' in response.text:
        gateways.append('WooCommerce')
    if 'Shopify' in response.text:
        gateways.append('Shopify')
    if 'adyen' in response.text or 'Adyen' in response.text:
        gateways.append('Adyen')
    if 'braintree' in response.text:
        gateways.append('Braintree')
    if 'square' in response.text:
        gateways.append('Square')
    if 'payflow' in response.text:
        gateways.append('Payflow')
    
    return ', '.join(gateways) if gateways else 'No recognized payment gateway found'

# Check for cloud services in the website
def check_cloud_in_website(url):
    response = safe_request(url)
    if response is None:
        return False
    if 'cloudflare' in response.text.lower():
        return True
    return False

# Check for GraphQL
def check_graphql(url):
    response = safe_request(url)
    if response is None:
        return False
    if 'graphql' in response.text.lower() or 'query {' in response.text or 'mutation {' in response.text:
        return True
    
    # Optionally, try querying the /graphql endpoint directly
    graphql_url = url.rstrip('/') + '/graphql'
    graphql_response = safe_request(graphql_url)
    if graphql_response and graphql_response.status_code == 200:
        return True
    
    return False

# Check if the path /my-account/add-payment-method/ exists
def check_auth_path(url):
    auth_path = url.rstrip('/') + '/my-account/add-payment-method/'
    response = safe_request(auth_path)
    if response is not None and response.status_code == 200:
        return 'Auth'
    return 'None'

# Get the status code
def get_status_code(url):
    response = safe_request(url)
    if response is not None:
        return response.status_code
    return 'Error'

# Check for platform (simplified)
def check_platform(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'wordpress' in response.text.lower():
        return 'WordPress'
    if 'shopify' in response.text.lower():
        return 'Shopify'
    return 'None'

# Check for error logs (simplified)
def check_error_logs(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'error' in response.text.lower() or 'exception' in response.text.lower():
        return 'Error logs found'
    return 'None'

# Generate credit card numbers based on a BIN
def generate_credit_card_numbers(bin_number, amount):
    card_numbers = []
    for _ in range(amount):  # Generate 'amount' card numbers
        # Create a 16-digit card number using the BIN
        card_number = bin_number + ''.join([str(random.randint(0, 9)) for _ in range(10)])  
        expiration_date = f"{random.randint(1, 12):02}|{random.randint(2024, 2030)}"  # MM|YYYY
        cvv = f"{random.randint(100, 999)}"  # CVV
        card_numbers.append(f"{card_number}|{expiration_date}|{cvv}")
    return card_numbers

# Check single URL with /check command
@bot.message_handler(commands=['check'])
def check_url(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Please provide a valid URL after the /check command.')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request.')
        return

    url = message.text.split()[1]

    try:
        captcha = check_captcha(url)
    except:
        captcha = 'Error checking captcha'

    cloud = check_cloud_in_website(url)
    payment = check_credit_card_payment(url)
    graphql = check_graphql(url)
    auth_path = check_auth_path(url)
    platform = check_platform(url)
    error_logs = check_error_logs(url)
    status_code = get_status_code(url)

    loading_message = bot.reply_to(message, '<strong>[~]-Loading... 🥸</strong>', parse_mode="HTML")
    time.sleep(1)

    # Conditionally add the 😞 emoji based on Captcha and Cloudflare detection
    captcha_emoji = "😞" if captcha else "🔥"
    cloud_emoji = "😞" if cloud else "🔥"

    # Create formatted message
    response_message = (
        "🔍 Gateways Fetched Successfully ✅\n"
        "━━━━━━━━━━━━━━\n"
        f"🔹 URL: {url}\n"
        f"🔹 Payment Gateways: {payment}\n"
        f"🔹 Captcha: {captcha} {captcha_emoji}\n"
        f"🔹 Cloudflare: {cloud} {cloud_emoji}\n"
        f"🔹 GraphQL: {graphql}\n"
        f"🔹 Auth Path: {auth_path}\n"
        f"🔹 Platform: {platform}\n"
        f"🔹 Error Logs: {error_logs}\n"
        f"🔹 Status: {status_code}\n"
        "\nBot by: @ZodMadara"
    )

    # Send the final formatted message
    bot.edit_message_text(response_message, message.chat.id, loading_message.message_id, parse_mode='html')

# Handle .txt file upload with a list of URLs
@bot.message_handler(content_types=['document'])
def handle_txt_file(message):
    file_info = bot.get_file(message.document.file_id)
    file_extension = file_info.file_path.split('.')[-1]

    if file_extension != 'txt':
        bot.reply_to(message, 'Please upload a .txt file containing URLs.')
        return

    file = bot.download_file(file_info.file_path)
    urls = file.decode('utf-8').splitlines()

    # Validate URL count (should be between 50 and 100)
    if len(urls) < 50 or len(urls) > 100:
        bot.reply_to(message, 'Please provide a .txt file with between 50 and 100 URLs.')
        return

    bot.reply_to(message, 'Processing your URLs... This may take some time.')

    # Process each URL and collect results
    results = []
    for url in urls:
        try:
            captcha = check_captcha(url)
        except:
            captcha = 'Error checking captcha'

        cloud = check_cloud_in_website(url)
        payment = check_credit_card_payment(url)
        graphql = check_graphql(url)
        auth_path = check_auth_path(url)
        platform = check_platform(url)
        error_logs = check_error_logs(url)
        status_code = get_status_code(url)

        captcha_emoji = "😞" if captcha else "🔥"
        cloud_emoji = "😞" if cloud else "🔥"

        result_message = (
            "━━━━━━━━━━━━━━\n"
            f"🔹 URL: {url}\n"
            f"🔹 Payment Gateways: {payment}\n"
            f"🔹 Captcha: {captcha} {captcha_emoji}\n"
            f"🔹 Cloudflare: {cloud} {cloud_emoji}\n"
            f"🔹 GraphQL: {graphql}\n"
            f"🔹 Auth Path: {auth_path}\n"
            f"🔹 Platform: {platform}\n"
            f"🔹 Error Logs: {error_logs}\n"
            f"🔹 Status: {status_code}\n"
        )
        results.append(result_message)

    # Send all results back to the user
    final_response = "\n".join(results)
    bot.reply_to(message, final_response)

# Generate credit card numbers with /gen command
@bot.message_handler(commands=['gen'])
def gen_credit_card(message):
    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Please provide a BIN and the amount of cards to generate after the /gen command.')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request.')
        return

    bin_number = message.text.split()[1]
    try:
        amount = int(message.text.split()[2])
        if amount < 1 or amount > 10:  # Limit the number of generated cards to a reasonable amount
            raise ValueError("Amount must be between 1 and 10.")
    except ValueError:
        bot.reply_to(message, 'Please provide a valid number for the amount (1-10).')
        return

    # Generate credit card numbers
    card_numbers = generate_credit_card_numbers(bin_number, amount)

    # Format the response
    cc_info = f"𝗕𝗜𝗡 ⇾ {bin_number}\n𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {amount}\n\n"
    cc_info += "\n".join(card_numbers) + "\n\n"
    cc_info += "𝗜𝗻𝗳𝗼: MASTERCARD - DEBIT - DEBIT UNEMBOSSED MASTERCARD® CARD\n"
    cc_info += "𝐈𝐬𝐬𝐮𝐞𝐫: CIMB BANK BERHAD\n"
    cc_info += "𝗖𝗼𝘂𝗻𝘁𝗿𝘆: MALAYSIA 🇲🇾"

    bot.reply_to(message, cc_info)

# Start the bot
bot.polling(none_stop=True)