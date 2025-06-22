# app/nfs_utils.py
"""
NFS Utilities module for the VideoInventory application.
This module manages NFS mount points, providing functionality to mount and unmount
NFS shares across different operating systems (Linux and macOS).
"""

import os
import subprocess
from pathlib import Path
import logging
import platform
import shutil

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class NFSManager:
    def __init__(self, base_mount_dir, nfs_directories):
        """
        Initialize NFS Manager to mount NFS shares under a single base directory.

        :param base_mount_dir: The base directory for all NFS mounts under the project.
                               Example: '/Users/sst/PycharmProjects/videoinventor/mountpoints'
        :param nfs_directories: A dictionary of remote NFS paths to mount.
                                Example: {'/cluster-01/gaystuff-inbox': 'server:/path/to/shared1', ...}
        """
        self.base_mount_dir = Path(base_mount_dir).resolve()
        self.nfs_directories = nfs_directories  # In the form {relative_mount_path: remote_path}
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base mount directory exists."""
        if not self.base_mount_dir.exists():
            self.base_mount_dir.mkdir(parents=True, exist_ok=True)

    def _run_command(self, command):
        """
        Run a shell command and handle errors.
        """
        try:
            result = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Error running command {' '.join(command)}: {e}")
            return 1, "", str(e)

    def construct_mountpoints(self):
        """Create necessary local directories for NFS mounts under the base directory."""
        for relative_path in self.nfs_directories.keys():
            full_path = self.base_mount_dir / relative_path.strip("/")
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)

    def mount_all(self):
        """
        Mount all NFS shares under the base directory.
        In development/test mode, this creates mock directories instead.
        """
        logger.info("Creating mount points...")
        self.construct_mountpoints()  # Ensure mount points exist



        # Real NFS mounting logic for production environments
        for relative_path, remote_path in self.nfs_directories.items():
            full_mount_point = self.base_mount_dir / relative_path.strip("/")

            if not self.is_mounted(full_mount_point):
                command = ["mount", "-t", "nfs", remote_path, str(full_mount_point)]
                returncode, stdout, stderr = self._run_command(command)
                if returncode == 0:
                    logger.info(f"Mounted {remote_path} to {full_mount_point}")
                else:
                    logger.error(f"Failed to mount {remote_path}: {stderr}")
            else:
                logger.info(f"{full_mount_point} is already mounted.")


    def unmount_all(self):
        """
        Unmount all directories in the base mount directory.
        In development mode, this simply logs the action without doing anything.
        """
        # Check if we're in development mode
        is_dev_mode = platform.system() == 'Darwin' or not shutil.which('umount')

        if is_dev_mode:
            logger.info("Running in development mode. Skipping unmount operations.")
            return

        # Real unmounting logic for production environments
        for relative_path in self.nfs_directories.keys():
            full_mount_point = self.base_mount_dir / relative_path.strip("/")
            if self.is_mounted(full_mount_point):
                command = ["umount", str(full_mount_point)]
                returncode, stdout, stderr = self._run_command(command)
                if returncode == 0:
                    logger.info(f"Unmounted {full_mount_point}")
                else:
                    logger.error(f"Failed to unmount {full_mount_point}: {stderr}")

    def is_mounted(self, mount_point):
        """
        Check if a specific mount point is currently mounted.
        For macOS/development, we just check if the directory exists and has content.
        """
        # For macOS or when mountpoint command is not available
        if platform.system() == 'Darwin' or not shutil.which('mountpoint'):
            # Check if directory exists and has some files
            if not os.path.exists(mount_point):
                return False

            # If it exists and has content, consider it "mounted"
            try:
                return len(os.listdir(mount_point)) > 0
            except:
                return False

        # For Linux, use the mountpoint command
        command = ["mountpoint", "-q", str(mount_point)]
        return subprocess.run(command).returncode == 0

    def list_mountpoints(self):
        """
        List all resolved mount points.
        """
        return [str(self.base_mount_dir / relative_path.strip("/")) for relative_path in self.nfs_directories.keys()]