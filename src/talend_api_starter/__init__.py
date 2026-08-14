"""Read-only Talend API, local Studio, and public GitHub CLI toolkit."""

from ._version import __version__
from .github import GITHUB_API_VERSION, GitHubPublicClient, GitHubSnapshot
from .talend_api import TalendApiClient
from .xmlsafe import JobDescriptor, inventory_talend_jobs, parse_talend_job

__all__ = [
    "GITHUB_API_VERSION",
    "GitHubPublicClient",
    "GitHubSnapshot",
    "JobDescriptor",
    "TalendApiClient",
    "__version__",
    "inventory_talend_jobs",
    "parse_talend_job",
]
