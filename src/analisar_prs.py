import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns

csv_path = 'prs_dataset.csv'
df = pd.read_csv(csv_path)

def get_review_column(df):
    if 'review_comments' in df.columns:
        return df['review_comments']
    elif 'Comments' in df.columns:
        print("⚠️ Usando 'Comments' como proxy de 'review_comments'.")
        return df['Comments']
    else:
        raise ValueError("Nenhuma coluna de revisão encontrada.")

metrics = [
    'Files Changed', 'Additions', 'Deletions',
    'Analysis Time (hours)', 'Description Length',
    'Participants', 'Comments'
]

if 'Status_numeric' not in df.columns:
    df['Status_numeric'] = df['Status'].map({'MERGED': 1, 'CLOSED': 0})

review_col = get_review_column(df)

fig, axs = plt.subplots(nrows=len(metrics), ncols=2, figsize=(20, 4 * len(metrics)))
axs = axs.reshape(len(metrics), 2)

fig.subplots_adjust(hspace=0.4, top=0.95)
fig.suptitle("Correlação das Métricas com Status e Número de Revisões", fontsize=20)

for i, metric in enumerate(metrics):
    corr_status, p_status = spearmanr(df[metric], df['Status_numeric'])
    sns.scatterplot(x=df[metric], y=df['Status_numeric'], ax=axs[i][0])
    axs[i][0].set_title(f"{metric} vs Status\nr={corr_status:.3f}, p={p_status:.3f}")
    axs[i][0].set_xlabel(metric)
    axs[i][0].set_ylabel("Status (MERGED=1, CLOSED=0)")

    corr_review, p_review = spearmanr(df[metric], review_col)
    sns.scatterplot(x=df[metric], y=review_col, ax=axs[i][1])
    axs[i][1].set_title(f"{metric} vs Revisões\nr={corr_review:.3f}, p={p_review:.3f}")
    axs[i][1].set_xlabel(metric)
    axs[i][1].set_ylabel("Número de Revisões")

plt.tight_layout(rect=[0, 0, 1, 0.96]) 
plt.show()
