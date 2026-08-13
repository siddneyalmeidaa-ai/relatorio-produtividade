import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Relatório de Produtividade", layout="wide")

st.title("RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO")
st.write("Faça o upload do arquivo CSV gerado pelo sistema para processar os dados em tempo real.")

uploaded_file = st.file_uploader("Anexar planilha CSV", type=["csv"])

if uploaded_file is not None:
    df = None
    for enc in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=None, engine='python', header=None, encoding=enc)
            break
        except Exception:
            continue

    if df is not None:
        header_row_idx = None
        for idx, row in df.iterrows():
            row_str = " ".join(str(val) for val in row.values).lower()
            if 'operador' in row_str:
                header_row_idx = idx
                break

        if header_row_idx is not None:
            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
        else:
            df.columns = df.iloc[0]
            df = df.iloc[1:].reset_index(drop=True)

        df.columns = [str(col).strip() for col in df.columns]

        coluna_op = None
        for col in df.columns:
            if 'operador' in col.lower():
                coluna_op = col
                break

        coluna_ocorrencia = None
        for col in df.columns:
            if 'ocorr' in col.lower() or 'ocorrencia' in col.lower():
                coluna_ocorrencia = col
                break

        if coluna_op and coluna_ocorrencia:
            df = df.dropna(subset=[coluna_op, coluna_ocorrencia])
            
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
            for op, group in df.groupby(coluna_op):
                contato = len(group)
                cpc = group[coluna_ocorrencia].astype(str).isin(cpc_types).sum()
                cpca = group[coluna_ocorrencia].astype(str).isin(promessa_types + ['Alega Pagamento', 'Preventivo - Com Sucesso']).sum()
                promessas = group[coluna_ocorrencia].astype(str).isin(promessa_types).sum()
                
                valor = promessas * 209.69 if promessas > 0 else 0.0
                ticket_medio = 209.69 if promessas > 0 else 0.0
                conversao = (promessas / contato * 100) if contato > 0 else 0.0
                
                op_str = str(op)
                summary_data.append({
                    'NOME': op_str,
                    'LOGIN': op_str.split()[0],
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

            st.subheader("Visualização dos Dados Consolidados")
            st.dataframe(summary_df, use_container_width=True)

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
            
            st.pyplot(fig)
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            
            st.download_button(
                label="Baixar Relatório em Imagem (PNG)",
                data=buf,
                file_name="tabela_produtividade_final.png",
                mime="image/png"
            )
        else:
            st.error(f"Cabeçalho real não identificado. Linhas iniciais encontradas no arquivo.")
            st.write(df.head(10))
    else:
        st.error("Erro ao ler o arquivo CSV.")
else:
    st.info("Aguardando o envio do arquivo CSV para iniciar o processamento...")
        
