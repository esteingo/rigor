import asyncio
import aiohttp

from . import SuiteResult, Runner
from . import get_logger


def execute(suite, profile):
    log = get_logger()
    log.debug("execute suite start", suite=suite, profile=profile)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(do_suite(loop, suite, profile))
    loop.run_until_complete(future)

    result = SuiteResult.create(suite, profile, future.result())
    log.info("execute suite complete", passed=len(result.passed),
             failed=len(result.failed))

    return result


async def do_suite(loop, suite, profile):
    tasks = []
    connector = aiohttp.TCPConnector(limit_per_host=suite.concurrency)

    with aiohttp.ClientSession(loop=loop, connector=connector) as session:
        for case in suite.queued.values():
            for scenario in case.scenarios:
                runner = Runner(session=session, suite=suite, profile=profile,
                                case=case, scenario=scenario)

                tasks.append(asyncio.ensure_future(runner.do_run()))

        results = await asyncio.gather(*tasks, return_exceptions=False)

    return results
