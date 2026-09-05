from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage
items = {}


@app.route('/')
def index():
    return jsonify({
        'name': 'Flask Items API',
        'version': '1.0.0',
        'description': 'A simple Flask web application for managing items'
    })


@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify(list(items.values()))


@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    item_id = len(items) + 1
    item = {
        'id': item_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'price': data.get('price', 0.0)
    }
    items[item_id] = item
    return jsonify(item), 201


@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = items.get(item_id)
    if item is None:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify(item)


@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = items.get(item_id)
    if item is None:
        return jsonify({'error': 'Item not found'}), 404
    data = request.get_json()
    if 'name' in data:
        item['name'] = data['name']
    if 'description' in data:
        item['description'] = data['description']
    if 'price' in data:
        item['price'] = data['price']
    return jsonify(item)


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = items.get(item_id)
    if item is None:
        return jsonify({'error': 'Item not found'}), 404
    del items[item_id]
    return jsonify({'message': 'Item deleted'})


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True)
