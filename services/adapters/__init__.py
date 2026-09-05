from services.adapters.arbeitnow import ArbeitnowAdapter
from services.adapters.base import OpportunityAdapter, StaticOpportunityAdapter
from services.adapters.devto import DevToAdapter
from services.adapters.duckduckgo import DuckDuckGoAdapter
from services.adapters.github import GitHubIssuesAdapter
from services.adapters.hackernews import HackerNewsAdapter
from services.adapters.remotive import RemotiveAdapter


__all__ = [
    "ArbeitnowAdapter",
    "DevToAdapter",
    "DuckDuckGoAdapter",
    "GitHubIssuesAdapter",
    "HackerNewsAdapter",
    "OpportunityAdapter",
    "RemotiveAdapter",
    "StaticOpportunityAdapter",
]
