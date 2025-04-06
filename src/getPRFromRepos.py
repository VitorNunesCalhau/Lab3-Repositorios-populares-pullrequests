import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import time
import re

GITHUB_TOKEN = ''
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

def get_top_repositories(n=1):
    repos = []
    page = 1
    while len(repos) < n:
        url = f'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS).json()
        repos.extend(response.get('items', []))
        page += 1
    return repos[:n]

def has_enough_prs(repo_full_name):
    url = f"https://api.github.com/search/issues?q=repo:{repo_full_name}+is:pr"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return False
    total_prs = response.json().get('total_count', 0)
    print(f"{repo_full_name}: {total_prs} PRs")
    return total_prs >= 100


def get_valid_prs(repo_full_name, max_prs=300):
    prs_data = []
    page = 1

    skipped_by_state = 0
    skipped_by_duration = 0
    skipped_by_review = 0

    while len(prs_data) < max_prs:
        url = f'https://api.github.com/repos/{repo_full_name}/pulls?state=all&per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS).json()

        if not response or (isinstance(response, dict) and response.get('message')):
            print(f" Erro ou resposta inválida - página {page}")
            break

        for pr_summary in response:
            pr_number = pr_summary['number']

            pr_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
            pr = requests.get(pr_url, headers=HEADERS).json()
            if isinstance(pr, dict) and pr.get('message'):
                print(f"⛔ PR #{pr_number} ignorado: erro ao buscar detalhes")
                continue

            if pr['state'] == 'open':
                skipped_by_state += 1
                print(f"⛔ PR #{pr_number} descartado: ainda está aberto")
                continue

            if pr.get('merged_at') is None and pr['state'] != 'closed':
                skipped_by_state += 1
                print(f"⛔ PR #{pr_number} descartado: não está merged nem fechado")
                continue

            created = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00"))
            closed_or_merged_at = pr['merged_at'] or pr['closed_at']
            if not closed_or_merged_at:
                skipped_by_state += 1
                print(f"⛔ PR #{pr_number} descartado: sem data de merge/close")
                continue

            closed = datetime.fromisoformat(closed_or_merged_at.replace("Z", "+00:00"))
            duration = (closed - created).total_seconds() / 3600
            if duration < 0.17:
                skipped_by_duration += 1
                print(f"⛔ PR #{pr_number} descartado: duração {duration:.2f}h < 10min")
                continue

            reviews_url = pr['_links']['self']['href'] + '/reviews'
            reviews = requests.get(reviews_url, headers=HEADERS).json()
            if isinstance(reviews, dict) or len(reviews) == 0:
                skipped_by_review += 1
                print(f"⛔ PR #{pr_number} descartado: sem reviews humanos")
                continue

            participants = len(set([rev['user']['login'] for rev in reviews if rev.get('user')]))

            print(f"✅ PR #{pr_number} incluído")
            prs_data.append({
                'repo': repo_full_name,
                'number': pr_number,
                'state': pr['state'],
                'merged': pr.get('merged_at') is not None,
                'created_at': pr['created_at'],
                'closed_or_merged_at': closed_or_merged_at,
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0),
                'changed_files': pr.get('changed_files', 0),
                'description_length': len(pr['body']) if pr.get('body') else 0,
                'comments': pr.get('comments', 0),
                'review_comments': pr.get('review_comments', 0),
                'participants': participants
            })

            time.sleep(0.1)

        page += 1

    print(f"[{repo_full_name}] Coletados: {len(prs_data)} | Pulados: estado={skipped_by_state}, duração<10min={skipped_by_duration}, sem review={skipped_by_review}")
    return prs_data


def save_dataset(data, filename='prs_dataset.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)


def main():
    top_repos = get_top_repositories(1) 
    selected_repos = []

    for repo in tqdm(top_repos):
        if has_enough_prs(repo['full_name']):
            selected_repos.append(repo['full_name'])
        time.sleep(0.2)

    all_prs = []
    for repo_full_name in tqdm(selected_repos[:3]): 
        prs = get_valid_prs(repo_full_name)
        all_prs.extend(prs)

    save_dataset(all_prs)

if __name__ == '__main__':
    main()
