Scale API Compose Pilot Documentation
====================================

Scale API Compose Pilot is a Python library and CLI tool for deploying Docker Compose workloads to TrueNAS Scale via WebSocket API.

.. image:: https://github.com/svnstfns/scale-api-compose-pilot/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/svnstfns/scale-api-compose-pilot/actions/workflows/ci.yml
   :alt: CI/CD Status

.. image:: https://badge.fury.io/py/scale-api-compose-pilot.svg
   :target: https://badge.fury.io/py/scale-api-compose-pilot
   :alt: PyPI version

Features
--------

* 🐳 **Docker Compose Support**: Deploy Docker Compose stacks to TrueNAS Scale
* 🔌 **WebSocket API**: Uses TrueNAS Scale's modern WebSocket API (Electric Eel)
* 🛠️ **CLI Interface**: Easy-to-use command-line tool
* 📦 **Python Library**: Programmatic access for automation
* 🔒 **Authentication**: Secure API key authentication
* 🔄 **App Management**: Start, stop, delete, and update apps

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Install TrueNAS API client first
   pip install git+https://github.com/truenas/api_client.git
   
   # Install scale-api-compose-pilot
   pip install scale-api-compose-pilot

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # Set up environment
   export TRUENAS_HOST=your-truenas-host.local
   export TRUENAS_API_KEY=your-api-key-here
   
   # Deploy a Docker Compose stack
   scale-compose deploy ./docker-compose.yml my-app
   
   # List all apps
   scale-compose list
   
   # Start/stop apps
   scale-compose start my-app
   scale-compose stop my-app

Python API
~~~~~~~~~~

.. code-block:: python

   import asyncio
   from scale_api_compose_pilot import TrueNASDockerManager
   
   async def main():
       async with TrueNASDockerManager() as manager:
           # List apps
           apps = await manager.list_apps()
           print(f"Found {len(apps)} apps")
           
           # Deploy Docker Compose
           await manager.deploy_compose_stack(
               './docker-compose.yml', 
               'my-app'
           )
   
   asyncio.run(main())

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index
   cli
   examples
   troubleshooting
   contributing

API Reference
~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/manager
   api/exceptions
   api/discovery
   api/config

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`