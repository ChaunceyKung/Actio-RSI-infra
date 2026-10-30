"""TicTacToe AEC adapter. PettingZoo alone owns board, turns and rewards."""
from actio.adapters.environment.session import SessionAdmission
from actio.contracts.environment import Capabilities, Decision, Frame, Resolution, Status, Submission
from actio.contracts.json import ContractError


class TicTacToeSession(SessionAdmission):
    capabilities = Capabilities()

    def __init__(self, config):
        super().__init__()
        if set(config) - {'seed'}:
            raise ContractError('unknown TicTacToe config')
        from pettingzoo.classic import tictactoe_v3
        self.env = tictactoe_v3.env(render_mode=None)
        try:
            self.env.reset(seed=config.get('seed', 0))
        except BaseException:
            self.env.close()
            raise

    def status(self):
        self.check_open()
        terminated = all(self.env.terminations.values())
        truncated = any(self.env.truncations.values())
        return Status(terminated, truncated, 'game_over' if terminated else 'truncated' if truncated else None,
                      {'rewards': dict(self.env.rewards)} if terminated or truncated else {})

    def observe(self):
        self.check_open()
        if self.status().done:
            return Frame(self.revision, ())
        agent = self.env.agent_selection
        obs = self.env.observe(agent)
        mask = obs['action_mask'].tolist()
        return Frame(self.revision, (Decision(agent, obs['observation'].tolist(),
            tuple(i for i, legal in enumerate(mask) if legal),
            {'action_mask': mask, 'type': 'integer', 'minimum': 0, 'maximum': 8}),))

    def submit(self, actions, *, operation, expected_revision):
        cached = self.admit(actions, operation, expected_revision)
        if cached is not None:
            return cached
        frame = self.observe()
        decision = frame.decisions[0] if frame.decisions else None
        reason = None
        if not decision:
            reason = 'episode_done'
        elif set(actions) != {decision.agent}:
            reason = 'wrong_acting_agents'
        elif type(actions[decision.agent]) is not int or actions[decision.agent] not in decision.legal_actions:
            reason = 'illegal_action'
        if reason:
            return self.remember(actions, operation, expected_revision,
                                 Submission(operation, 'rejected', self.revision, reason))
        # Adapter rejects malformed intent before dispatch; native step remains
        # the sole world executor. Native reward/termination semantics are intact.
        self.env.step(actions[decision.agent])
        self.revision += 1
        outcome = Resolution(len(self.outcomes) + 1, self.revision, operation,
            {'actions': actions, 'rewards': dict(self.env.rewards),
             'terminations': dict(self.env.terminations), 'truncations': dict(self.env.truncations)})
        self.outcomes.append(outcome)
        return self.remember(actions, operation, expected_revision,
            Submission(operation, 'accepted', self.revision, outcomes=(outcome,)))

    def close(self):
        if not self.closed:
            self.env.close()
            self.closed = True


def create(config):
    return TicTacToeSession(config)


def identity():
    from importlib.metadata import version
    return {name: version(name) for name in ('pettingzoo', 'gymnasium', 'numpy', 'pygame')}


create.identity = identity
