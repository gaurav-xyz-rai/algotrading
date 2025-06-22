# Yahoo Finance Integration

This project integrates with the Yahoo Finance API to fetch stock data and historical data for various financial symbols.

## Project Structure

```
yahoo-finance-integration
├── src
│   ├── main.py          # Entry point of the application
│   ├── yahoo_api.py     # Contains YahooFinanceAPI class for API interactions
│   └── utils.py         # Utility functions for data formatting and error logging
├── requirements.txt      # Lists project dependencies
├── README.md             # Project documentation
└── .gitignore            # Git ignore file
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/yahoo-finance-integration.git
   cd yahoo-finance-integration
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

## Yahoo Finance API Integration

This project utilizes the Yahoo Finance API to retrieve stock and historical data. The `YahooFinanceAPI` class in `yahoo_api.py` provides methods to interact with the API.

### Example

To fetch stock data for a specific symbol, you can use the following code snippet in `main.py`:

```python
from yahoo_api import YahooFinanceAPI

api = YahooFinanceAPI()
stock_data = api.get_stock_data('AAPL')
print(stock_data)
```

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.