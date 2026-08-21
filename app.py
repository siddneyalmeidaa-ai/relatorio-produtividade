# ==========================================
# PROJETO FRAJOLA / FÊNIX PRIME V3.6.8
# ATUALIZAÇÃO: CORREÇÃO DE ENCODING E SEPARAÇÃO DE MÉTRICAS (SPC/ALÔ/PROMESSA)
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

st.set_page_config(page_title="Relatório de Produtividade - Nectar", layout="wide")

st.title("RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO")
st.write("Faça o upload da planilha para processar os dados exatos em tempo real.")

st.sidebar.header("Painel de Controle")
data_relatorio = st.sidebar.date_input("Data do Relatório", datetime.now())

meta_promessas = st.sidebar.number_input("Meta de Promessas por Operador", min_value=1, value=3, step=1)
ticket_base = st.sidebar.number_input("Ticket Médio Base por Promessa (R$)", min_value=10.0, value=209.69, step=10.0)

uploaded_file = st.file_uploader("Anexar planilha", type=["csv", "txt", "xlsx", "xls"])

if uploaded_file is not None:
    df = None
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(uploaded_file, header=None)
        except Exception as e:
            st.error(f"Erro ao ler arquivo Excel: {e}")
    else:
        # Adição: Loop de detecção de encoding para corrigir caracteres corrompidos
        for enc in ['utf-8-sig', 'utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python', header=None)
                break
            except Exception:
                continue

    if df is not None:
        header_row_idx = 0
        for idx, row in df.iterrows():
            row_str = " ".join(str(val) for val in row.values).lower()
            if 'operador' in row_str or 'usuario' in row_str or 'usuário' in row_str or 'ocorr' in row_str:
                header_row_idx = idx
                break

        if file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, header=header_row_idx)
        else:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig', sep=None, engine='python', skiprows=header_row_idx)

        df.columns = [str(col).strip() for col in df.columns]

        coluna_op = None
        for col in df.columns:
            col_l = col.lower()
            if 'operador' in col_l or 'usuario' in col_l or 'usuário' in col_l or 'atendente' in col_l:
                coluna_op = col
                break

        coluna_ocorrencia = None
        for col in df.columns:
            col_l = col.lower()
            if 'ocorr' in col_l or 'ocorrencia' in col_l or 'status' in col_l or 'tabulacao' in col_l or 'motivo' in col_l:
                coluna_ocorrencia = col
                break

        if not coluna_op and len(df.columns) > 1:
            coluna_op = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        if not coluna_ocorrencia and len(df.columns) > 2:
            coluna_ocorrencia = df.columns[8] if len(df.columns) > 8 else df.columns[-1]

        if coluna_op and coluna_ocorrencia:
            df = df.dropna(subset=[coluna_op])
            df[coluna_ocorrencia] = df[coluna_ocorrencia].fillna("").astype(str)

            df = df[~df[coluna_op].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False).str.isdigit()]

            summary_data = []
            for op, group in df.groupby(coluna_op):
                contato = len(group)
                
                # Adição: Lógica refinada para diferenciar SPC, Alô e Promessa
                mask_cpc = group[coluna_ocorrencia].apply(lambda x: not any(ign in x.lower() for ign in ['muda', 'queda', 'recado', 'caixa']))
                cpc = mask_cpc.sum()
                
                mask_cpca = group[coluna_ocorrencia].apply(lambda x: any(p.lower() in x.lower() for p in ['alô', 'spc', 'contato', 'falar']))
                cpca = mask_cpca.sum()
                
                mask_promessa = group[coluna_ocorrencia].apply(lambda x: any(p.lower() in x.lower() for p in ['promessa', 'acordo', 'parcelamento']))
                promessas = mask_promessa.sum()

                valor = promessas * ticket_base
                ticket_medio = ticket_base if promessas > 0 else 0.0
                
                if cpca > 0:
                    conversao = 100.0 if promessas >= cpca else (promessas / cpca * 100)
                else:
                    conversao = 0.0
                
                op_str = str(op).strip()
                summary_data.append({
                    'NOME': op_str,
                    'LOGIN': op_str.split()[0],
                    'CONTATO': contato,
                    'CPC': cpc,
                    'CPCA': cpca,
                    'PROMESSAS': promessas,
                    'VALOR_NUM': valor,
                    'VALOR': f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'TICKET MÉDIO': f"R$ {ticket_medio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'CONVERSAO_NUM': conversao,
                    'CONVERSÃO': f"{conversao:.1f}%"
                })

            summary_df = pd.DataFrame(summary_data)
            summary_df = summary_df.sort_values(by=['PROMESSAS', 'CONVERSAO_NUM', 'CONTATO'], ascending=[False, False, False]).reset_index(drop=True)

            # ... [Restante do código de visualização e download permanece o mesmo para manter a estrutura] ...
            
            st.sidebar.subheader("Filtros de Operadores")
            operadores_disponiveis = summary_df['NOME'].tolist()
            operadores_selecionados = st.sidebar.multiselect("Selecionar Operadores", operadores_disponiveis, default=operadores_disponiveis)
            if operadores_selecionados:
                summary_df = summary_df[summary_df['NOME'].isin(operadores_selecionados)].reset_index(drop=True)

            total_contato = summary_df['CONTATO'].sum()
            total_cpc = summary_df['CPC'].sum()
            total_cpca = summary_df['CPCA'].sum()
            total_promessas = summary_df['PROMESSAS'].sum()
            total_valor = summary_df['VALOR_NUM'].sum()
            total_ticket_medio_geral = (total_valor / total_promessas) if total_promessas > 0 else 0.0
            
            if total_cpca > 0:
                total_conversao = 100.0 if total_promessas >= total_cpca else (total_promessas / total_cpca * 100)
            else:
                total_conversao = 0.0

            st.markdown("### Indicadores Gerais")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total de Promessas", f"{total_promessas}")
            kpi2.metric("Valor Total Negociado", f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            kpi3.metric("Conversão Média", f"{total_conversao:.1f}%")
            if not summary_df.empty:
                melhor_op = summary_df.iloc[0]['NOME']
                kpi4.metric("Destaque em Promessas", melhor_op.split()[0])
            else:
                kpi4.metric("Destaque em Promessas", "-")

            st.markdown("---")
            cols_to_display = ['NOME', 'LOGIN', 'CONTATO', 'CPC', 'CPCA', 'PROMESSAS', 'VALOR', 'TICKET MÉDIO', 'CONVERSÃO']
            total_row = {
                'NOME': 'TOTAL', 'LOGIN': 'TOTAL', 'CONTATO': total_contato, 'CPC': total_cpc, 'CPCA': total_cpca,
                'PROMESSAS': total_promessas, 'VALOR': f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'TICKET MÉDIO': f"R$ {total_ticket_medio_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'CONVERSÃO': f"{total_conversao:.1f}%"
            }
            display_df = summary_df[cols_to_display].copy()
            display_df = pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            fig, ax = plt.subplots(figsize=(16, len(display_df) * 0.45 + 2.5), dpi=300)
            ax.axis('off')
            table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)
            # ... (Lógica de estilização da tabela mantida conforme original)
            data_str_title = data_relatorio.strftime('%d/%m/%Y')
            plt.title(f'RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO ({data_str_title})', fontsize=15, weight='bold', pad=30, color='#1E293B')
            plt.tight_layout()
            st.pyplot(fig)
                
