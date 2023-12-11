import requests
import json
from os import getenv
from time import sleep
import re
from configparser import ConfigParser


VERIFIED = json.load(open('verified.json', "r+", encoding='utf-8'))
INJECT = json.load(open('inject.json', "r+", encoding='utf-8'))

RETRY_COUNT = 25

GH_TOKEN = getenv("GH_TOKEN")
HEADERS = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "AntiCope/anticope.ml"}

# regex
FEATURE_RE = re.compile("(?:add\(new )([^(]+)(?:\([^)]*)\)\)")
INVITE_RE = re.compile("((?:https?:\/\/)?(?:www.)?(?:discord.(?:gg|io|me|li|com)|discordapp.com\/invite|dsc.gg)\/[a-zA-z0-9-\/]+)")
MCVER_RE = re.compile("(?:['\"]com\.mojang:minecraft:)([0-9a-z.]+)(?:[\"'])")

def sleep_if_rate_limited(type="search"):
    for _ in range(RETRY_COUNT):
        try:
            r = requests.get("https://api.github.com/rate_limit", headers=HEADERS)
            if r.status_code != 304 and r.json()['resources'][type]['remaining'] > 0:
                return
            print("rate limited. sleeping...")
        except Exception:
            print("[rate limit] error. ignoring...")
        sleep(25)

repos = set(VERIFIED)

# Fetch all repo names that contain meteor entrypoint in fabric.mod.json
incomplete = True
page = 0
print("Fetching based on fabric.mod.json")
while incomplete:
    print(f"Fetching page {page}")
    for _ in range(RETRY_COUNT):
        try:
            sleep_if_rate_limited()
            r = requests.get(
                f"https://api.github.com/search/code?q=entrypoints+meteor+extension:json+filename:fabric.mod.json+fork:true+in:file&per_page=100&page={page}", headers=HEADERS).json()
            if 'message' in r.keys() and "rate limit" in r['message']:
                print("[search fetch] rate limited. sleeping...")
                sleep(60)
                continue
            for file in r['items']:
                repo = file['repository']
                if not repo['private']:
                    repos.add(repo['full_name'])
            incomplete = r["incomplete_results"]
            break
        except Exception:
            print("[search fetch] error. ignoring...")
    page += 1
    if page > 10: # fallback
        break
    
# Fetch all repo names that extend MeteorAddon
incomplete = True
page = 0
print("Fetching based on extends MeteorAddon")
while incomplete:
    print(f"Fetching page {page}")
    for _ in range(RETRY_COUNT):
        try:
            sleep_if_rate_limited()
            r = requests.get(
                f"https://api.github.com/search/code?q=extends+MeteorAddon+language:java+in:file&per_page=100&page={page}", headers=HEADERS).json()
            if 'message' in r.keys() and "rate limit" in r['message']:
                print("[search fetch] rate limited. sleeping...")
                sleep(60)
                continue
            for file in r['items']:
                repo = file['repository']
                if not repo['private']:
                    repos.add(repo['full_name'])
            incomplete = r["incomplete_results"]
            break
        except Exception:
            print("[search fetch] error. ignoring...")
    page += 1
    if page > 10: # fallback
        break

# Request all forks of templates because some people cant click generate
r = requests.get("https://api.github.com/repos/MeteorDevelopment/meteor-addon-template/forks?per_page=100", headers=HEADERS).json()
for fork in r:
    try:
        repos.add(fork['full_name'])
    except Exception:
        print("[fork fetch] error. ignoring...")
        
# filter templates
repos = list(filter(lambda x: "-addon-template" not in x.lower(), repos))

def parse_repo(name):
    sleep_if_rate_limited(type="core")
    print(f"parsing: {name}")

    repo = requests.get(f"https://api.github.com/repos/{name}", headers=HEADERS).json()
    fabric = requests.get(f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/src/main/resources/fabric.mod.json").json()

    # find authors from mod metadata or from github username
    authors = []
    for author in fabric['authors']:
        if type(author) == str:
            authors.append(author)
    if len(authors) == 0:
        authors.append(repo['owner']['login'])
    
    links = {"github": repo['html_url']}

    if "meteor" not in fabric["entrypoints"].keys():
        print("Missing meteor entrypoint")
        raise Exception("Missing meteor entrypoint")
    
    summary = ""
    try:
        summary = repo['description'] or fabric['description']
    except Exception:
        print("[summary] error. ignoring...")
    
    # direct download from releases
    downloads = 0
    try:
        releases = requests.get(f"https://api.github.com/repos/{name}/releases", headers=HEADERS).json()
        url = None
        for release in releases:
            for asset in release['assets']:
                asset_name: str = asset['name'].lower()
                if asset_name.endswith("-dev.jar") or asset_name.endswith("-sources.jar"):
                    continue
                if asset_name.endswith(".jar"):
                    url = asset['browser_download_url']
                    downloads = asset['download_count']
                    break
            if url != None:
                break
        if url == None:
            print("missing release")
        else:
            links["download"] = url
    except Exception:
        print("[dl] error. ignoring...")
    
    # icon from mod metadata
    icon = None
    try:
        icon = f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/src/main/resources/{fabric['icon']}"
        if requests.head(icon).status_code == 404:
            print("missing icon")
            icon = None
    except Exception:
        print("[icon] error. ignoring...")

    # find discord server by looking at readme mod and repository metadata
    try:
        readme = requests.get(f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/README.md").text
        invites = INVITE_RE.findall(readme) + INVITE_RE.findall(str(fabric)) + INVITE_RE.findall(str(repo))
        for invite in invites:
            if requests.head(invite).status_code != 404:
                links["discord"] = invite
                break
    except Exception:
        print("[discord invite] error. ignoring...")

    try:
        site = repo['homepage']
        if not INVITE_RE.match(site) and site: # skip discord invites
            links["homepage"] = site
    except Exception:
        print("[homepage] error. ignoring...")

    # find features by parsing the entrypoint
    features = []
    feature_count = 0
    try:
        entrypoint = requests.get(f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/src/main/java/{fabric['entrypoints']['meteor'][0].replace('.', '/')}.java").text
        features.extend([str(x) for x in FEATURE_RE.findall(entrypoint)])
        feature_count = len(features)
        if len(features) > 50:
            count = len(features) - 50
            features = features[:50]
            features.append(f"...and {count} more")
    except Exception:
        print("[features] error. ignoring...")
        
    # parse build.gradle
    mc_version = None
    try:
        build_gradle = requests.get(f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/build.gradle").text
        try:
            props = requests.get(f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/gradle.properties").text
            props = "[conf]\n"+props # convert to ini format
            gradle_props = ConfigParser()
            gradle_props.read_string(props)
            for key, val in dict(gradle_props['conf']).items():
                build_gradle = build_gradle.replace("${project."+key+"}", val)
                build_gradle = build_gradle.replace(f"$project.{key}", val)
                build_gradle = build_gradle.replace(f"project.{key}", val)
        except Exception as ex:
            print(f"[build.gradle] failed to read gradle.properties.")  
        mc_version = MCVER_RE.findall(build_gradle)[0]
    except Exception:
        print("[build.gradle] error. ignoring...")  
    
    result = {
        "authors": authors,
        "features": features,
        "feature_count": feature_count,
        "icon": icon,
        "id": repo['full_name'],
        "links": links,
        "name": fabric['name'],
        "stars": repo['stargazers_count'],
        "last_update": repo['pushed_at'],
        "downloads": downloads,
        "mc_version": mc_version,
        "status": {
            "archived": repo['archived']
        },
        "verified": (repo['full_name'] in VERIFIED),
        "summary": summary
    }

    result.update(INJECT.get(repo['full_name'], {}))
    return result
    
verified_json = []
unverified_json = []
for repo in repos:
    if repo in VERIFIED:
        try:
            verified_json.append(parse_repo(repo))
        except Exception as ex:
            print(f"error {ex}. ignoring..., repo: {repo}")
    else:
        try:
            unverified_json.append(parse_repo(repo))
        except Exception as ex:
            print(f"error {ex}. ignoring..., repo: {repo}")
            
json.dump(verified_json, open("addons-ver.json", "w+", encoding='utf-8'), indent=None)
json.dump(unverified_json, open("addons-unver.json", "w+", encoding='utf-8'), indent=None)
