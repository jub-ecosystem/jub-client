"""
Tasks examples — JUB API v2.

Background tasks are created automatically when setup_observatory() is called.
An external indexer processes the observatory data and then calls complete_task()
to enable it. This example shows how to monitor and manage those tasks.

Covers: get_task_stats, list_my_tasks, get_task,
        complete_task, retry_task.

Run:
    python examples/v2/cars/tasks/example_tasks.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with the task_id returned by setup_observatory().
TASK_ID = "<your-task-id>"


async def main():
    client = await get_client()

    # --- 1. Task statistics across all statuses -----------------------
    stats_result = await client.get_task_stats()
    print_result("get_task_stats", stats_result)

    # --- 2. List recent tasks for the authenticated user ---------------
    list_result = await client.list_my_tasks(limit=20)
    print_result("list_my_tasks", list_result)

    # --- 3. Fetch details for a specific task --------------------------
    get_result = await client.get_task(TASK_ID)
    print_result("get_task", get_result)

    # --- 4. Mark a task as successfully completed ---------------------
    # This is called by the indexer once it finishes processing.
    # On success=True the API enables the linked observatory automatically.
    complete_result = await client.complete_task(
        TASK_ID,
        DTO.TaskCompleteDTO(
            success=True,
            message="Indexed 12,540 car production records from Germany.",
        ),
    )
    print_result("complete_task / success=True", complete_result)

    # --- 5. Retry a failed task ----------------------------------------
    # Useful when a transient error caused the first attempt to fail.
    retry_result = await client.retry_task(TASK_ID)
    print_result("retry_task", retry_result)


if __name__ == "__main__":
    asyncio.run(main())
