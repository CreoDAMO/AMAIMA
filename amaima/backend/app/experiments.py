import asyncpg
import secrets
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.billing import get_pool
from app.modules.nvidia_nim_client import chat_completion

logger = logging.getLogger(__name__)


async def create_experiment(
    api_key_id: str,
    name: str,
    model_a: str,
    model_b: str,
    description: Optional[str] = None,
    traffic_split: float = 0.5,
) -> Dict[str, Any]:
    """Create a new A/B testing experiment in draft status."""
    pool = await get_pool()
    experiment_id = secrets.token_hex(8)

    try:
        row = await pool.fetchrow(
            """INSERT INTO experiments 
               (id, name, description, model_a, model_b, traffic_split, status, api_key_id, 
                total_trials, model_a_wins, model_b_wins, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
               RETURNING id, name, description, model_a, model_b, traffic_split, status, 
                         api_key_id, total_trials, model_a_wins, model_b_wins, created_at, updated_at""",
            experiment_id, name, description, model_a, model_b, traffic_split, "draft", api_key_id,
            0, 0, 0
        )
        logger.info(f"Created experiment {experiment_id} for api_key {api_key_id}")
        return dict(row)
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        raise


async def list_experiments(api_key_id: str) -> List[Dict[str, Any]]:
    """List all experiments for an API key."""
    pool = await get_pool()

    try:
        rows = await pool.fetch(
            """SELECT id, name, description, model_a, model_b, traffic_split, status, 
                      api_key_id, total_trials, model_a_wins, model_b_wins, created_at, updated_at
               FROM experiments
               WHERE api_key_id = $1
               ORDER BY created_at DESC""",
            api_key_id
        )
        logger.info(f"Listed {len(rows)} experiments for api_key {api_key_id}")
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise


async def get_experiment(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Get experiment with recent trials (last 20)."""
    pool = await get_pool()

    try:
        # Get experiment details
        exp_row = await pool.fetchrow(
            """SELECT id, name, description, model_a, model_b, traffic_split, status, 
                      api_key_id, total_trials, model_a_wins, model_b_wins, created_at, updated_at
               FROM experiments
               WHERE id = $1""",
            experiment_id
        )

        if not exp_row:
            logger.warning(f"Experiment {experiment_id} not found")
            return None

        # Get recent trials (last 20)
        trials_rows = await pool.fetch(
            """SELECT id, experiment_id, query_text, model_a_response, model_b_response,
                      model_a_latency_ms, model_b_latency_ms, winner, created_at
               FROM experiment_trials
               WHERE experiment_id = $1
               ORDER BY created_at DESC
               LIMIT 20""",
            experiment_id
        )

        result = dict(exp_row)
        result["trials"] = [dict(r) for r in trials_rows]
        logger.info(f"Retrieved experiment {experiment_id} with {len(trials_rows)} trials")
        return result

    except Exception as e:
        logger.error(f"Error getting experiment: {e}")
        raise


async def update_experiment_status(experiment_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update experiment status (draft/running/paused/completed)."""
    pool = await get_pool()
    valid_statuses = {"draft", "running", "paused", "completed"}

    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    try:
        row = await pool.fetchrow(
            """UPDATE experiments
               SET status = $1, updated_at = NOW()
               WHERE id = $2
               RETURNING id, name, description, model_a, model_b, traffic_split, status, 
                         api_key_id, total_trials, model_a_wins, model_b_wins, created_at, updated_at""",
            status, experiment_id
        )

        if not row:
            logger.warning(f"Experiment {experiment_id} not found for status update")
            return None

        logger.info(f"Updated experiment {experiment_id} status to {status}")
        return dict(row)

    except Exception as e:
        logger.error(f"Error updating experiment status: {e}")
        raise


async def run_trial(experiment_id: str, query_text: str) -> Dict[str, Any]:
    """Run a trial against both models, record responses and latencies."""
    pool = await get_pool()

    try:
        # Get experiment details
        exp = await pool.fetchrow(
            """SELECT model_a, model_b FROM experiments WHERE id = $1""",
            experiment_id
        )

        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        model_a = exp["model_a"]
        model_b = exp["model_b"]

        # Run both models in parallel
        messages = [{"role": "user", "content": query_text}]

        # Run model A
        start_a = time.time()
        result_a = await chat_completion(model_a, messages)
        model_a_response = result_a["content"]
        model_a_latency = result_a["latency_ms"]

        # Run model B
        start_b = time.time()
        result_b = await chat_completion(model_b, messages)
        model_b_response = result_b["content"]
        model_b_latency = result_b["latency_ms"]

        # Record trial
        trial_row = await pool.fetchrow(
            """INSERT INTO experiment_trials
               (experiment_id, query_text, model_a_response, model_b_response,
                model_a_latency_ms, model_b_latency_ms, winner, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
               RETURNING id, experiment_id, query_text, model_a_response, model_b_response,
                         model_a_latency_ms, model_b_latency_ms, winner, created_at""",
            experiment_id, query_text, model_a_response, model_b_response,
            int(model_a_latency), int(model_b_latency), None
        )

        logger.info(f"Created trial {trial_row['id']} for experiment {experiment_id}")
        return dict(trial_row)

    except Exception as e:
        logger.error(f"Error running trial: {e}")
        raise


async def vote_trial(trial_id: int, winner: str) -> Dict[str, Any]:
    """Record winner for a trial and update experiment win counts."""
    pool = await get_pool()
    valid_winners = {"a", "b", "tie"}

    if winner not in valid_winners:
        raise ValueError(f"Invalid winner: {winner}. Must be one of {valid_winners}")

    try:
        # Get the trial to find the experiment
        trial = await pool.fetchrow(
            """SELECT experiment_id FROM experiment_trials WHERE id = $1""",
            trial_id
        )

        if not trial:
            raise ValueError(f"Trial {trial_id} not found")

        experiment_id = trial["experiment_id"]

        # Update trial winner
        trial_row = await pool.fetchrow(
            """UPDATE experiment_trials
               SET winner = $1
               WHERE id = $2
               RETURNING id, experiment_id, query_text, model_a_response, model_b_response,
                         model_a_latency_ms, model_b_latency_ms, winner, created_at""",
            winner, trial_id
        )

        # Update experiment win counts
        if winner == "a":
            await pool.execute(
                """UPDATE experiments
                   SET model_a_wins = model_a_wins + 1, updated_at = NOW()
                   WHERE id = $1""",
                experiment_id
            )
        elif winner == "b":
            await pool.execute(
                """UPDATE experiments
                   SET model_b_wins = model_b_wins + 1, updated_at = NOW()
                   WHERE id = $1""",
                experiment_id
            )
        # For "tie", we don't update win counts

        logger.info(f"Voted trial {trial_id} as winner: {winner}")
        return dict(trial_row)

    except Exception as e:
        logger.error(f"Error voting on trial: {e}")
        raise


async def get_experiment_stats(experiment_id: str) -> Dict[str, Any]:
    """Get detailed statistics for an experiment."""
    pool = await get_pool()

    try:
        # Get experiment
        exp = await pool.fetchrow(
            """SELECT id, name, model_a, model_b, total_trials, model_a_wins, model_b_wins, status
               FROM experiments
               WHERE id = $1""",
            experiment_id
        )

        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Get trial statistics
        stats = await pool.fetchrow(
            """SELECT 
                 COUNT(*) as total_trials,
                 AVG(model_a_latency_ms) as avg_latency_model_a,
                 AVG(model_b_latency_ms) as avg_latency_model_b,
                 MIN(model_a_latency_ms) as min_latency_model_a,
                 MIN(model_b_latency_ms) as min_latency_model_b,
                 MAX(model_a_latency_ms) as max_latency_model_a,
                 MAX(model_b_latency_ms) as max_latency_model_b,
                 SUM(CASE WHEN winner = 'a' THEN 1 ELSE 0 END) as model_a_wins_counted,
                 SUM(CASE WHEN winner = 'b' THEN 1 ELSE 0 END) as model_b_wins_counted,
                 SUM(CASE WHEN winner = 'tie' THEN 1 ELSE 0 END) as ties
               FROM experiment_trials
               WHERE experiment_id = $1""",
            experiment_id
        )

        total_trials = stats["total_trials"] or 0
        model_a_wins = stats["model_a_wins_counted"] or 0
        model_b_wins = stats["model_b_wins_counted"] or 0
        ties = stats["ties"] or 0

        # Calculate win rates
        model_a_win_rate = (model_a_wins / total_trials * 100) if total_trials > 0 else 0
        model_b_win_rate = (model_b_wins / total_trials * 100) if total_trials > 0 else 0
        tie_rate = (ties / total_trials * 100) if total_trials > 0 else 0

        result = {
            "experiment_id": experiment_id,
            "name": exp["name"],
            "model_a": exp["model_a"],
            "model_b": exp["model_b"],
            "status": exp["status"],
            "total_trials": total_trials,
            "model_a_wins": model_a_wins,
            "model_b_wins": model_b_wins,
            "ties": ties,
            "model_a_win_rate_percent": round(model_a_win_rate, 2),
            "model_b_win_rate_percent": round(model_b_win_rate, 2),
            "tie_rate_percent": round(tie_rate, 2),
            "avg_latency_model_a_ms": round(stats["avg_latency_model_a"] or 0, 2),
            "avg_latency_model_b_ms": round(stats["avg_latency_model_b"] or 0, 2),
            "min_latency_model_a_ms": stats["min_latency_model_a"],
            "min_latency_model_b_ms": stats["min_latency_model_b"],
            "max_latency_model_a_ms": stats["max_latency_model_a"],
            "max_latency_model_b_ms": stats["max_latency_model_b"],
        }

        logger.info(f"Retrieved stats for experiment {experiment_id}")
        return result

    except Exception as e:
        logger.error(f"Error getting experiment stats: {e}")
        raise


async def delete_experiment(experiment_id: str) -> bool:
    """Delete experiment and cascading trials."""
    pool = await get_pool()

    try:
        # Delete trials first (due to foreign key)
        await pool.execute(
            """DELETE FROM experiment_trials WHERE experiment_id = $1""",
            experiment_id
        )

        # Delete experiment
        result = await pool.execute(
            """DELETE FROM experiments WHERE id = $1""",
            experiment_id
        )

        logger.info(f"Deleted experiment {experiment_id} and its trials")
        return True

    except Exception as e:
        logger.error(f"Error deleting experiment: {e}")
        raise
