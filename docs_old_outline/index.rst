Welcome to AgentHost's documentation!
====================================

AgentHost is a powerful, plugin-based Python framework for creating and managing AI agents. It offers a flexible architecture with an open, customizable registry system for easy installation and management of plugins, agents, and AI capabilities.

Key Features:
- Open registry system for plugins, agents, personas, models, and knowledgebases
  - Customizable and swappable for user-specific registries
- Extensible plugin architecture
- Customizable AI agents with persona definitions
- Intelligent service management based on agent requirements
- Flexible service providers for various AI capabilities
- Easily customizable UI
- Support for both local and remote AI services
- RAG: easily share, find and use pre-generated embeddings for topic knowledgebases

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   core_concepts
   registry_system
   plugin_system
   agents_and_personas
   services_and_providers
   ui_customization
   deployment
   rag_and_knowledgebases
   usage
   configuration
   examples
   api
   developer_guide
   user_guide
   troubleshooting

Core Concepts Overview
----------------------

AgentHost revolves around several key concepts:

1. **Open Registry**: A flexible system for indexing and managing plugins, agents, personas, and potentially models. It can be customized or replaced with user-specific registries.

2. **Plugins**: Extend the functionality of AgentHost, providing new features, services, or integrations.

3. **Agents and Personas**: AI agents with defined capabilities and customizable personalities.

4. **Services and Providers**: Backend services that power agent capabilities, with support for both local and remote implementations.

5. **Intelligent Service Management**: The system automatically determines and installs required services based on agent definitions.

6. **UI Customization**: Easily modifiable user interface through theme overrides and plugin injections.

7. **RAG and Knowledgebases**: Planned features for enhanced AI capabilities, also integrated with the registry system.

Project Structure
-----------------

The AgentHost project is structured as follows:

.. code-block:: text

    /files/ah/
    ├── docs/
    │   ├── conf.py
    │   ├── index.rst
    │   ├── installation.rst
    │   ├── core_concepts.rst
    │   ├── registry_system.rst
    │   ├── plugin_system.rst
    │   ├── agents_and_personas.rst
    │   ├── services_and_providers.rst
    │   ├── ui_customization.rst
    │   ├── deployment.rst
    │   ├── rag_and_knowledgebases.rst
    │   ├── usage.rst
    │   ├── configuration.rst
    │   ├── examples.rst
    │   ├── api.rst
    │   ├── developer_guide.rst
    │   ├── user_guide.rst
    │   └── troubleshooting.rst
    ├── agenthost/
    │   └── (source files)
    ├── tests/
    ├── .readthedocs.yml
    ├── setup.py
    └── README.md

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
