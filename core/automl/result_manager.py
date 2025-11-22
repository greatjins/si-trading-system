"""
AutoML 결과 관리
"""
import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from utils.types import BacktestResult
from utils.logger import setup_logger
from data.repository import BacktestRepository

logger = setup_logger(__name__)


class AutoMLResultManager:
    """
    AutoML 결과 관리
    
    - 최적 파라미터 저장 (JSON)
    - 백테스트 결과 저장 (DB)
    - 결과 순위화
    """
    
    def __init__(
        self,
        output_dir: str = "automl_results",
        repository: BacktestRepository = None
    ):
        """
        Args:
            output_dir: 결과 저장 디렉토리
            repository: 백테스트 저장소
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.repository = repository or BacktestRepository()
        
        logger.info(f"AutoMLResultManager initialized: {self.output_dir}")
    
    def save_best_parameters(
        self,
        results: List[BacktestResult],
        metric: str = "sharpe_ratio",
        top_n: int = 10,
        filename: str = None
    ) -> str:
        """
        최고 성과 파라미터 저장
        
        Args:
            results: 백테스트 결과 리스트
            metric: 정렬 기준 메트릭
            top_n: 상위 N개
            filename: 파일명 (None이면 자동 생성)
        
        Returns:
            저장된 파일 경로
        """
        # 정렬
        sorted_results = self._sort_results(results, metric)
        top_results = sorted_results[:top_n]
        
        # JSON 데이터 생성
        data = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "top_n": top_n,
            "total_results": len(results),
            "best_parameters": []
        }
        
        for i, result in enumerate(top_results, 1):
            data["best_parameters"].append({
                "rank": i,
                "strategy": result.strategy_name,
                "parameters": result.parameters,
                "metrics": {
                    "total_return": result.total_return,
                    "mdd": result.mdd,
                    "sharpe_ratio": result.sharpe_ratio,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "total_trades": result.total_trades
                }
            })
        
        # 파일 저장
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"best_params_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Best parameters saved: {filepath}")
        return str(filepath)
    
    def save_to_database(
        self,
        results: List[BacktestResult]
    ) -> List[int]:
        """
        백테스트 결과를 데이터베이스에 저장
        
        Args:
            results: 백테스트 결과 리스트
        
        Returns:
            저장된 백테스트 ID 리스트
        """
        saved_ids = []
        
        for result in results:
            try:
                backtest_id = self.repository.save_backtest_result(result)
                saved_ids.append(backtest_id)
            except Exception as e:
                logger.error(f"Failed to save result: {e}")
        
        logger.info(f"Saved {len(saved_ids)} results to database")
        return saved_ids
    
    def load_parameters(self, filepath: str) -> Dict[str, Any]:
        """
        저장된 파라미터 로드
        
        Args:
            filepath: JSON 파일 경로
        
        Returns:
            파라미터 데이터
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Parameters loaded: {filepath}")
        return data
    
    def generate_report(
        self,
        results: List[BacktestResult],
        filename: str = None
    ) -> str:
        """
        AutoML 결과 리포트 생성
        
        Args:
            results: 백테스트 결과 리스트
            filename: 파일명
        
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"automl_report_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("AutoML 결과 리포트\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"생성 시간: {datetime.now()}\n")
            f.write(f"총 결과 수: {len(results)}\n\n")
            
            # 통계
            returns = [r.total_return for r in results]
            mdds = [r.mdd for r in results]
            sharpes = [r.sharpe_ratio for r in results]
            
            f.write("[통계]\n")
            f.write(f"평균 수익률: {sum(returns)/len(returns):+.2%}\n")
            f.write(f"최고 수익률: {max(returns):+.2%}\n")
            f.write(f"최저 수익률: {min(returns):+.2%}\n")
            f.write(f"평균 MDD: {sum(mdds)/len(mdds):.2%}\n")
            f.write(f"평균 Sharpe: {sum(sharpes)/len(sharpes):.2f}\n\n")
            
            # 상위 10개
            sorted_results = sorted(
                results,
                key=lambda r: r.sharpe_ratio,
                reverse=True
            )[:10]
            
            f.write("[상위 10개 결과]\n")
            for i, result in enumerate(sorted_results, 1):
                f.write(f"\n{i}. {result.strategy_name}\n")
                f.write(f"   파라미터: {result.parameters}\n")
                f.write(f"   수익률: {result.total_return:+.2%}\n")
                f.write(f"   MDD: {result.mdd:.2%}\n")
                f.write(f"   Sharpe: {result.sharpe_ratio:.2f}\n")
        
        logger.info(f"Report generated: {filepath}")
        return str(filepath)
    
    def _sort_results(
        self,
        results: List[BacktestResult],
        metric: str
    ) -> List[BacktestResult]:
        """결과 정렬"""
        if metric == "total_return":
            return sorted(results, key=lambda r: r.total_return, reverse=True)
        elif metric == "sharpe_ratio":
            return sorted(results, key=lambda r: r.sharpe_ratio, reverse=True)
        elif metric == "mdd":
            return sorted(results, key=lambda r: r.mdd)
        else:
            return results
