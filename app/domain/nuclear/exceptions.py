# app/domain/nuclear/exceptions.py

import uuid


class NuclearReactorNotFoundError(Exception):
    def __init__(self, reactor_id):
        super().__init__(f"Nuclear reactor with id '{reactor_id}' was not found.")
        self.reactor_id = reactor_id