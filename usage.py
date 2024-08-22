import requests
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Import Keys here
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os


# Load environment variables from .env file
load_dotenv()

# PhantomBuster API credentials
phantombuster_api_key = os.getenv('PHANTOMBUSTER_API_KEY')

# Make (Integromat) API credentials
make_api_key = os.getenv('MAKE_API_KEY')
organization_id = os.getenv('MAKE_ORG_ID')

# Discord Webhook URL
discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

# Zapier credentials
zapier_email = os.getenv('ZAPIER_EMAIL')
zapier_password = os.getenv('ZAPIER_PASSWORD')

def get_phantombuster_usage(api_key):
    url = "https://api.phantombuster.com/api/v2/orgs/fetch-resources"
    headers = {
        "accept": "application/json",
        "X-Phantombuster-Key": api_key
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to retrieve PhantomBuster data. Status code: {response.status_code}, Response: {response.text}"

def get_make_usage(api_key, organization_id):
    url = f"https://eu2.make.com/api/v2/organizations/{organization_id}?wait=true"
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to retrieve Make data. Status code: {response.status_code}, Response: {response.text}"

def calculate_percentage(part, total):
    return (part / total) * 100 if total > 0 else 0

def visualize_loading_bar(percentage):
    bar_length = 20
    filled_length = int(round(bar_length * percentage / 100))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"|{bar}| {percentage:.2f}%"

def get_usage_indicator(usage_pct, period_pct):
    if usage_pct <= period_pct - 10:
        return '🟢'
    elif abs(usage_pct - period_pct) <= 10:
        return '🟠'
    else:
        return '🔴'

def calculate_monthly_period_percentage():
    now = datetime.now(timezone.utc)
    reset_day = 20
    reset_hour = 16  # 4:30 PM BST

    current_month = now.month
    current_year = now.year
    reset_time = datetime(current_year, current_month, reset_day, reset_hour, 30, tzinfo=timezone.utc)

    if now < reset_time:
        last_reset_time = reset_time.replace(month=current_month - 1 if current_month > 1 else 12, year=current_year if current_month > 1 else current_year - 1)
    else:
        last_reset_time = reset_time
        reset_time = reset_time.replace(month=current_month + 1 if current_month < 12 else 1, year=current_year if current_month < 12 else current_year + 1)

    period_pct = (now - last_reset_time).total_seconds() / (reset_time - last_reset_time).total_seconds() * 100
    return period_pct

def get_zapier_usage():
    # Use webdriver-manager to automatically manage ChromeDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")

    # Initialize Chrome WebDriver with the correct executable path and options
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)

    try:
        driver.get("https://zapier.com/app/login")

        google_signin_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue with Google')]"))
        )
        google_signin_button.click()

        time.sleep(10)

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.send_keys(os.getenv('ZAPIER_EMAIL'))
        email_input.send_keys(Keys.RETURN)

        time.sleep(5)
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        password_input.send_keys(os.getenv('ZAPIER_PASSWORD'))
        password_input.send_keys(Keys.RETURN)

        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Continue']]"))
        )
        continue_button.click()

        time.sleep(10)

        driver.get("https://zapier.com/app/home")
        time.sleep(5)

        expand_sidebar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-1xymhdn-MenuCollapseButton"))
        )
        expand_sidebar_button.click()

        time.sleep(5)

        footer_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-1fmjwmw-InAppSidebarFooter__footerWrapper"))
        ).text

        return footer_content
    finally:
        driver.quit()



def send_discord_message(content):
    data = {
        "content": content
    }
    response = requests.post(discord_webhook_url, json=data)
    if response.status_code == 204:
        print("Message sent successfully to Discord.")
    else:
        print(f"Failed to send message to Discord. Status code: {response.status_code}, Response: {response.text}")

def main():
    discord_message = ""

    # Calculate the period percentage for monthly reset
    period_pct = calculate_monthly_period_percentage()

    # Fetch PhantomBuster usage
    phantombuster_usage = get_phantombuster_usage(phantombuster_api_key)

    # Calculate PhantomBuster usage percentages
    if isinstance(phantombuster_usage, dict):
        monthly_exec_time_pct = calculate_percentage(phantombuster_usage['monthlyExecutionTime'], phantombuster_usage['plan']['monthlyExecutionTime'])

        discord_message += "# === PhantomBuster Usage Information ===\n"
        discord_message += f"**Monthly Execution Time Used:** {visualize_loading_bar(monthly_exec_time_pct)} {get_usage_indicator(monthly_exec_time_pct, period_pct)}\n"
        discord_message += f"**Percent Through Monthly Period:** {visualize_loading_bar(period_pct)}\n\n"
    else:
        discord_message += str(phantombuster_usage)

    # Fetch Make usage
    make_usage = get_make_usage(make_api_key, organization_id)

    # Calculate Make usage percentages
    if isinstance(make_usage, dict):
        make_org = make_usage['organization']
        operations_used_pct = calculate_percentage(int(make_org['operations']), make_org['license']['operations'])
        transfer_used_pct = calculate_percentage(int(make_org['transfer']), make_org['license']['transfer'])

        discord_message += "\n# === Make (Formerly Integromat) Usage Information ===\n"
        discord_message += f"**Operations Used:** {visualize_loading_bar(operations_used_pct)} {get_usage_indicator(operations_used_pct, period_pct)}\n"
        discord_message += f"**Transfer Used:** {visualize_loading_bar(transfer_used_pct)} {get_usage_indicator(transfer_used_pct, period_pct)}\n\n"
        discord_message += f"**Percent Through Current Usage Period:** {visualize_loading_bar(period_pct)}\n"
    else:
        discord_message += str(make_usage)

    # Fetch Zapier usage
    zapier_usage = get_zapier_usage()

    # Parse and calculate Zapier usage
    if zapier_usage:
        tasks_used_line = [line for line in zapier_usage.splitlines() if "Included Tasks" in line][0]
        tasks_used, task_limit = map(int, tasks_used_line.split()[1].split('/'))
        zapier_usage_pct = calculate_percentage(tasks_used, task_limit)

        discord_message += "\n# === Zapier Usage Information ===\n"
        discord_message += f"**Included Tasks Used:** {visualize_loading_bar(zapier_usage_pct)} {get_usage_indicator(zapier_usage_pct, period_pct)}\n"
        discord_message += f"**Percent Through Monthly Period:** {visualize_loading_bar(period_pct)}\n"
    else:
        discord_message += "Failed to retrieve Zapier usage."

    # Send the message to Discord
    send_discord_message(discord_message)

if __name__ == "__main__":
    main()
