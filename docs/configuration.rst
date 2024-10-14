Configuration
=============

AgentHost can be configured using a configuration file or through environment variables.

Configuration File
------------------

By default, AgentHost looks for a configuration file named `agenthost.yaml` in the current working directory. You can specify a different file using the `--config` command-line option.

Here's an example configuration file:

.. code-block:: yaml

    agent:
      name: MyAgent
      log_level: INFO

    plugins:
      - name: WeatherPlugin
        api_key: your_api_key_here

    tasks:
      - name: daily_weather_check
        schedule: "0 9 * * *"  # Run at 9 AM daily

Environment Variables
---------------------

You can also configure AgentHost using environment variables. Environment variables take precedence over the configuration file.

- `AGENTHOST_NAME`: Set the agent name
- `AGENTHOST_LOG_LEVEL`: Set the log level (DEBUG, INFO, WARNING, ERROR)
- `AGENTHOST_PLUGINS`: Comma-separated list of plugins to load

Example:

.. code-block:: bash

    export AGENTHOST_NAME=MyAgent
    export AGENTHOST_LOG_LEVEL=DEBUG
    export AGENTHOST_PLUGINS=WeatherPlugin,TimePlugin

Refer to the API documentation for a complete list of configuration options.
