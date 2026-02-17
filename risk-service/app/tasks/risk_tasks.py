"""
Risk evaluation Celery tasks.

Consumes transaction IDs from the queue, runs the hybrid scoring pipeline,
updates the database, creates alerts for HIGH risk, and caches results in Redis.
"""

import json
from uuid import UUID

import redis
import structlog
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.services.risk_scorer import evaluate_transaction_risk
from app.tasks.celery_app import celery_app

logger = structlog.get_logger("risk_tasks")

# Synchronous DB engine for Celery workers (Celery doesn't support asyncio natively)
_sync_engine = create_engine(settings.database_url_sync, pool_size=10, max_overflow=5)
SyncSessionFactory = sessionmaker(bind=_sync_engine)

# Synchronous Redis client for caching
_redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

CACHE_TTL_SECONDS = 600  # 10 minutes


@celery_app.task(name="app.tasks.risk_tasks.evaluate_transaction", bind=True, max_retries=3)
def evaluate_transaction(self, transaction_id: str) -> dict:
    """Evaluate the fraud risk of a transaction.

    Steps:
        1. Load transaction from DB.
        2. Run hybrid risk scoring (ML + rules).
        3. Update transaction with scores and status.
        4. If HIGH risk, create an alert record.
        5. Cache the result in Redis.

    Args:
        transaction_id: UUID string of the transaction to evaluate.

    Returns:
        dict with scoring results.
    """
    logger.info("evaluate_transaction_start", transaction_id=transaction_id)

    try:
        with SyncSessionFactory() as session:
            # 1. Load transaction
            from app.models.transaction import Transaction, Alert

            txn = session.query(Transaction).filter(
                Transaction.id == UUID(transaction_id)
            ).first()

            if txn is None:
                logger.error("transaction_not_found", transaction_id=transaction_id)
                return {"error": "Transaction not found"}

            # 2. Run risk evaluation
            result = evaluate_transaction_risk(
                amount=float(txn.amount),
                hour=txn.transaction_time.hour,
                is_new_device=bool(txn.device_id),  # Simplified: any device_id = potentially new
                is_unusual_location=bool(txn.location),  # Simplified: any location data = check
            )

            # 3. Update transaction
            txn.ml_score = result["ml_score"]
            txn.rule_score = result["rule_score"]
            txn.final_score = result["final_score"]
            txn.status = result["status"]
            txn.risk_level = result["risk_level"]
            session.flush()

            # 4. Create alert if HIGH risk
            if result["risk_level"] == "HIGH":
                alert = Alert(
                    transaction_id=txn.id,
                    alert_type="HIGH_RISK_TRANSACTION",
                    message=(
                        f"Transaction {txn.id} blocked with final_score={result['final_score']:.4f}. "
                        f"Amount: {txn.amount}, ML: {result['ml_score']:.4f}, "
                        f"Rules: {result['rule_score']:.4f}"
                    ),
                )
                session.add(alert)
                logger.warning(
                    "high_risk_alert_created",
                    transaction_id=transaction_id,
                    final_score=result["final_score"],
                )

            session.commit()

            # 5. Cache result in Redis
            cache_key = f"txn_result:{transaction_id}"
            cache_data = {
                "id": transaction_id,
                "user_id": str(txn.user_id),
                "amount": float(txn.amount),
                "currency": txn.currency,
                "location": txn.location,
                "device_id": txn.device_id,
                "ip_address": txn.ip_address,
                "transaction_time": txn.transaction_time.isoformat(),
                "status": result["status"],
                "rule_score": result["rule_score"],
                "ml_score": result["ml_score"],
                "final_score": result["final_score"],
                "risk_level": result["risk_level"],
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
                "updated_at": txn.updated_at.isoformat() if txn.updated_at else None,
            }
            _redis_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(cache_data))

            logger.info(
                "evaluate_transaction_complete",
                transaction_id=transaction_id,
                status=result["status"],
                risk_level=result["risk_level"],
                final_score=result["final_score"],
            )
            return result

    except Exception as exc:
        logger.error("evaluate_transaction_error", transaction_id=transaction_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
