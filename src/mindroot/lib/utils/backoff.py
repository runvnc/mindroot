import time
import random

class ExponentialBackoff:
    """Manages exponential backoff state for multiple identifiers."""

    def __init__(self, initial_delay=1.0, max_delay=60.0, factor=2.0, jitter=True):
        """
        Initializes the ExponentialBackoff manager.

        Args:
            initial_delay (float): The initial delay in seconds after the first failure.
            max_delay (float): The maximum delay in seconds.
            factor (float): The multiplicative factor for the delay (e.g., 2 for doubling).
            jitter (bool): Whether to add a small random jitter to the delay.
        """
        self.initial_delay = float(initial_delay)
        self.max_delay = float(max_delay)
        self.factor = float(factor)
        self.jitter = jitter
        self._states = {}

    def _calculate_delay(self, attempts):
        """Calculates the delay based on the number of attempts."""
        if attempts <= 0:
            return 0.0
        delay = self.initial_delay * self.factor ** (attempts - 1)
        return min(delay, self.max_delay)

    def record_failure(self, identifier):
        """Records a failure for the given identifier, increasing its backoff attempts."""
        state = self._states.get(identifier, {'attempts': 0})
        state['attempts'] += 1
        self._states[identifier] = state

    def record_success(self, identifier):
        """Records a success for the given identifier, decreasing its backoff attempts."""
        if identifier in self._states:
            state = self._states[identifier]
            if state['attempts'] > 0:
                state['attempts'] -= 1
            if state['attempts'] == 0:
                del self._states[identifier]
            else:
                self._states[identifier] = state

    def get_wait_time(self, identifier):
        """
        Gets the current calculated wait time for the given identifier.

        Args:
            identifier (str): The identifier for the resource/service.

        Returns:
            float: The calculated wait time in seconds. Returns 0 if no backoff is active.
        """
        state = self._states.get(identifier)
        if not state or state['attempts'] == 0:
            return 0.0
        base_delay = self._calculate_delay(state['attempts'])
        if self.jitter:
            jitter_amount = random.uniform(-self.initial_delay * 0.25, self.initial_delay * 0.25)
            wait_time = max(0.0, base_delay + jitter_amount)
        else:
            wait_time = base_delay
        return wait_time
if __name__ == '__main__':
    backoff_manager = ExponentialBackoff(initial_delay=1, max_delay=10, factor=2, jitter=True)
    api_endpoint = 'my_api_call'
    for i in range(5):
        current_wait = backoff_manager.get_wait_time(api_endpoint)
        is_successful = random.choice([True, False, False])
        if not is_successful and i < 4:
            backoff_manager.record_failure(api_endpoint)
        else:
            backoff_manager.record_success(api_endpoint)
    for _ in range(5):
        if api_endpoint not in backoff_manager._states:
            break
        backoff_manager.record_success(api_endpoint)
        if api_endpoint not in backoff_manager._states:
            break