import sys
import os
import asyncio
from termcolor import colored
from ..plugins.installation import download_github_files
from ..plugins.manifest import update_plugin_manifest

async def _stream_subprocess(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, prefix):
        while True:
            line = await stream.readline()
            if line:
                print(f"{prefix}{line.decode().strip()}")
            else:
                break

    await asyncio.gather(
        read_stream(process.stdout, ''),
        read_stream(process.stderr, colored('ERR: ', 'red'))
    )

    await process.wait()
    return process.returncode

async def install_plugins_from_cli(plugin_sources: list, reinstall: bool = False):
    """
    Install plugins from the command line, streaming output.
    """
    print(colored(f"Attempting to install {len(plugin_sources)} plugins...", "cyan"))
    results = []

    for plugin_source in plugin_sources:
        plugin_name = plugin_source.split('/')[-1]
        print(colored(f"\n=== Installing {plugin_name} ===", "yellow"))

        try:
            if not reinstall:
                import pkg_resources
                try:
                    pkg_resources.get_distribution(plugin_name)
                    print(colored(f"{plugin_name} is already installed. Use --reinstall to update or force.", "green"))
                    results.append({"plugin": plugin_name, "status": "already_installed"})
                    continue
                except pkg_resources.DistributionNotFound:
                    pass # Not installed, proceed

            if '/' in plugin_source:  # GitHub source
                print(f"Installing from GitHub: {plugin_source}")
                plugin_dir, _, plugin_info = download_github_files(plugin_source)
                cmd = [sys.executable, '-m', 'pip', 'install', '-e', plugin_dir]
                if reinstall:
                    cmd.append('--force-reinstall')
                return_code = await _stream_subprocess(cmd)

                if return_code == 0:
                    print(colored(f"Successfully installed {plugin_name} from {plugin_source}", "green"))
                    update_plugin_manifest(
                        plugin_info['name'],
                        'github',
                        os.path.abspath(plugin_dir),
                        remote_source=plugin_source,
                        version=plugin_info.get('version', '0.0.1'),
                        metadata=plugin_info
                    )
                    results.append({"plugin": plugin_name, "status": "success", "source": "github"})
                else:
                    raise Exception(f"pip install failed with exit code {return_code}")

            else:  # PyPI source
                print(f"Installing from PyPI: {plugin_name}")
                cmd = [sys.executable, '-m', 'pip', 'install', plugin_name]
                if reinstall:
                    cmd.extend(['--upgrade', '--force-reinstall'])
                return_code = await _stream_subprocess(cmd)

                if return_code == 0:
                    print(colored(f"Successfully installed {plugin_name} from PyPI", "green"))
                    update_plugin_manifest(plugin_name, 'pypi', None)
                    results.append({"plugin": plugin_name, "status": "success", "source": "pypi"})
                else:
                    raise Exception(f"pip install failed with exit code {return_code}")

        except Exception as e:
            print(colored(f"ERROR: Failed to install {plugin_name}: {str(e)}", "red"))
            results.append({"plugin": plugin_name, "status": "error", "message": str(e)})

    print(colored("\nPlugin installation process finished.", "cyan"))
    # You can optionally print a summary of results here
