import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('NECTAR20260810041332_1152_1.csv')

promessa_types = [
    'Promessa A Vista Com Desconto',
    'Promessa A Vista Com Isencao de Juros e Multa',
    'Promessa A Vista Sem Desconto',
    'Parcelamento Com Desconto',
    'Parcelamento Com Desconto e Isencao de Juros e Mul'
]

cpc_types = [
    'Promessa A Vista Com Desconto', 'Promessa A Vista Com Isencao de Juros e Multa',
    'Promessa A Vista Sem Desconto', 'Parcelamento Com Desconto',
    'Parcelamento Com Desconto e Isencao de Juros e Mul', 'Alega Pagamento',
    'Sem Previsao de Pagamento', 'Retorno Agendado Indireto', 'Retorno Agendado Direto',
    'Preventivo - Com Sucesso', 'Dificuldades Financeiras', 'Cliente Pagara Outra Proposta'
]

summary_data = []
for op, group in df.groupby('Operador'):
    contato = len(group)
    cpc = group['Ocorrência'].isin(cpc_types).sum()
    cpca = group['Ocorrência'].isin(promessa_types + ['Alega Pagamento', 'Preventivo - Com Sucesso']).sum()
    promessas = group['Ocorrência'].isin(promessa_types).sum()
    
    valor = promessas * 209.69 if promessas > 0 else 0.0
    ticket_medio = 209.69 if promessas > 0 else 0.0
    conversao = (promessas / contato * 100) if contato > 0 else 0.0
    
    summary_data.append({
        'NOME': op,
        'LOGIN': op.split()[0],
        'CONTATO': contato,
        'CPC': cpc,
        'CPCA': cpca,
        'PROMESSAS': promessas,
        'VALOR': f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'TICKET MÉDIO': f"R$ {ticket_medio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'CONVERSÃO': f"{conversao:.1f}%"
    })

summary_df = pd.DataFrame(summary_data)
summary_df = summary_df.sort_values(by='CONTATO', ascending=False).reset_index(drop=True)

total_contato = summary_df['CONTATO'].sum()
total_cpc = summary_df['CPC'].sum()
total_cpca = summary_df['CPCA'].sum()
total_promessas = summary_df['PROMESSAS'].sum()
total_valor = total_promessas * 209.69
total_conversao = (total_promessas / total_contato * 100) if total_contato > 0 else 0.0

total_row = {
    'NOME': 'TOTAL',
    'LOGIN': 'TOTAL',
    'CONTATO': total_contato,
    'CPC': total_cpc,
    'CPCA': total_cpca,
    'PROMESSAS': total_promessas,
    'VALOR': f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
    'TICKET MÉDIO': f"R$ 209,69",
    'CONVERSÃO': f"{total_conversao:.1f}%"
}

summary_df = pd.concat([summary_df, pd.DataFrame([total_row])], ignore_index=True)

fig, ax = plt.subplots(figsize=(16, len(summary_df) * 0.45 + 2), dpi=300)
ax.axis('off')

table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.6)

col_widths = [0.28, 0.10, 0.08, 0.08, 0.08, 0.09, 0.11, 0.11, 0.09]
for i, width in enumerate(col_widths):
    for row in range(len(summary_df) + 1):
        table[(row, i)].set_width(width)

for k, cell in table.get_celld().items():
    cell.set_edgecolor('#CCCCCC')
    if k[0] == 0:
        cell.set_facecolor('#3B1443')
        cell.set_text_props(color='white', weight='bold', fontsize=10)
    elif k[0] == len(summary_df):
        cell.set_facecolor('#EAEAEA')
        cell.set_text_props(color='#111111', weight='bold', fontsize=9.5)
    else:
        cell.set_facecolor('#F7F9FA' if k[0] % 2 == 0 else '#FFFFFF')
        cell.set_text_props(color='#333333', fontsize=9)

plt.title('RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO', fontsize=14, weight='bold', pad=25, color='#222222')
plt.tight_layout()
plt.savefig('tabela_produtividade_final.png', bbox_inches='tight')
plt.close()
