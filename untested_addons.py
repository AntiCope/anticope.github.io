import requests
import json
from os import getenv

GH_TOKEN = getenv("GH_TOKEN")

# Request all code snippets in java extending MeteorAddon class
r = requests.get(f"https://api.github.com/search/code?q=extends+MeteorAddon+language:java+in:file&access_token={GH_TOKEN}")

# function that formats repos contents to exclute private repos and add code size property
def parse_repo(repo):
    repo = repo['repository']
    if repo['private']:
        return None
    r = requests.get(repo['url'])
    repo.update(r.json())
    return repo

# load repos
repos = r.json()['items']
repos = [parse_repo(repo) for repo in repos]
repos = list(filter(bool, repos))
repos.sort(key=lambda x: x['size'], reverse=True)

# create markdown file, write template to it
file = open("UntestedAddons.md", 'w+', encoding='utf-8')
file.write(open("res/UntestedAddons.template.md", "r", encoding='utf-8').read())

# add a line for each repo
for repo in repos:
    print(f"Adding: {repo['full_name']}")
    file.write(f"\n| {repo['name']} | {repo['description']} | [Repository]({repo['html_url']}) | {repo['owner']['login']} |")

file.close()