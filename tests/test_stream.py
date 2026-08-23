import asyncio

import pytest

from app.data.brsapi.stream import RealtimeHub


@pytest.mark.asyncio
async def test_hub_fanout_and_bounded_queue():
    hub = RealtimeHub(max_queue=1)
    q1 = await hub.subscribe()
    q2 = await hub.subscribe()

    hub.publish({"sequence": 1})
    await asyncio.sleep(0)
    assert await q1.get() == {"sequence": 1}
    assert await q2.get() == {"sequence": 1}

    hub.publish({"sequence": 2})
    hub.publish({"sequence": 3})
    await asyncio.sleep(0)
    assert await q1.get() == {"sequence": 3}
    assert await q2.get() == {"sequence": 3}

    await hub.unsubscribe(q1)
    await hub.unsubscribe(q2)
    assert hub.subscriber_count == 0
