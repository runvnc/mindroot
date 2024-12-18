
Mindroot

[![PyPI](https://img.shields.io/pypi/v/mindroot)](https://pypi.org/project/mindroot/)

**Note: some of the following is a work in progress and not yet functional. A few of them aren't really started.**

Mindroot is a powerful plugin-based Python framework for creating, deploying, and sharing AI agents and related models. It offers a flexible architecture with indices and a public registry (coming soon) for easily sharing and finding plugins, agents, personas, services, knowledgebases, and apps.

Installation
------------

You can install Mindroot using pip:

```bash
pip install mindroot
```

For development, you can install the package in editable mode:

```bash
git clone https://github.com/mindroot/mindroot.git
cd mindroot
pip install -e .
```


Key Features:

- Public registry for sharing and finding plugins, agents, personas, models, and knowledgebases
  - https://registry.agenthost.org (work in progress)
  - Customizable and swappable for user-specific registries
- Extensible plugin architecture for adding services, commands, and building arbitrary web apps
- Customizable AI agents with persona definitions
- Intelligent service management based on agent requirements
- Flexible service providers for various AI capabilities
- Plugins can add/use hooks and pipelines such as for modifying prompts, running startup commands, or anything you want
- Easily customizable UI built on Jinja2 and Lit Web Components
- Support for both local and remote AI services
- RAG: easily share, find and use pre-generated embeddings and documents for topic knowledgebases

Core Concepts Overview
----------------------

mindroot revolves around several key concepts:

1. **Open Public Registry**: A flexible system for indexing and sharing plugins, agents, personas, and potentially models. It can be customized or replaced with user-specific registries.

2. **Plugins**: Extend the functionality of mindroot, providing new features, services, or integrations.

3. **Agents and Personas**: AI agents with defined capabilities and customizable personalities.

4. **Services and Providers**: Backend services that power agent capabilities, with support for swapping between local and remote implementations.

5. **Intelligent Service Management**: The system automatically determines and installs required services based on agent definitions.

6. **UI Customization**: Easily modifiable user interface through theme overrides and injections.

7. **RAG and Knowledgebases**: The community can easily share and search for topic embeddings and document sets rather than everyone rebuilding them per topic.
