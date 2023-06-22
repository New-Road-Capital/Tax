import numpy as np
import plotly.express as px
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Tax Dashboard', layout="wide", initial_sidebar_state="expanded")


investment_period = 0
retirement_period = 0
invest_r = 0
infl = 0
start_retirement = 0
start_discretionary = 0
salary = 0
contribution_ra = 0
contribution_ds = 0
lump_perc = 0
la_perc = 0


salaries = None
salaries_tax = None

retirement_portfolio = None
retirement_contributions = None
retirement_tax = None

discretionary_portfolio = None
discretionary_contributions = None
discretionary_tax = None

living_portfolio = None
living_withdrawals = None
living_tax = None

lump_portfolio = None
lump_withdrawals = None
lump_tax = None
lump_withdrawal_tax = None


# def income_tax(r):
#     tax = 0

#     if r <= 27_500:
#         tax = 0

#     elif r > 27_500 and r <= 726_000:
#         tax = 0.18*(r-27_500)

#     elif r > 726_000 and r <= 1_089_000:
#         tax = 0.27*(r-726_000) + 125_730

#     elif r > 1_089_000:
#         tax = 0.36*(r-1_089_000) + 223_740

#     return tax

def marginal_tax(r):
    tax = 0

    if r <= 1:
        tax = 0

    elif r > 1 and r <= 237_100:
        tax = 0.18*r

    elif r > 237_100 and r <= 370_500:
        tax = 0.26*(r-237_100) + 42_678

    elif r > 370_500 and r <= 512_800:
        tax = 0.31*(r-370_500) + 77_362

    elif r > 512_800 and r <= 673_000:
        tax = 0.36*(r-512_800) + 121_475

    elif r > 673_000 and r <= 857_900:
        tax = 0.39*(r-673_000) + 179_147

    elif r > 857_900 and r <= 1_817_000:
        tax = 0.41*(r-857_900) + 251_258

    elif r > 1_817_000:
        tax = 0.45*(r-1_817_000) + 644_489

    return tax

def lumpw_tax(r):
    tax = 0

    if r <= 550_000:
        tax = 0

    elif r > 550_000 and r <= 770_000:
        tax = 0.18*(r-550_000)

    elif r > 770_000 and r <= 1_155_000:
        tax = 0.27*(r-770_000) + 39_600
        
    elif r > 1_155_000:
        tax = 0.36*(r-1_155_000) + 143_550

    return tax

def cap_gains_tax(r):
    return marginal_tax(0.4*max(0, r-40_000))

def tax_deduction(r, c):
    return r - min(min(350_000, 0.275*r), c)

def growth_sim(periods, start_val, contribution_perc, salary, mu, infl):

    periods = periods*12 - 1
    contribution_perc = contribution_perc/100
    mu = 1 + mu/100
    infl = 1 + infl/100
    
    portfolio = [start_val]
    contributions = [0]

    for i in range(periods):
        _ = portfolio[-1]*mu**(1/12)
        s = salary/12*(infl**(i//12))
        c = s*contribution_perc

        contributions.append(c)
        portfolio.append(_+c)

    return np.array(portfolio), np.array(contributions)

def la_sim(periods, start_val, portion, mu, infl):
    periods = periods*12 - 1*0
    portion = portion/100*start_val
    mu = 1 + mu/100
    infl = 1 + infl/100

    portfolio = [start_val]
    withdrawals = []

    for i in range(periods):
        _ = portfolio[-1]*mu**(1/12)
        wd = portion/12*(infl**(i//12))

        withdrawals.append(wd)
        portfolio.append(_-wd)

    return np.array(portfolio)[:-1], np.array(withdrawals)

def disc_sim(periods, start_val, portion, mu, infl):
    periods = periods*12 - 1*0
    portion = portion/100
    mu = 1 + mu/100
    infl = 1 + infl/100

    portfolio = [start_val]
    withdrawals = []

    for i in range(periods):
        _ = portfolio[-1]*mu**(1/12)
        wd = _*portion/12

        withdrawals.append(wd)
        portfolio.append(_-wd)

    return np.array(portfolio)[:-1], np.array(withdrawals)

def salary_lister(periods, salary, infl):
    
    periods = periods*12 - 1
    infl = 1 + infl/100
    
    salaries = [0]

    for i in range(periods):
        s = salary/12*(infl**(i//12))

        salaries.append(s)

    return salaries

def salary_tax(salaries, contributions):
    taxes = []

    sals = []
    conts = []

    for s, c in zip(salaries, contributions):

        sals.append(s)
        conts.append(c)

        if len(sals)<12:
            taxes.append(0)
        else:
            taxable = tax_deduction(sum(sals), sum(conts))
            taxes.append(marginal_tax(taxable))
            
            sals.clear()
            conts.clear()

    return taxes

def living_tax_lister(withdrawals):
    taxes = []

    withs = []

    for w in withdrawals[:]:

        withs.append(w)

        if len(withs)<12:
            taxes.append(0)
        else:
            taxable = sum(withs)
            taxes.append(marginal_tax(taxable))
            
            withs.clear()

    return taxes

def lump_tax_lister(withdrawals, portfolio):
    taxes = []
    taxables = []
    base = portfolio[0]

    for i in range(len(withdrawals)):

        cg = (portfolio[i] + withdrawals[i])/base - 1
        t_ratio = cg/((portfolio[i] + withdrawals[i])/base)

        taxables.append(t_ratio*withdrawals[i])

        base = portfolio[i]/(portfolio[i] + withdrawals[i])*base

        if len(taxables)<12:
            taxes.append(0)
        else:
            taxable = sum(taxables)
            taxes.append(cap_gains_tax(taxable))
            
            taxables.clear()

    return taxes

def yearly_converter(arr):
    l = len(arr)
    steps = np.arange(0, l+12, 12)
    yearly = []

    for i in range(len(steps)-1):
        _ = arr[steps[i]:steps[i+1]]
        yearly.append(sum(_))

    return yearly

with st.sidebar:
    
    st.header('Display Options')

    cols = st.columns(2)

    with cols[0]:
        cumm_bool = st.checkbox('Cummulative', False)

    with cols[1]:
        yearly_bool = st.checkbox('Yearly', False)

    # st.header('Inputs')

    with st.expander('Inputs', expanded=True):
        investment_period = st.number_input('Investment Years', min_value=0, max_value=None, value=20)
        retirement_period = st.number_input('Retirement Years', min_value=0, max_value=None, value=20)
        
        invest_r = st.number_input('Investment Return %', min_value=-50.0, max_value=50.0, value=10.0, step=0.5)
        infl = st.number_input('Inflation %', min_value=-50.0, max_value=50.0, value=6.0, step=0.5)

        start_retirement = st.number_input('Starting Retirement Portfolio', min_value=0.0, max_value=None, value=0.0, step=5e4)
        start_discretionary = st.number_input('Starting Discretionary Portfolio', min_value=0.0, max_value=None, value=0.0, step=5e4)

        salary = st.number_input('Monthly Salary', min_value=0.0, max_value=None, value=5e4, step=5e3)
        
        contribution_ra = st.number_input('RA Contribution %', min_value=0.0, max_value=27.5, value=27.5, step=2.5)
        contribution_ds = st.number_input('DS Contribution %', min_value=0.0, max_value=100.0-contribution_ra, value=0.0, step=2.5)
        
        lump_perc = st.number_input('Lumpsum Withdrawal', min_value=0.0, max_value=33.33, value=0.0, step=2.5)
        la_perc = st.number_input('Living Annuity Withdrawal %', min_value=-50.0, max_value=50.0, value=7.5, step=0.5)


retirement_portfolio, retirement_contributions = growth_sim(investment_period, start_retirement, contribution_ra, salary, invest_r, infl)

discretionary_portfolio, discretionary_contributions = growth_sim(investment_period, start_discretionary, contribution_ds, salary, invest_r, infl)

_ = (1-lump_perc/100)*retirement_portfolio[-1]
living_portfolio, living_withdrawals = la_sim(retirement_period, _, la_perc, invest_r, infl)

_ = lump_perc/100*retirement_portfolio[-1]
lump_tax = lumpw_tax(_)
lump_portfolio, lump_withdrawals = disc_sim(retirement_period, _ - lump_tax + discretionary_portfolio[-1], la_perc, invest_r, infl)

salaries = salary_lister(investment_period, salary, infl)
salaries_tax = salary_tax(salaries, retirement_contributions)

living_tax = living_tax_lister(living_withdrawals)
lump_withdrawal_tax = lump_tax_lister(lump_withdrawals, lump_portfolio)


all_incomes = salaries + list(np.array(lump_withdrawals) + np.array(living_withdrawals))

all_taxes = salaries_tax + list(np.array(lump_withdrawal_tax) + np.array(living_tax))
all_net_incomes = list(np.array(all_incomes) - np.array(all_taxes))

all_taxes_incl = all_taxes
all_taxes_incl[len(salaries_tax)+12] = all_taxes_incl[len(salaries_tax)+12] + lump_tax
all_net_incomes_incl = list(np.array(all_incomes) - np.array(all_taxes_incl))


total_retirement_portfolio = list(retirement_portfolio) + list(living_portfolio)
total_discretionary_portfolio = list(discretionary_portfolio) + list(lump_portfolio)

if yearly_bool:

    all_incomes = yearly_converter(all_incomes)
    all_taxes = yearly_converter(all_taxes)
    all_net_incomes = yearly_converter(all_net_incomes)
    all_taxes_incl = yearly_converter(all_taxes_incl)
    all_net_incomes_incl = yearly_converter(all_net_incomes_incl)

    total_retirement_portfolio = total_retirement_portfolio[::12]
    total_discretionary_portfolio = total_discretionary_portfolio[::12]

st.header('Summary')

_ = {
    'Total Income': [sum(all_incomes)],
    'Total Taxes': [sum(all_taxes)],
    'Total Net Income': [sum(all_net_incomes_incl)],
    'Total Portfolio End Value': [total_retirement_portfolio[-1] + total_discretionary_portfolio[-1]],
}

df_summary = pd.DataFrame(_)

st.dataframe(data=df_summary, width=None, height=None, use_container_width=True, hide_index=True, column_order=None, column_config=None)

st.header('Details')

tabs = st.tabs(['Graphs', 'Tables', 'Calculations'])

# st.subheader('Graphs')
with tabs[0]:

    with st.expander('Total'):

        st.header('Total Income')
        if cumm_bool:
            _ = {
                'Total Income': np.cumsum(all_incomes),
            }
        else:
            _ = {
                'Total Income': (all_incomes),
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})

        st.header('Total Taxes')
        if cumm_bool:
            _ = {
                'Total Taxes': np.cumsum(all_taxes_incl),
            }
        else:
            _ = {
                'Total Taxes': (all_taxes_incl),
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})


    with st.expander('Net'):

        st.header('Net Income')
        if cumm_bool:
            _ = {
                'Net Income': np.cumsum(all_net_incomes),
            }
        else:
            _ = {
                'Net Income': (all_net_incomes),
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})

        st.header('Income Taxes')
        if cumm_bool:
            _ = {
                'Income Taxes': np.cumsum(all_taxes),
            }
        else:
            _ = {
                'Income Taxes': (all_taxes),
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})


    with st.expander('Portfolio'):

        st.header('Retirement Portfolio')
        if cumm_bool:
            _ = {
                'Retirement Portfolio': total_retirement_portfolio,
            }
        else:
            _ = {
                'Retirement Portfolio': total_retirement_portfolio,
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})

        st.header('Discretionary Portfolio')
        if cumm_bool:
            _ = {
                'Discretionary Portfolio': total_discretionary_portfolio,
            }
        else:
            _ = {
                'Discretionary Portfolio': total_discretionary_portfolio,
            }

        df = pd.DataFrame(_)

        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False})
        

# st.subheader('Tables')
with tabs[1]:

    with st.expander('Data'):
        if cumm_bool:
            _ = {
                'Total Income': np.cumsum(all_incomes),
                'Total Taxes': np.cumsum(all_taxes_incl),
                'Net Income': np.cumsum(all_net_incomes),
                'Income Taxes': np.cumsum(all_taxes),
                'Retirement Portfolio': total_retirement_portfolio,
                'Discretionary Portfolio': total_discretionary_portfolio,
            }
        else:
            _ = {
                'Total Income': all_incomes,
                'Total Taxes': all_taxes_incl,
                'Net Income': all_net_incomes,
                'Income Taxes': all_taxes,
                'Retirement Portfolio': total_retirement_portfolio,
                'Discretionary Portfolio': total_discretionary_portfolio,
            }

        df = pd.DataFrame(_)

        if yearly_bool:
            df.index.name='Year'
        else:
            df.index.name='Month'

        st.dataframe(df, width=None, height=None, use_container_width=True, hide_index=False, column_order=None, column_config=None)


# st.subheader('Calculations')
with tabs[2]:

    with st.expander('Tax Methodology'):

        st.subheader('Marginal Tax')

        code = '''
        tax = 0
        r = income

        if r <= 1:
            tax = 0

        elif r > 1 and r <= 237_100:
            tax = 0.18*r

        elif r > 237_100 and r <= 370_500:
            tax = 0.26*(r-237_100) + 42_678

        elif r > 370_500 and r <= 512_800:
            tax = 0.31*(r-370_500) + 77_362

        elif r > 512_800 and r <= 673_000:
            tax = 0.36*(r-512_800) + 121_475

        elif r > 673_000 and r <= 857_900:
            tax = 0.39*(r-673_000) + 179_147

        elif r > 857_900 and r <= 1_817_000:
            tax = 0.41*(r-857_900) + 251_258

        elif r > 1_817_000:
            tax = 0.45*(r-1_817_000) + 644_489
        '''
        st.code(code)

        st.subheader('Lumpsum Withdrawal Tax')

        code = '''
        tax = 0
        r = withdrawal

        if r <= 550_000:
            tax = 0

        elif r > 550_000 and r <= 770_000:
            tax = 0.18*(r-550_000)

        elif r > 770_000 and r <= 1_155_000:
            tax = 0.27*(r-770_000) + 39_600
            
        elif r > 1_155_000:
            tax = 0.36*(r-1_155_000) + 143_550
        '''
        st.code(code)

        st.subheader('Capital Gains Tax')

        code = '''
        r = capital_gain

        cap_gains_tax = marginal_tax(0.4*max(0, r-40_000))
        '''
        st.code(code)

        st.subheader('Tax Deduction from RA Contribution')

        code = '''
        r = income
        c = contribution

        tax_deduction = r - min(min(350_000, 0.275*r), c)
        '''
        st.code(code)


# cgt tax graph
# no <0 portfolio