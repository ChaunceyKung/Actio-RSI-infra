"""Shared adapter admission bookkeeping, never a simulator or platform clock."""
from actio.contracts.environment import Submission
from actio.contracts.json import ContractError, digest


class SessionAdmission:
    def __init__(self):
        self.revision = 0
        self.closed = False
        self.outcomes = []
        self.requests = {}

    def check_open(self):
        if self.closed:
            raise ContractError('environment session closed')

    def admit(self, actions, operation, expected_revision):
        self.check_open()
        if not isinstance(operation, str) or not 0 < len(operation) <= 256:
            raise ContractError('bounded operation key required')
        signature = digest([actions, expected_revision])
        if operation in self.requests:
            original, reply = self.requests[operation]
            if signature != original:
                raise ContractError('environment operation key conflict')
            return reply
        if type(expected_revision) is not int or expected_revision != self.revision:
            return self.remember(actions, operation, expected_revision, Submission(
                operation, 'rejected', self.revision, 'stale_revision'))
        return None

    def remember(self, actions, operation, expected_revision, reply):
        self.requests[operation] = (digest([actions, expected_revision]), reply)
        return reply

    def poll(self, after=0):
        self.check_open()
        if type(after) is not int or not 0 <= after <= len(self.outcomes):
            raise ContractError('invalid outcome cursor')
        return tuple(self.outcomes[after:])
