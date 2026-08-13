import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

st.set_page_config(page_title="Relatório de Produtividade", layout="wide")

st.title("RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO")
st.write("Faça o upload do arquivo CSV gerado pelo sistema para processar os dados em tempo real.")

st.sidebar.header("Painel de Controle")
data_relatorio = st.sidebar.date_input("Data do Relatório", datetime.now())

meta_promessas = st.sidebar.number_input("Meta de Promessas por Operador", min_value=1, value=3, step=1)

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

        coluna_data = None
        for col in df.columns:
            if 'data' in col.lower() or 'hora' in col.lower() or 'time' in col.lower():
                coluna_data = col
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
                
                conversao = (promessas / cpca * 100) if cpca > 0 else 0.0
                
                op_str = str(op).encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
                summary_data.append({
                    'NOME': op_str,
                    'LOGIN': op_str.split()[0],
                    'CONTATO': contato,
                    'CPC': cpc,
                    'CPCA': cpca,
                    'PROMESSAS': promessas,
                    'VALOR': f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'TICKET MÉDIO': f"R$ {ticket_medio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'CONVERSAO_NUM': conversao,
                    'CONVERSÃO': f"{conversao:.1f}%"
                })

            summary_df = pd.DataFrame(summary_data)
            
            summary_df = summary_df.sort_values(by=['PROMESSAS', 'CONVERSAO_NUM', 'CPCA', 'CONTATO'], ascending=[False, False, False, False]).reset_index(drop=True)

            st.sidebar.subheader("Filtros")
            operadores_disponiveis = summary_df['NOME'].tolist()
            operadores_selecionados = st.sidebar.multiselect("Selecionar Operadores", operadores_disponiveis, default=operadores_disponiveis)

            if operadores_selecionados:
                summary_df = summary_df[summary_df['NOME'].isin(operadores_selecionados)].reset_index(drop=True)

            total_contato = summary_df['CONTATO'].sum()
            total_cpc = summary_df['CPC'].sum()
            total_cpca = summary_df['CPCA'].sum()
            total_promessas = summary_df['PROMESSAS'].sum()
            total_valor = total_promessas * 209.69
            total_conversao = (total_promessas / total_cpca * 100) if total_cpca > 0 else 0.0

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

            # Sugestão 1: Alerta Automático de Auditoria (Omissão/Sabotagem)
            st.subheader("Auditoria de Operadores (Alto Contato e Zero Promessas)")
            audit_df = summary_df[(summary_df['CONTATO'] > 20) & (summary_df['PROMESSAS'] == 0)]
            if not audit_df.empty:
                st.warning("Atenção: Os operadores abaixo realizaram alto volume de contatos, mas estão com zero promessas registradas hoje:")
                st.dataframe(audit_df[['NOME', 'CONTATO', 'CPC', 'CONVERSÃO']], use_container_width=True, hide_index=True)
            else:
                st.success("Nenhum operador crítico detectado na auditoria de hoje.")

            st.markdown("---")

            st.subheader("Flash Report para o WhatsApp (Top 3)")
            if len(summary_df) >= 3:
                top1 = summary_df.iloc[0]
                top2 = summary_df.iloc[1]
                top3 = summary_df.iloc[2]
                whatsapp_text = f"RANKING DE PRODUTIVIDADE\nData: {data_relatorio.strftime('%d/%m/%Y')}\n\n1 - {top1['NOME']} ({top1['PROMESSAS']} promessas | {top1['CONVERSÃO']} conv.)\n2 - {top2['NOME']} ({top2['PROMESSAS']} promessas | {top2['CONVERSÃO']} conv.)\n3 - {top3['NOME']} ({top3['PROMESSAS']} promessas | {top3['CONVERSÃO']} conv.)\n\nTotal da Equipe: {total_promessas} promessas negociadas!"
                st.code(whatsapp_text, language="text")

            st.markdown("---")

            cols_to_display = ['NOME', 'LOGIN', 'CONTATO', 'CPC', 'CPCA', 'PROMESSAS', 'VALOR', 'TICKET MÉDIO', 'CONVERSÃO']
            
            total_row = {
                'NOME': 'TOTAL',
                'LOGIN': 'TOTAL',
                'CONTATO': total_contato,
                'CPC': total_cpc,
                'CPCA': total_cpca,
                'PROMESSAS': total_promessas,
                'VALOR': f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'TICKET MÉDIO': "R$ 209,69",
                'CONVERSÃO': f"{total_conversao:.1f}%"
            }

            display_df = summary_df[cols_to_display].copy()
            display_df = pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)

            st.subheader("Visualização dos Dados Consolidados")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            fig, ax = plt.subplots(figsize=(16, len(display_df) * 0.45 + 2.5), dpi=300)
            ax.axis('off')

            table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)

            col_widths = [0.26, 0.10, 0.08, 0.08, 0.08, 0.09, 0.12, 0.11, 0.08]
            for i, width in enumerate(col_widths):
                for row in range(len(display_df) + 1):
                    table[(row, i)].set_width(width)

            for k, cell in table.get_celld().items():
                cell.set_edgecolor('#D1D5DB')
                cell.set_linewidth(0.8)
                if k[0] == 0:
                    cell.set_facecolor('#2D1B4E')
                    cell.set_text_props(color='#FFFFFF', weight='bold', fontsize=10)
                elif k[0] == len(display_df):
                    cell.set_facecolor('#E2E8F0')
                    cell.set_text_props(color='#0F172A', weight='bold', fontsize=9.5)
                else:
                    op_nome_cel = display_df.iloc[k[0]-1]['NOME'] if k[0] - 1 < len(summary_df) else ""
                    is_meta_batida = False
                    if op_nome_cel and op_nome_cel != 'TOTAL':
                        row_match = summary_df[summary_df['NOME'] == op_nome_cel]
                        if not row_match.empty and row_match.iloc[0]['PROMESSAS'] >= meta_promessas:
                            is_meta_batida = True

                    if is_meta_batida and k[1] == 5:
                        cell.set_facecolor('#DCFCE7')
                        cell.set_text_props(color='#166534', weight='bold', fontsize=9)
                    else:
                        cell.set_facecolor('#F8FAFC' if k[0] % 2 == 0 else '#FFFFFF')
                        cell.set_text_props(color='#1E293B', fontsize=9)

            data_str_title = data_relatorio.strftime('%d/%m/%Y')
            plt.title(f'RELATÓRIO DE PRODUTIVIDADE POR OPERADOR - CONSOLIDADO ({data_str_title})', fontsize=15, weight='bold', pad=30, color='#1E293B')
            plt.tight_layout()
            
            st.pyplot(fig)
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            
            data_str_file = data_relatorio.strftime('%d_%m_%Y')
            st.download_button(
                label="Baixar Relatório em Imagem (PNG)",
                data=buf,
                file_name=f"relatorio_produtividade_{data_str_file}.png",
                mime="image/png"
            )

            # Sugestão 3: Análise de Turnos/Horários (se houver coluna de data/hora)
            if coluna_data:
                st.markdown("---")
                st.subheader("Análise de Produtividade por Turno / Horário")
                try:
                    df['HORA_TEMP'] = pd.to_datetime(df[coluna_data], errors='coerce').dt.hour
                    turno_counts = df.dropna(subset=['HORA_TEMP']).groupby(pd.cut(df['HORA_TEMP'], bins=[0, 12, 18, 24], labels=['Manhã (00h-12h)', 'Tarde (12h-18h)', 'Noite (18h-24h)'])).size()
                    
                    fig_turno, ax_turno = plt.subplots(figsize=(8, 3.5), dpi=300)
                    turno_counts.plot(kind='bar', ax=ax_turno, color='#2D1B4E')
                    ax_turno.set_title("Volume de Atendimentos por Período", fontsize=12, weight='bold', color='#1E293B')
                    ax_turno.set_xlabel("")
                    ax_turno.set_ylabel("Quantidade")
                    plt.xticks(rotation=0)
                    plt.tight_layout()
                    st.pyplot(fig_turno)

                    buf_turno = io.BytesIO()
                    fig_turno.savefig(buf_turno, format="png", bbox_inches='tight')
                    buf_turno.seek(0)
                    st.download_button(
                        label="Baixar Gráfico de Turnos em Imagem (PNG)",
                        data=buf_turno,
                        file_name=f"grafico_turnos_{data_str_file}.png",
                        mime="image/png"
                    )
                except Exception:
                    st.info("Não foi possível processar os horários automaticamente desta base.")

            st.markdown("---")
            st.subheader("Análise de Tipos de Ocorrências na Operação")
            
            ocorrencias_counts = df[coluna_ocorrencia].value_counts().head(8)
            fig_occ, ax_occ = plt.subplots(figsize=(10, 4), dpi=300)
            ocorrencias_counts.plot(kind='barh', ax=ax_occ, color='#4A154B')
            ax_occ.invert_yaxis()
            ax_occ.set_title("Top Ocorrências Registradas", fontsize=12, weight='bold', color='#1E293B')
            ax_occ.set_xlabel("Quantidade")
            ax_occ.set_ylabel("")
            plt.tight_layout()
            
            st.pyplot(fig_occ)

            buf_occ = io.BytesIO()
            fig_occ.savefig(buf_occ, format="png", bbox_inches='tight')
            buf_occ.seek(0)
            
            st.download_button(
                label="Baixar Gráfico de Ocorrências em Imagem (PNG)",
                data=buf_occ,
                file_name=f"grafico_ocorrencias_{data_str_file}.png",
                mime="image/png"
            )

        else:
            st.error("Cabeçalho real não identificado.")
    else:
        st.error("Erro ao ler o arquivo CSV.")
else:
    st.info("Aguardando o envio do arquivo CSV para iniciar o processamento...")
                
