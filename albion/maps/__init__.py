import os
import asyncio
import json
import networkx as nx
from datetime import datetime, timedelta, timezone
from albion.maps.exceptions import MapNotFound, NoRoute

roa_portal_closing_time: dict[str, datetime] = {}
graph = nx.Graph()
maps: dict[str, str]
map_connection: dict[str, list[str]]
this_dir = os.path.dirname(os.path.abspath(__file__))

try:
    with open(os.path.join(this_dir, "maps.json"), "r", encoding="utf-8") as f:
        maps = json.load(f)
    with open(
        os.path.join(this_dir, "map_connection.json"), "r", encoding="utf-8"
    ) as f:
        map_connection = json.load(f)
except Exception as e:
    print(f"error while opening map_connection or map json file: {e}")

try:
    for map_id in maps.keys():
        if map_id in map_connection:
            for map_dst_id in map_connection[map_id]:
                if not graph.has_edge(map_id, map_dst_id):
                    graph.add_edge(map_id, map_dst_id)
except Exception as e:
    print(f"error while adding edge from world map into graph : {e}")


def add_roa_portal(
    map_id_a: str,
    map_id_b: str,
    duration: str,
) -> datetime:
    if graph.has_edge(map_id_a, map_id_b):
        return get_roa_portal_closing_datetime(map_id_a, map_id_b)

    graph.add_edge(map_id_a, map_id_b)

    format = ""
    if "h" in duration:
        format += "%Hh"
    if "m" in duration:
        format += "%Mm"
    if "s" in duration:
        format += "%Ss"
    parsed_time = datetime.strptime(duration, format)
    duration_time = timedelta(
        hours=parsed_time.hour, minutes=parsed_time.minute, seconds=parsed_time.second
    )
    closing_datetime = datetime.now(timezone(timedelta(hours=7))) + duration_time
    roa_portal_closing_time[f"{map_id_a}_{map_id_b}"] = closing_datetime

    async def remove_edge_from_graph():
        await asyncio.sleep(duration_time.total_seconds())
        graph.remove_edge(map_id_a, map_id_b)

    asyncio.ensure_future(remove_edge_from_graph())

    return closing_datetime


def get_roa_portal_closing_datetime(map_id_a: str, map_id_b: str) -> datetime | None:
    if f"{map_id_a}_{map_id_b}" in roa_portal_closing_time:
        return roa_portal_closing_time[f"{map_id_a}_{map_id_b}"]
    if f"{map_id_b}_{map_id_a}" in roa_portal_closing_time:
        return roa_portal_closing_time[f"{map_id_b}_{map_id_a}"]

    return None


def get_route(from_map_id: str, to_map_id: str) -> list[str]:
    try:
        map_ids = nx.shortest_path(graph, from_map_id, to_map_id)
        return map_ids
    except nx.NodeNotFound as e:
        missing_map = str(e).split(" ", 1)[1].replace("is not in G", "").strip()
        raise MapNotFound(missing_map)
    except nx.NetworkXNoPath as e:
        raise NoRoute()


def get_maps() -> dict[str, str]:
    return maps


def get_displayname(map_id: str) -> str | None:
    return maps[map_id] if map_id in maps else None


def get_map_id(map_displayname: str) -> str | None:
    for id, displayname in maps.items():
        if displayname == map_displayname:
            return id
    return None
