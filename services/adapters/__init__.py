from services.adapters.ashby import AshbyAdapter
from services.adapters.arbeitnow import ArbeitnowAdapter
from services.adapters.base import OpportunityAdapter, StaticOpportunityAdapter
from services.adapters.lever import LeverAdapter
from services.adapters.devto import DevToAdapter
from services.adapters.duckduckgo import DuckDuckGoAdapter
from services.adapters.greenhouse import GreenhouseAdapter
from services.adapters.github import GitHubIssuesAdapter
from services.adapters.hackernews import HackerNewsAdapter
from services.adapters.hackernews_jobs import HackerNewsJobsAdapter
from services.adapters.remotive import RemotiveAdapter


__all__ = [
    "AshbyAdapter",
    "ArbeitnowAdapter",
    "DevToAdapter",
    "DuckDuckGoAdapter",
    "GreenhouseAdapter",
    "GitHubIssuesAdapter",
    "HackerNewsAdapter",
    "HackerNewsJobsAdapter",
    "LeverAdapter",
    "OpportunityAdapter",
    "RemotiveAdapter",
    "StaticOpportunityAdapter",
]
