class BaseRepository:
    model = None

    def __init__(self, session):
        self.session = session

    def get(self, entity_id):
        return self.session.get(self.model, entity_id)

    def add(self, entity):
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity):
        self.session.delete(entity)
        self.session.flush()
