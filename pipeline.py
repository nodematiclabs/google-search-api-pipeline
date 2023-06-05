from typing import List

import kfp
import kfp.dsl as dsl

from kfp import compiler

@dsl.component(
    base_image='python:3.11',
    packages_to_install=['google-api-python-client', 'appengine-python-standard']
)
def get_search_results(name: str) -> str:
    import json
    import re
    import requests

    from googleapiclient.discovery import build

    GOOGLE_API_KEY = ""
    GITHUB_TOKEN = ""

    service = build(
        "customsearch", "v1", developerKey=GOOGLE_API_KEY
    )

    res = (
        service.cse()
        .list(
            q=name,
            cx="",
        )
        .execute()
    )
    organization = None
    repository = None
    i = 1
    for item in res["items"]:
        print("Search Result: ", i)
        matches = re.search(r'https://github.com/([^/]+?)/([^/]+?)$', item["link"])
        if matches:
            organization = matches.group(1)
            repository = matches.group(2)
            break
        i += 1
    
    if organization is not None and repository is not None:
        url = f"https://api.github.com/repos/{organization}/{repository}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return json.dumps({
                "stars": response.json()["stargazers_count"],
                "last_update": response.json()["updated_at"]
            })
        else:
            return ""
    else:
        return ""

@dsl.pipeline(
    name="github-activity-check"
)
def github_activity_check(libraries: List[str]):
    with dsl.ParallelFor(
        name="github-activity-check",
        items=libraries,
        parallelism=3
    ) as library:
        get_search_results(name=library)

compiler.Compiler().compile(github_activity_check, "pipeline.yaml")