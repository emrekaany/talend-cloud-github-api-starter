"""Read-only Talend Cloud and public GitHub inventory starter."""

from .github import GITHUB_API_VERSION, GitHubPublicClient, GitHubSnapshot
from .talend_cloud import TalendCloudClient
from .xmlsafe import JobDescriptor, inventory_talend_jobs, parse_talend_job

__all__ = [
    "GITHUB_API_VERSION",
    "GitHubPublicClient",
    "GitHubSnapshot",
    "JobDescriptor",
    "TalendCloudClient",
    "inventory_talend_jobs",
    "parse_talend_job",
]

__version__ = "0.1.1"
