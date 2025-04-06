import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
import re




# Token: 
GITHUB_TOKEN = ''
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

# ========== FUNÇÕES ==========

def get_top_repositories(n=200):
    repos = []
    page = 1
    print("🔍 Buscando repositórios populares...")
    while len(repos) < n:
        url = f'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS).json()
        repos.extend(response.get('items', []))
        page += 1
    return repos[:n]

def has_enough_prs(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=all&per_page=1"
    response = requests.get(url, headers=HEADERS)

    if 'Link' in response.headers:
        links = response.headers['Link'].split(',')
        for link in links:
            if 'rel="last"' in link:
                match = re.search(r'page=(\d+)', link)
                if match:
                    last_page = int(match.group(1))
                    return last_page * 1 >= 100  # porque per_page=1
    return False

def get_valid_prs(repo_full_name, max_prs=300):
    prs_data = []
    page = 1
    print(f"📥 Coletando PRs de {repo_full_name}...")

    while len(prs_data) < max_prs:
        url = f'https://api.github.com/repos/{repo_full_name}/pulls?state=all&per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS).json()

        if not response or isinstance(response, dict) and response.get('message'):
            break

        for pr in response:
            if pr['state'] == 'open':
                continue
            if pr.get('merged_at') is None and pr['state'] != 'closed':
                continue

            created = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00"))
            closed_or_merged_at = pr['merged_at'] or pr['closed_at']
            if not closed_or_merged_at:
                continue

            closed = datetime.fromisoformat(closed_or_merged_at.replace("Z", "+00:00"))
            duration = (closed - created).total_seconds() / 3600
            if duration < 1:
                continue

            reviews_url = pr['_links']['review_comments']['href'].replace('/comments', '')
            reviews = requests.get(reviews_url, headers=HEADERS).json()
            if isinstance(reviews, dict) or len(reviews) == 0:
                continue

            participants = len(set([rev['user']['login'] for rev in reviews if rev.get('user')]))
            prs_data.append({
                'repo': repo_full_name,
                'number': pr['number'],
                'state': pr['state'],
                'merged': pr.get('merged_at') is not None,
                'created_at': pr['created_at'],
                'closed_or_merged_at': closed_or_merged_at,
                'additions': pr['additions'],
                'deletions': pr['deletions'],
                'changed_files': pr['changed_files'],
                'description_length': len(pr['body']) if pr['body'] else 0,
                'comments': pr['comments'],
                'review_comments': pr['review_comments'],
                'participants': participants
            })
            time.sleep(0.1)

        page += 1

    return prs_data

def save_dataset(data, filename='prs_dataset.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Dataset salvo em: {filename}")

# ========== EXECUÇÃO ==========

def main():
    top_repos = get_top_repositories(200)
    selected_repos = []

    print("📊 Filtrando repositórios com ≥ 100 PRs...")
    for repo in tqdm(top_repos):
        if has_enough_prs(repo['full_name']):
            selected_repos.append(repo['full_name'])
        time.sleep(0.2)  # evitar bloqueio

    all_prs = []
    print("🚀 Iniciando coleta de PRs válidos...")
    for repo_full_name in tqdm(selected_repos[:5]):  # limite inicial de 10 para testes
        prs = get_valid_prs(repo_full_name)
        all_prs.extend(prs)

    save_dataset(all_prs)

if __name__ == '__main__':
    main()