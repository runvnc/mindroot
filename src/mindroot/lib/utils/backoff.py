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
        self._states = {}  # Stores {'identifier': {'attempts': N}}

    def _calculate_delay(self, attempts):
        """Calculates the delay based on the number of attempts."""
        if attempts <= 0:
            return 0.0
        delay = self.initial_delay * (self.factor ** (attempts - 1))
        return min(delay, self.max_delay)

    def record_failure(self, identifier):
        """Records a failure for the given identifier, increasing its backoff attempts."""
        state = self._states.get(identifier, {'attempts': 0})
        state['attempts'] += 1
        self._states[identifier] = state
        # print(f"Backoff: Recorded failure for '{identifier}', attempts: {state['attempts']}")

    def record_success(self, identifier):
        """Records a success for the given identifier, decreasing its backoff attempts."""
        if identifier in self._states:
            state = self._states[identifier]
            if state['attempts'] > 0:
                state['attempts'] -= 1
            
            if state['attempts'] == 0:
                # print(f"Backoff: Reset for '{identifier}' after success.")
                del self._states[identifier] # Fully reset, remove state
            else:
                # print(f"Backoff: Recorded success for '{identifier}', attempts remaining: {state['attempts']}")
                self._states[identifier] = state
        # else:
            # print(f"Backoff: Recorded success for '{identifier}', no active backoff.")

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
            # Add random jitter: +/- up to 25% of the initial_delay, or a small fixed range
            # This jitter is simple; more sophisticated jitter might be a percentage of base_delay itself.
            jitter_amount = random.uniform(-self.initial_delay * 0.25, self.initial_delay * 0.25)
            wait_time = max(0.0, base_delay + jitter_amount) # Ensure wait time is not negative
        else:
            wait_time = base_delay
        
        # print(f"Backoff: Wait time for '{identifier}': {wait_time:.2f}s (attempts: {state['attempts']})")
        return wait_time

if __name__ == '__main__':
    # Example Usage
    backoff_manager = ExponentialBackoff(initial_delay=1, max_delay=10, factor=2, jitter=True)
    api_endpoint = "my_api_call"

    print(f"Initial wait time for {api_endpoint}: {backoff_manager.get_wait_time(api_endpoint)}s")

    # Simulate some failures
    for i in range(5):
        print(f"\nAttempting operation for {api_endpoint}...")
        current_wait = backoff_manager.get_wait_time(api_endpoint)
        if current_wait > 0:
            print(f"Rate limit active. Waiting for {current_wait:.2f} seconds.")
            # In a real async app, this would be asyncio.sleep(current_wait)
            # time.sleep(current_wait) 
        
        # Simulate API call
        print(f"Making API call (attempt {i+1})...")
        is_successful = random.choice([True, False, False]) # Simulate success/failure

        if not is_successful and i < 4: # Let's make it succeed on the last try for demo
            print(f"API call failed for {api_endpoint} (simulated rate limit).")
            backoff_manager.record_failure(api_endpoint)
        else:
            print(f"API call successful for {api_endpoint}.")
            backoff_manager.record_success(api_endpoint)
            # break # If successful, might break retry loop in real code
        
        print(f"Current state for {api_endpoint}: {backoff_manager._states.get(api_endpoint)}")

    print(f"\nFinal wait time for {api_endpoint} after operations: {backoff_manager.get_wait_time(api_endpoint)}s")

    # Simulate successes to see it recover
    print("\nSimulating successes to recover...")
    for _ in range(5):
        if api_endpoint not in backoff_manager._states:
            print(f"{api_endpoint} backoff fully reset.")
            break
        backoff_manager.record_success(api_endpoint)
        print(f"Recorded success. Wait time: {backoff_manager.get_wait_time(api_endpoint):.2f}s, State: {backoff_manager._states.get(api_endpoint)}")
        if api_endpoint not in backoff_manager._states:
            print(f"{api_endpoint} backoff fully reset after last success.")
            break
