"""
SSH tunnel manager for connecting to Apache Atlas behind firewalls.
Uses Paramiko for SSH connections and port forwarding.
"""

import logging
import os
from contextlib import contextmanager

import paramiko

logger = logging.getLogger(__name__)


class SSHTunnel:
    """Manages SSH tunnels for accessing remote services."""

    def __init__(self, ssh_host: str, ssh_user: str, ssh_key_path: str, ssh_port: int = 22):
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_key_path = ssh_key_path
        self.ssh_port = ssh_port
        self.client: paramiko.SSHClient | None = None

    @classmethod
    def from_env(cls) -> "SSHTunnel":
        return cls(
            ssh_host=os.environ["SSH_HOST"],
            ssh_user=os.environ["SSH_USER"],
            ssh_key_path=os.environ.get("SSH_KEY_PATH", "~/.ssh/id_rsa"),
            ssh_port=int(os.environ.get("SSH_PORT", "22")),
        )

    def connect(self) -> paramiko.SSHClient:
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        self.client.connect(
            hostname=self.ssh_host,
            port=self.ssh_port,
            username=self.ssh_user,
            key_filename=os.path.expanduser(self.ssh_key_path),
        )
        logger.info("SSH connected to %s@%s", self.ssh_user, self.ssh_host)
        return self.client

    def execute_remote(self, command: str) -> tuple[str, str]:
        """Execute a command on the remote server and return (stdout, stderr)."""
        if not self.client:
            self.connect()
        _, stdout, stderr = self.client.exec_command(command)
        out = stdout.read().decode("utf-8")
        err = stderr.read().decode("utf-8")
        return out, err

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            logger.info("SSH connection closed")

    @contextmanager
    def session(self):
        """Context manager for SSH sessions."""
        try:
            self.connect()
            yield self
        finally:
            self.close()
