import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_item():
    return {
        'name': 'Test Item',
        'description': 'A test item',
        'price': 9.99
    }


class TestIndexRoute:
    def test_index_returns_json(self, client):
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'name' in data
        assert 'version' in data
        assert 'description' in data


class TestGetItems:
    def test_get_items_empty(self, client):
        response = client.get('/api/items')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_get_items_with_data(self, client, sample_item):
        client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        response = client.get('/api/items')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['name'] == sample_item['name']


class TestCreateItem:
    def test_create_item(self, client, sample_item):
        response = client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == sample_item['name']
        assert data['description'] == sample_item['description']
        assert data['price'] == sample_item['price']
        assert 'id' in data

    def test_create_item_missing_name(self, client):
        response = client.post('/api/items', data=json.dumps({'description': 'No name'}), content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_item_minimal(self, client):
        response = client.post('/api/items', data=json.dumps({'name': 'Minimal'}), content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Minimal'
        assert data['description'] == ''
        assert data['price'] == 0.0


class TestGetItem:
    def test_get_existing_item(self, client, sample_item):
        response = client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        item_id = json.loads(response.data)['id']
        response = client.get(f'/api/items/{item_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == item_id

    def test_get_nonexistent_item(self, client):
        response = client.get('/api/items/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestUpdateItem:
    def test_update_existing_item(self, client, sample_item):
        response = client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        item_id = json.loads(response.data)['id']
        updates = {'name': 'Updated Name', 'price': 19.99}
        response = client.put(f'/api/items/{item_id}', data=json.dumps(updates), content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Name'
        assert data['price'] == 19.99

    def test_update_nonexistent_item(self, client):
        response = client.put('/api/items/999', data=json.dumps({'name': 'X'}), content_type='application/json')
        assert response.status_code == 404

    def test_partial_update(self, client, sample_item):
        response = client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        item_id = json.loads(response.data)['id']
        response = client.put(f'/api/items/{item_id}', data=json.dumps({'price': 5.0}), content_type='application/json')
        data = json.loads(response.data)
        assert data['price'] == 5.0
        assert data['name'] == sample_item['name']


class TestDeleteItem:
    def test_delete_existing_item(self, client, sample_item):
        response = client.post('/api/items', data=json.dumps(sample_item), content_type='application/json')
        item_id = json.loads(response.data)['id']
        response = client.delete(f'/api/items/{item_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data

        # Verify deletion
        response = client.get(f'/api/items/{item_id}')
        assert response.status_code == 404

    def test_delete_nonexistent_item(self, client):
        response = client.delete('/api/items/999')
        assert response.status_code == 404


class TestErrorHandlers:
    def test_404_handler(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
