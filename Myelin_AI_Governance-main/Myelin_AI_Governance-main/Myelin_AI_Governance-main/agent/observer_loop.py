import asyncio
import os
import json
import logging
import time
from datetime import datetime

# Add orchestrator to path
import sys
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_path, "orchestrator"))

from agent_core import get_agent_core

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [OBSERVER] %(message)s'
)
logger = logging.getLogger("ObserverLoop")

LOG_FILE = "agent_logs.jsonl"
POLL_INTERVAL_SECONDS = 5

async def tail_logs(filepath):
    """Async generator to tail a file like `tail -f`."""
    if not os.path.exists(filepath):
        # Create it if it doesn't exist
        open(filepath, 'a').close()
        
    with open(filepath, 'r', encoding='utf-8') as f:
        # Seek to the end of the file
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue
            yield line

async def process_log_entry(entry: dict, agent_core):
    """
    In the real world, this would run heavy meta-audits,
    aggregate metrics over time, or check against large databases.
    Here we simulate checking for trends or deep analysis.
    """
    user_prompt = entry.get("user_prompt", "")
    bot_response = entry.get("bot_response", "")
    risk_score = entry.get("risk_score", 0)

    # 1. Simulate a deep background check / trend analysis
    logger.info(f"Background Reviewing Conversation from {entry.get('timestamp')}")
    
    # Normally, we might re-run orchestrator here if it wasn't already run in real-time,
    # or run heavier models that were skipped in the proxy for latency reasons.
    # For demonstration, we simply process the risk.
    if risk_score > 0.5:
        # Send a webhook to a monitoring system
        logger.warning(f"🚨 TREND ALERT: High Risk Conversation Found (Score {risk_score})")
        logger.warning(f"   Prompt: {user_prompt[:50]}...")
        # e.g., send_slack_alert(entry)

    # Accumulate metrics (in a real app, write to Prometheus/Grafana)
    await asyncio.sleep(0.1)

async def main():
    logger.info("Initializing 24/7 Asynchronous Observer...")
    agent_core = get_agent_core()
    logger.info(f"Tailing logs from: {LOG_FILE}")
    
    # Keep track of metrics for trend analysis
    total_processed = 0
    high_risk_count = 0
    
    async for line in tail_logs(LOG_FILE):
        if not line.strip():
            continue
            
        try:
            entry = json.loads(line)
            await process_log_entry(entry, agent_core)
            
            total_processed += 1
            if entry.get("risk_score", 0) > 0.5:
                high_risk_count += 1
                
            # Log trends every 5 logs
            if total_processed % 5 == 0:
                logger.info(f"📊 TRENDS UPDATE: Processed {total_processed} logs. High Risk: {high_risk_count} ({high_risk_count/total_processed*100:.1f}%)")
                
        except json.JSONDecodeError:
            logger.error("Failed to parse log entry")
        except Exception as e:
            logger.error(f"Observer error: {e}")

if __name__ == "__main__":
    print("="*80)
    print(" MYELIN SENTINEL 24/7 OBSERVER ".center(80, "="))
    print("="*80)
    print("This worker tails secondary channels to ensure AI safety across scale.")
    print("Press Ctrl+C to stop.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nObserver stopped gracefully.")
