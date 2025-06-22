def format_data(data):
    # Function to format the data retrieved from the Yahoo Finance API
    formatted_data = {
        'symbol': data.get('symbol'),
        'price': data.get('price'),
        'volume': data.get('volume'),
        'marketCap': data.get('marketCap'),
        'timestamp': data.get('timestamp')
    }
    return formatted_data

def log_error(error):
    # Function to log errors encountered during API calls
    with open('error_log.txt', 'a') as log_file:
        log_file.write(f"{error}\n")