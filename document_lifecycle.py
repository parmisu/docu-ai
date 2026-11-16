class DocumentLifecycle:
    def __init__(self):
        self._stores = {}
        self._active_key = None

    @property
    def active_key(self):
        return self._active_key

    def register(self, document_key, vector_store):
        self._stores[document_key] = vector_store
        self._active_key = document_key

    def replace(self, document_key, vector_store):
        self.register(
            document_key,
            vector_store,
        )

    def delete_active(self):
        self._active_key = None

    def get_active_store(self):
        if self._active_key is None:
            return None

        return self._stores.get(
            self._active_key
        )

    def search_active(self, query, k=1):
        store = self.get_active_store()

        if store is None:
            return []

        return store.similarity_search(
            query,
            k=k,
        )