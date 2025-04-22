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

def correlation_with_status(df, metric):
    df['Status_numeric'] = df['Status'].map({'MERGED': 1, 'CLOSED': 0})
    corr, p = spearmanr(df[metric], df['Status_numeric'])
    print(f"📊 Correlação entre '{metric}' e Status: r={corr:.3f}, p={p:.3f}")
    sns.scatterplot(x=df[metric], y=df['Status_numeric'])
    plt.title(f"Correlação entre {metric} e Status\nr={corr:.3f}, p={p:.3f}")
    plt.xlabel(metric)
    plt.ylabel('Status (MERGED=1, CLOSED=0)')
    plt.tight_layout()
    plt.show()


def correlation_with_reviews(df, metric):
    review_col = get_review_column(df)
    corr, p = spearmanr(review_col, df[metric])
    print(f"🔎 Correlação entre '{metric}' e número de revisões: r={corr:.3f}, p={p:.3f}")
    sns.scatterplot(x=df[metric], y=review_col)
    plt.title(f"Correlação entre {metric} e Número de Revisões\nr={corr:.3f}, p={p:.3f}")
    plt.xlabel(metric)
    plt.ylabel('Número de Revisões')
    plt.tight_layout()
    plt.show()

metrics = [
    'Files Changed',      
    'Additions',          
    'Deletions',          
    'Analysis Time (hours)',  
    'Description Length',     
    'Participants',           
    'Comments'              
]

print("\n📈 Correlações com STATUS (feedback final):")
for metric in metrics:
    correlation_with_status(df, metric)

print("\n📈 Correlações com NÚMERO DE REVISÕES:")
for metric in metrics:
    correlation_with_reviews(df, metric)
