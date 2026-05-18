import asyncio

from app.queue.worker import enqueue_task, get_task_status, recover_failed_jobs, start_worker


async def main() -> None:
    email_job = await enqueue_task(
        "send_email",
        args={
            "to": "lead@example.com",
            "subject": "Meeting confirmed",
            "body": "Your AI automation meeting is confirmed.",
        },
        user_id="demo-user-001",
    )

    crm_job = await enqueue_task(
        "create_lead",
        args={
            "name": "Akshat Seth",
            "email": "akshat@example.com",
            "lead_status": "NEW",
        },
        user_id="demo-user-001",
    )

    print(email_job)
    print(crm_job)
    print(await get_task_status(email_job["data"]["job_id"]))
    print(await recover_failed_jobs())

    # Usually run this in a separate worker process/container.
    # await start_worker(burst=True)


if __name__ == "__main__":
    asyncio.run(main())
