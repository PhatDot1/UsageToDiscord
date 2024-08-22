import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PhantomBuster API credentials
phantombuster_api_key = os.getenv('PHANTOMBUSTER_API_KEY')

# Make (Integromat) API credentials
make_api_key = os.getenv('MAKE_API_KEY')
organization_id = os.getenv('MAKE_ORG_ID')

# Discord Webhook URL
discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

# Function definitions (same as before)...

def main():
    # Fetch PhantomBuster usage
    phantombuster_usage = get_phantombuster_usage(phantombuster_api_key)
    
    # Prepare the message content
    discord_message = ""

    # Calculate PhantomBuster usage percentages
    if isinstance(phantombuster_usage, dict):
        daily_exec_time_pct = calculate_percentage(phantombuster_usage['dailyExecutionTime'], phantombuster_usage['plan']['dailyExecutionTime'])
        monthly_exec_time_pct = calculate_percentage(phantombuster_usage['monthlyExecutionTime'], phantombuster_usage['plan']['monthlyExecutionTime'])
        daily_reset_pct = calculate_time_percentage(phantombuster_usage['dailyResourceNextResetAt'] - 24*3600*1000, phantombuster_usage['dailyResourceNextResetAt'])
        monthly_reset_pct = calculate_time_percentage(phantombuster_usage['monthlyResourceNextResetAt'] - 30*24*3600*1000, phantombuster_usage['monthlyResourceNextResetAt'])

        discord_message += "# === PhantomBuster Usage Information ===\n"
        discord_message += f"Daily Execution Time Used: {visualize_loading_bar(daily_exec_time_pct)} {get_usage_indicator(daily_exec_time_pct, daily_reset_pct)}\n"
        discord_message += f"Percent Through Daily Period: {visualize_loading_bar(daily_reset_pct)}\n\n"
        discord_message += f"Monthly Execution Time Used: {visualize_loading_bar(monthly_exec_time_pct)} {get_usage_indicator(monthly_exec_time_pct, monthly_reset_pct)}\n"
        discord_message += f"Percent Through Monthly Period: {visualize_loading_bar(monthly_reset_pct)}\n"
    else:
        discord_message += str(phantombuster_usage)

    # Fetch Make usage
    make_usage = get_make_usage(make_api_key, organization_id)
    
    # Calculate Make usage percentages
    if isinstance(make_usage, dict):
        make_org = make_usage['organization']
        operations_used_pct = calculate_percentage(int(make_org['operations']), make_org['license']['operations'])
        transfer_used_pct = calculate_percentage(int(make_org['transfer']), make_org['license']['transfer'])
        
        last_reset = datetime.strptime(make_org['lastReset'], '%Y-%m-%dT%H:%M:%S.%fZ')
        next_reset = datetime.strptime(make_org['nextReset'], '%Y-%m-%dT%H:%M:%S.%fZ')
        period_pct = calculate_percentage((datetime.utcnow() - last_reset).total_seconds(), (next_reset - last_reset).total_seconds())

        discord_message += "\n# === Make (Formerly Integromat) Usage Information ===\n"
        discord_message += f"Operations Used: {visualize_loading_bar(operations_used_pct)} {get_usage_indicator(operations_used_pct, period_pct)}\n"
        discord_message += f"Transfer Used: {visualize_loading_bar(transfer_used_pct)} {get_usage_indicator(transfer_used_pct, period_pct)}\n\n"
        discord_message += f"Percent Through Current Usage Period: {visualize_loading_bar(period_pct)}\n"
    else:
        discord_message += str(make_usage)

    # Send the message to Discord
    send_discord_message(discord_message)

if __name__ == "__main__":
    main()
