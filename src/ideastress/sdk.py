"""Public Python SDK for IdeaStress."""

from __future__ import annotations

from pathlib import Path

from ideastress.config import IdeaStressConfig
from ideastress.domain.models import AnalysisRequest, AnalysisResult, FinancialInputs, LedgerDiffResult, ReverseFrontier
from ideastress.finance.solver import solve_reverse_frontier
from ideastress.ledger.diff import diff_ledgers, load_ledger_yaml
from ideastress.orchestration.runner import AnalysisOrchestrator
from ideastress.storage.sqlite_store import SQLiteAnalysisStore


class IdeaStress:
    """High-level typed Python SDK client."""

    def __init__(self, config: IdeaStressConfig | None = None) -> None:
        self.config = config or IdeaStressConfig.from_env()
        self.store = SQLiteAnalysisStore(self.config.database_path)
        self.orchestrator = AnalysisOrchestrator(config=self.config, store=self.store)

    @classmethod
    def from_env(cls) -> IdeaStress:
        return cls(IdeaStressConfig.from_env())

    def analyze(self, request: AnalysisRequest, *, save: bool = True) -> AnalysisResult:
        return self.orchestrator.run(request, save_to_db=save)

    def solve(self, financials: FinancialInputs) -> ReverseFrontier:
        return solve_reverse_frontier(financials)

    def diff(self, before_path: str | Path, after_path: str | Path) -> LedgerDiffResult:
        return diff_ledgers(load_ledger_yaml(before_path), load_ledger_yaml(after_path))
