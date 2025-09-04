import streamlit as st
import pandas as pd
import re
from streamlit_option_menu import option_menu
from modules.drive_access import get_files_from_drive_folder
from modules.data_processor import process_spreadsheet
from modules.calculations import calcular_pagamento_semanal, calcular_pagamento_individual
from modules.config import FORMAS_PAGAMENTO_VALIDAS, INVALID_CLIENTS
from modules.pdf_generator import (
    create_pdf,
    create_tech_payment_receipt,
    create_technician_of_the_week_receipt,
)
from modules.visualization import (
    plot_weekly_evolution,
    plot_weekly_payments,
    plot_payment_methods_total,
    plot_payment_methods_usage
)
from modules.utils import format_currency
from modules.payroll_module import payroll_page
from modules.verificacao_zip_codes import zip_code_page
from modules.limpeza_numeros import limpeza_numeros_page
from modules.franchises_module import franchises_page
from modules.home_page import home_page


def local_css():
    """Carrega um arquivo CSS local para estilizar a aplicação."""
    try:
        with open("styles.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("O ficheiro 'styles.css' não foi encontrado. A estilização pode não ser aplicada corretamente.")


def extract_folder_id(url_or_id):
    """
    Extrai o ID da pasta de um URL do Google Drive ou retorna a string se já for um ID.
    """
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    return url_or_id


def financial_analysis_page(data):
    """Conteúdo da página de Análises Financeiras."""

    # Título principal do dashboard
    st.markdown(
        """
        <div style="padding-top: 10px; padding-bottom: 10px;">
            <h1 style="font-weight: 700;">Dashboard de Análises Financeiras</h1>
            <p style="color: #666; font-size: 1.1rem;">Visão geral da performance e métricas operacionais.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Processamento dos dados
    completed_services = data[data['Realizado']]
    not_completed = data[(data['Realizado'] == False) & (data['Cliente'].notna())]

    if 'Pets' in completed_services.columns:
        quantidade_pets = completed_services['Pets'].sum()
    else:
        quantidade_pets = 0

    dias_trabalhados = completed_services.groupby(['Nome', 'Semana', 'Data']).size().reset_index()
    dias_trabalhados = dias_trabalhados.groupby(['Nome', 'Semana']).size().reset_index(name='Dias Trabalhados')

    weekly_totals = completed_services.groupby(['Nome', 'Semana', 'Categoria']).agg({
        'Serviço': 'sum',
        'Gorjeta': 'sum',
        'Dia': 'count'
    }).reset_index()

    weekly_totals = pd.merge(weekly_totals, dias_trabalhados, on=['Nome', 'Semana'], how='left')

    weekly_totals[['Pagamento Tecnico', 'Lucro Empresa']] = weekly_totals.apply(
        calcular_pagamento_semanal, axis=1, result_type='expand'
    )

    completed_services[['Pagamento Tecnico', 'Lucro Empresa']] = completed_services.apply(
        lambda x: calcular_pagamento_individual(x, weekly_totals), axis=1, result_type='expand'
    )

    # 📊 Cartões de Métricas - Layout mais compacto
    total_lucro = completed_services['Lucro Empresa'].sum()

    with st.container():
        st.markdown('<h3 style="margin-bottom: 0;">Métricas Gerais</h3>', unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Realizados</p><p class="metric-value-compact">{0}</p></div>'.format(len(completed_services)), unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Total Pets</p><p class="metric-value-compact">{0}</p></div>'.format(quantidade_pets), unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Não Realizados</p><p class="metric-value-compact">{0}</p></div>'.format(len(not_completed)), unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Total Serviços</p><p class="metric-value-compact">{0}</p></div>'.format(format_currency(completed_services["Serviço"].sum())), unsafe_allow_html=True)
        with col5:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Total Gorjetas</p><p class="metric-value-compact">{0}</p></div>'.format(format_currency(completed_services["Gorjeta"].sum())), unsafe_allow_html=True)
        with col6:
            st.markdown('<div class="metric-card-compact"><p class="metric-title-compact">Lucro Empresa</p><p class="metric-value-compact">{0}</p></div>'.format(format_currency(total_lucro)), unsafe_allow_html=True)

    st.markdown("---")

    # 📈 Gráficos e Tabelas - Layout de duas colunas
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Evolução e Pagamentos")
        st.plotly_chart(plot_weekly_evolution(weekly_totals), use_container_width=True)

        st.plotly_chart(plot_weekly_payments(weekly_totals), use_container_width=True)

    with col2:
        st.markdown("### Resumo por Técnico")
        tech_summary = weekly_totals.groupby(['Nome', 'Categoria']).agg({
            'Serviço': 'sum',
            'Gorjeta': 'sum',
            'Pagamento Tecnico': 'sum',
            'Lucro Empresa': 'sum',
            'Dia': 'sum',
            'Dias Trabalhados': 'sum'
        }).reset_index()

        tech_summary.columns = ['Técnico', 'Categoria', 'Total Serviços',
                                'Total Gorjetas', 'Total Pagamento', 'Lucro Empresa',
                                'Atendimentos', 'Dias Trabalhados']

        tech_summary['Média Atendimento'] = tech_summary['Total Serviços'] / tech_summary['Atendimentos']
        tech_summary['Gorjeta Média'] = tech_summary['Total Gorjetas'] / tech_summary['Atendimentos']

        for col in ['Total Serviços', 'Total Gorjetas', 'Total Pagamento', 'Lucro Empresa',
                    'Média Atendimento', 'Gorjeta Média']:
            tech_summary[col] = tech_summary[col].apply(format_currency)

        st.dataframe(tech_summary.sort_values('Atendimentos', ascending=False), hide_index=True)

        st.markdown("### Atendimentos Não Realizados")
        if not not_completed.empty:
            st.warning(f"{len(not_completed)} atendimentos não realizados.")
            st.dataframe(not_completed[['Nome', 'Dia', 'Data', 'Cliente']], hide_index=True)
        else:
            st.success("Todos os agendamentos foram realizados!")

    # 💳 Resumo de Pagamento
    st.markdown("---")
    st.markdown("### Resumo de Pagamento")
    valid_payments = completed_services[completed_services['Pagamento'].isin(FORMAS_PAGAMENTO_VALIDAS)]

    if not valid_payments.empty:
        payment_summary = valid_payments.groupby('Pagamento').agg({
            'Serviço': 'sum',
            'Gorjeta': 'sum',
            'Cliente': 'count'
        }).reset_index().rename(columns={'Cliente': 'Qtd Usos'})

        payment_summary['Total'] = payment_summary['Serviço'] + payment_summary['Gorjeta']
        payment_summary['Percentual Uso'] = (payment_summary['Qtd Usos'] / payment_summary['Qtd Usos'].sum() * 100).round(2)

        st.dataframe(payment_summary, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_payment_methods_total(payment_summary), use_container_width=True)
        with col2:
            st.plotly_chart(plot_payment_methods_usage(payment_summary), use_container_width=True)

    st.markdown("---")

    # 📤 Exportar Dados
    st.markdown("### Exportar Dados")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📁 Baixar CSV",
            data=csv,
            file_name="servicos_tecnicos.csv",
            mime="text/csv"
        )

    with col2:
        pdf = create_pdf(completed_services)
        pdf_output = pdf.output(dest='S').encode('latin-1')

        st.download_button(
            label="📥 Baixar Relatório PDF",
            data=pdf_output,
            file_name="relatorio_geral.pdf",
            mime="application/pdf"
        )

    with col3:
        if len(st.session_state.selected_techs) == 1 and len(st.session_state.selected_weeks) == 1:
            tech_name = st.session_state.selected_techs[0]
            week = st.session_state.selected_weeks[0]
            tech_data = completed_services[
                (completed_services['Nome'] == tech_name) & (completed_services['Semana'] == week)
            ]

            pdf = create_tech_payment_receipt(tech_data, tech_name, week)
            pdf_output = pdf.output(dest='S').encode('latin-1')

            st.download_button(
                label=f"📥 Recibo {tech_name}",
                data=pdf_output,
                file_name=f"recibo_{tech_name}_{week}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Selecione exatamente 1 técnico e 1 semana para gerar o recibo.")

    with col4:
        if len(st.session_state.selected_techs) == 1 and len(st.session_state.selected_weeks) == 1:
            tech_name = st.session_state.selected_techs[0]
            week = st.session_state.selected_weeks[0]
            tech_data = completed_services[
                (completed_services['Nome'] == tech_name) & (completed_services['Semana'] == week)
            ]

            pdf = create_technician_of_the_week_receipt(tech_data, tech_name, week)
            pdf_output = pdf.output(dest='S').encode('latin-1')

            st.download_button(
                label=f"🏆 Recibo TECH of the WEEK {tech_name}",
                data=pdf_output,
                file_name=f"technician_of_the_week_{tech_name}_{week}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Selecione exatamente 1 técnico e 1 semana para gerar o recibo.")

    st.markdown("""
        ---
        <small>Desenvolvido por Alan Salviano | Análise de Planilhas de Serviços Técnicos</small>
    """, unsafe_allow_html=True)


def main():
    """Função principal que controla a navegação entre as páginas."""
    st.set_page_config(page_title="BNS App", layout="wide")
    local_css()

    # Inicializa o estado de login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "Início"

    # Sidebar com menu de opções
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://i.imgur.com/50oBRbq.png" alt="Logo da Empresa" width="200">
        </div>
        """, unsafe_allow_html=True)

        st.session_state.selected_page = option_menu(
            menu_title=None,
            options=["Início", "Análises Financeiras", "Payroll dos Técnicos", "Franchises", "Limpeza de Números", "Zip Codes"],
            icons=["star", "star", "star", "star", "star", "star"],
            menu_icon="cast",
            default_index=0,
            styles={
                "nav-link-selected": {"background-color": "#f65a93"},
            }
        )

    # Lógica de carregamento de dados (compartilhada entre as páginas)
    if st.session_state.selected_page in ["Análises Financeiras", "Payroll dos Técnicos"]:
        st.sidebar.title("Filtros e Dados")
        drive_folder_input = st.sidebar.text_input("Cole o ID ou URL da pasta do Google Drive")
        drive_folder_id = extract_folder_id(drive_folder_input)

        all_dataframes = []

        if drive_folder_id:
            with st.spinner('Acedendo ao Google Drive e a processar as planilhas...'):
                try:
                    files_data = get_files_from_drive_folder(drive_folder_id)
                    if files_data:
                        for file_content in files_data:
                            df = process_spreadsheet(file_content)
                            if not df.empty:
                                all_dataframes.append(df)
                except Exception as e:
                    st.error(f"Erro ao aceder ao Google Drive: {e}")
                    st.stop()
        else:
            uploaded_files = st.sidebar.file_uploader("Ou carregue uma ou mais planilhas Excel", type=['xlsx'], accept_multiple_files=True)
            files_to_process = uploaded_files
            for file in files_to_process:
                df = process_spreadsheet(file)
                if not df.empty:
                    all_dataframes.append(df)

        if not all_dataframes:
            st.warning("⚠️ Nenhuma planilha carregada. Por favor, carregue uma planilha para iniciar.")
            st.stop()

        data = pd.concat(all_dataframes, ignore_index=True)

        # Filtros que serão aplicados a ambas as páginas
        st.sidebar.header("Filtrar por:")
        st.session_state.selected_weeks = st.sidebar.multiselect("Selecione as semanas para análise", options=data['Semana'].unique())
        st.session_state.selected_techs = st.sidebar.multiselect("Selecione os técnicos:", options=data['Nome'].unique(), default=list(data['Nome'].unique()))
        st.session_state.selected_categories = st.sidebar.multiselect("Selecione as categorias:", options=data['Categoria'].unique(), default=list(data['Categoria'].unique()))

        filtered_data = data.copy()
        if st.session_state.selected_weeks:
            filtered_data = filtered_data[filtered_data['Semana'].isin(st.session_state.selected_weeks)]
        if st.session_state.selected_techs:
            filtered_data = filtered_data[filtered_data['Nome'].isin(st.session_state.selected_techs)]
        if st.session_state.selected_categories:
            filtered_data = filtered_data[filtered_data['Categoria'].isin(st.session_state.selected_categories)]

        if filtered_data.empty:
            st.warning("Nenhum dado encontrado com os filtros selecionados.")
            st.stop()
            
    # Exibição da página selecionada
    if st.session_state.selected_page == "Início":
        home_page()
    elif st.session_state.selected_page == "Análises Financeiras":
        financial_analysis_page(filtered_data)
    elif st.session_state.selected_page == "Payroll dos Técnicos":
        payroll_page(filtered_data)
    elif st.session_state.selected_page == "Franchises":
        franchises_page()
    elif st.session_state.selected_page == "Zip Codes":
        zip_code_page()
    elif st.session_state.selected_page == "Limpeza de Números":
        limpeza_numeros_page()


if __name__ == "__main__":
    main()
