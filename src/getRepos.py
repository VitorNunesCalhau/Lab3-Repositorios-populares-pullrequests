import requests
import time
import pandas as pd
from tqdm import tqdm
import os


GITHUB_TOKEN = os.getenv("") or ""
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

def get_top_repo_names(n=200):
    repo_names = []
    page = 1

    print("Coletando nomes dos repositórios")

    while len(repo_names) < n:
        url = f'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            break

        items = response.json().get('items', [])
        if not items:
            break

        for repo in items:
            repo_names.append(repo['full_name'])
            if len(repo_names) >= n:
                break

        page += 1
        time.sleep(1)

    return repo_names

def get_pr_count(repo_full_name):
    url = f"https://api.github.com/search/issues?q=repo:{repo_full_name}+is:pr"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json().get('total_count', None)
    else:
        return None

def save_repos_to_csv(data, filename='repos_dataset.csv'):
    df = pd.DataFrame(data, columns=['repository', 'pull_requests'])
    df.to_csv(filename, index=False)
    print(f"Dados salvos")

# ========== EXECUÇÃO ==========

if __name__ == '__main__':
    repos = get_top_repo_names(200)
    data = []

    for repo in tqdm(repos):
        pr_count = get_pr_count(repo)
        if pr_count is None:
            pr_count = "sem informações"
        data.append((repo, pr_count))
        time.sleep(0.5)  # para evitar rate limit

    save_repos_to_csv(data, 'repos_dataset.csv')
