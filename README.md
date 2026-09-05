# Flask Items API

A comprehensive Flask web application for managing items with RESTful API endpoints.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mariuszmarcer/test-manul-e2e.git
cd test-manul-e2e
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install the package in development mode:
```bash
pip install -e .[test]
```

## Usage

Run the Flask application:
```bash
python app.py
```

The server will start on `http://127.0.0.1:5000/`

## API Endpoints

### Root
- `GET /` - Returns application info as JSON

### Items
- `GET /api/items` - Get all items
- `POST /api/items` - Create a new item
  - Body: `{"name": "Item Name", "description": "Description", "price": 9.99}`
- `GET /api/items/<id>` - Get a specific item
- `PUT /api/items/<id>` - Update an item
- `DELETE /api/items/<id>` - Delete an item

## Testing

Run the test suite:
```bash
pytest
```

Or with verbose output:
```bash
pytest -v
```

## Project Structure

```
.
├── app.py              # Flask application with routes and error handlers
├── models.py           # Item model class
├── tests/
│   └── test_app.py     # Test suite for all routes and operations
├── requirements.txt    # Python dependencies
├── setup.py            # Package setup configuration
└── README.md           # This file
```
