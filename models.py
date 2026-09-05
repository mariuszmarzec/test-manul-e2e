class Item:
    def __init__(self, id, name, description='', price=0.0):
        self.id = id
        self.name = name
        self.description = description
        self.price = price

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data['name'],
            description=data.get('description', ''),
            price=data.get('price', 0.0)
        )
