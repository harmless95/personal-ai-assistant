class DataLayerError(Exception):
    pass


class DuplicateEntryError(DataLayerError):
    def __init__(self, constraint: str | None = None):
        self.constraint = constraint
        super().__init__(f"Duplicate entry: {constraint}" if constraint else "Duplicate entry")


class ForeignKeyViolationError(DataLayerError):
    pass


class NotNullViolationError(DataLayerError):
    pass


class IntegrityViolationError(DataLayerError):
    pass


class DatabaseUnavailableError(DataLayerError):
    pass


class DatabaseError(DataLayerError):
    pass
