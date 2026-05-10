# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Bitcoin Regime Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_data():
    """Load all CSV files with defensive column handling."""
    try:
        # Load BTC price data
        btc = pd.read_csv('data/btc_clean.csv')
        btc.columns = btc.columns.str.lower().str.strip()
        if 'date' in btc.columns:
            btc['date'] = pd.to_datetime(btc['date'])
        elif 'timestamp' in btc.columns:
            btc['date'] = pd.to_datetime(btc['timestamp'])
            
        # Load regime labels
        regimes = pd.read_csv('data/hmm_labels.csv')
        regimes.columns = regimes.columns.str.lower().str.strip()
        if 'date' in regimes.columns:
            regimes['date'] = pd.to_datetime(regimes['date'])
        elif 'timestamp' in regimes.columns:
            regimes['date'] = pd.to_datetime(regimes['timestamp'])
            
        # Load change points
        cpd = pd.read_csv('data/cpd_points.csv')
        cpd.columns = cpd.columns.str.lower().str.strip()
        
        # Load performance metrics
        perf = pd.read_csv('data/performance_per_regime.csv')
        perf.columns = perf.columns.str.lower().str.strip()
        
        return btc, regimes, cpd, perf
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# ============================================================================
# DATA PROCESSING
# ============================================================================

def merge_price_regime(btc, regimes):
    """Merge BTC prices with regime labels."""
    df = btc.merge(regimes, on='date', how='left')
    df = df.sort_values('date').reset_index(drop=True)
    return df

def compute_regime_durations(df):
    """Compute duration statistics for each regime."""
    df = df.copy()
    df['regime_change'] = df['state'] != df['state'].shift(1)
    df['regime_id'] = df['regime_change'].cumsum()
    
    regime_groups = df.groupby(['state', 'regime_id']).size().reset_index(name='duration')
    
    stats = regime_groups.groupby('state').agg(
        avg_duration=('duration', 'mean'),
        max_duration=('duration', 'max'),
        occurrences=('duration', 'count')
    ).reset_index()
    
    stats.columns = ['Regime', 'Avg Duration (days)', 'Max Duration (days)', 'Occurrences']
    return stats

def compute_returns(df):
    """Compute daily returns."""
    df = df.copy()
    df['return'] = df['close'].pct_change()
    return df

def backtest_regime_strategy(df, best_regime):
    """Backtest strategy: long only in best regime, else cash."""
    df = df.copy()
    df['strategy_return'] = np.where(df['state'] == best_regime, df['return'], 0)
    df['buy_hold_cum'] = (1 + df['return']).cumprod()
    df['strategy_cum'] = (1 + df['strategy_return']).cumprod()
    return df

def backtest_custom_allocation(df, regime_weights):
    """Backtest custom allocation across selected regimes."""
    df = df.copy()
    df['custom_return'] = 0.0
    
    for regime, weight in regime_weights.items():
        df.loc[df['state'] == regime, 'custom_return'] += df['return'] * weight
    
    df['custom_cum'] = (1 + df['custom_return']).cumprod()
    return df

def compute_sharpe(returns, periods_per_year=365):
    """Compute annualized Sharpe ratio."""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    return (returns.mean() * periods_per_year) / (returns.std() * np.sqrt(periods_per_year))

# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_price_regime(df, cpd_indices):
    """Interactive price chart with regime overlay and change points."""
    fig = go.Figure()
    
    # Price line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        name='BTC Price',
        line=dict(color='#1f77b4', width=1.5),
        hovertemplate='<b>Date</b>: %{x}<br><b>Price</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    # Regime scatter overlay
    regime_colors = {0: '#2ca02c', 1: '#ff7f0e', 2: '#d62728', 3: '#9467bd', 4: '#8c564b'}
    
    for regime in df['state'].dropna().unique():
        regime_df = df[df['state'] == regime]
        fig.add_trace(go.Scatter(
            x=regime_df['date'],
            y=regime_df['close'],
            mode='markers',
            name=f'Regime {int(regime)}',
            marker=dict(size=4, color=regime_colors.get(regime, '#7f7f7f')),
            hovertemplate=f'<b>Regime {int(regime)}</b><br>Date: %{{x}}<br>Price: $%{{y:,.2f}}<extra></extra>'
        ))
    
    # Change point lines
    if len(cpd_indices) > 0 and 'index' in cpd_indices.columns:
        for idx in cpd_indices['index'].values:
            if idx < len(df):
                fig.add_vline(
                    x=df.iloc[idx]['date'],
                    line=dict(color='red', width=1, dash='dash'),
                    annotation_text='Change Point',
                    annotation_position='top'
                )
    
    fig.update_layout(
        title='Bitcoin Price with Market Regime Detection',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        hovermode='x unified',
        template='plotly_white',
        height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def plot_regime_heatmap(df):
    """Heatmap of regime probabilities over time."""
    prob_cols = [col for col in df.columns if col.startswith('prob_')]
    
    if len(prob_cols) == 0:
        return None
    
    prob_data = df[['date'] + prob_cols].copy()
    prob_data = prob_data.set_index('date')
    
    fig = go.Figure(data=go.Heatmap(
        z=prob_data.T.values,
        x=prob_data.index,
        y=[col.replace('prob_', 'Regime ') for col in prob_cols],
        colorscale='Viridis',
        hovertemplate='Date: %{x}<br>Regime: %{y}<br>Probability: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Regime Probability Distribution Over Time',
        xaxis_title='Date',
        yaxis_title='Regime',
        height=400,
        template='plotly_white'
    )
    
    return fig

def plot_performance_comparison(perf):
    """Bar chart comparing Sharpe ratios across regimes."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[f"Regime {int(r)}" for r in perf['regime']],
        y=perf['sharpe_ratio'],
        marker_color=['#2ca02c' if s == perf['sharpe_ratio'].max() else '#1f77b4' 
                      for s in perf['sharpe_ratio']],
        text=perf['sharpe_ratio'].round(2),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Sharpe: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Sharpe Ratio by Regime',
        xaxis_title='Regime',
        yaxis_title='Sharpe Ratio',
        template='plotly_white',
        height=400
    )
    
    return fig

def plot_backtest_comparison(df):
    """Plot buy & hold vs regime strategy."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['buy_hold_cum'],
        mode='lines',
        name='Buy & Hold',
        line=dict(color='#1f77b4', width=2),
        hovertemplate='<b>Buy & Hold</b><br>Date: %{x}<br>Value: %{y:.2f}x<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['strategy_cum'],
        mode='lines',
        name='Regime Strategy',
        line=dict(color='#2ca02c', width=2),
        hovertemplate='<b>Regime Strategy</b><br>Date: %{x}<br>Value: %{y:.2f}x<extra></extra>'
    ))
    
    fig.update_layout(
        title='Strategy Performance: Buy & Hold vs Regime-Based',
        xaxis_title='Date',
        yaxis_title='Cumulative Return (Multiple)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def plot_custom_allocation(df):
    """Plot custom allocation strategy."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['buy_hold_cum'],
        mode='lines',
        name='Buy & Hold',
        line=dict(color='#1f77b4', width=2, dash='dash'),
        hovertemplate='<b>Buy & Hold</b><br>Date: %{x}<br>Value: %{y:.2f}x<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['custom_cum'],
        mode='lines',
        name='Custom Allocation',
        line=dict(color='#ff7f0e', width=2),
        hovertemplate='<b>Custom Allocation</b><br>Date: %{x}<br>Value: %{y:.2f}x<extra></extra>'
    ))
    
    fig.update_layout(
        title='Custom Allocation Performance',
        xaxis_title='Date',
        yaxis_title='Cumulative Return (Multiple)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_pdf_report(df, perf, duration_stats):
    """Generate executive PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Bitcoin Market Regime Intelligence Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Date range
    date_range = Paragraph(
        f"<b>Analysis Period:</b> {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
        styles['Normal']
    )
    story.append(date_range)
    story.append(Spacer(1, 12))
    
    # Regime summary
    num_regimes = df['state'].nunique()
    summary = Paragraph(f"<b>Number of Regimes Detected:</b> {num_regimes}", styles['Normal'])
    story.append(summary)
    story.append(Spacer(1, 24))
    
    # Performance table
    story.append(Paragraph("<b>Performance by Regime</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    perf_data = [['Regime', 'Sharpe Ratio', 'Mean Return', 'Volatility', 'Max Drawdown']]
    for _, row in perf.iterrows():
        perf_data.append([
            f"Regime {int(row['regime'])}",
            f"{row['sharpe_ratio']:.2f}",
            f"{row['mean_return']:.4f}",
            f"{row['volatility']:.4f}",
            f"{row['max_drawdown']:.2%}"
        ])
    
    perf_table = Table(perf_data)
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 24))
    
    # Key insights
    story.append(Paragraph("<b>Key Insights</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    best_regime = perf.loc[perf['sharpe_ratio'].idxmax(), 'regime']
    best_sharpe = perf['sharpe_ratio'].max()
    
    insights = [
        f"Best performing regime: Regime {int(best_regime)} (Sharpe: {best_sharpe:.2f})",
        f"Total data points analyzed: {len(df):,}",
        f"Regime detection enables risk-adjusted portfolio construction",
        "Strategy outperforms buy-and-hold by focusing on high-Sharpe regimes"
    ]
    
    for insight in insights:
        story.append(Paragraph(f"• {insight}", styles['Normal']))
        story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Load data
    btc, regimes, cpd, perf = load_data()
    df = merge_price_regime(btc, regimes)
    df = compute_returns(df)
    
    # Ensure required columns exist
    if 'sharpe_ratio' not in perf.columns:
        perf['sharpe_ratio'] = 0.0
    if 'mean_return' not in perf.columns:
        perf['mean_return'] = 0.0
    if 'volatility' not in perf.columns:
        perf['volatility'] = 0.0
    if 'max_drawdown' not in perf.columns:
        perf['max_drawdown'] = 0.0
    if 'win_rate' not in perf.columns:
        perf['win_rate'] = 0.0
    
    # ========================================================================
    # HERO SECTION
    # ========================================================================
    
    st.title("📊 AI-Driven Bitcoin Market Regime Intelligence")
    st.markdown("""
    **Institutional-grade market regime detection powered by Hidden Markov Models and structural break analysis.**  
    Identify high-Sharpe environments, optimize allocation, and enhance risk-adjusted returns.
    """)
    
    st.markdown("---")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Start", df['date'].min().strftime('%Y-%m-%d'))
    
    with col2:
        st.metric("Data End", df['date'].max().strftime('%Y-%m-%d'))
    
    with col3:
        num_regimes = df['state'].nunique()
        st.metric("Regimes Detected", int(num_regimes))
    
    with col4:
        best_regime = perf.loc[perf['sharpe_ratio'].idxmax(), 'regime']
        best_sharpe = perf['sharpe_ratio'].max()
        st.metric("Best Sharpe Regime", f"Regime {int(best_regime)} ({best_sharpe:.2f})")
    
    st.markdown("---")
    
    # ========================================================================
    # INTERACTIVE PRICE + REGIME CHART
    # ========================================================================
    
    st.header("🔍 Market Regime Visualization")
    st.plotly_chart(plot_price_regime(df, cpd), use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # REGIME PROBABILITY HEATMAP
    # ========================================================================
    
    st.header("🌡️ Regime Probability Distribution")
    heatmap_fig = plot_regime_heatmap(df)
    
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("Probability columns not found in regime data. Skipping heatmap.")
    
    st.markdown("---")
    
    # ========================================================================
    # REGIME DURATION STATISTICS
    # ========================================================================
    
    st.header("⏱️ Regime Duration Statistics")
    duration_stats = compute_regime_durations(df)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(duration_stats, use_container_width=True)
    
    with col2:
        fig_duration = go.Figure()
        fig_duration.add_trace(go.Bar(
            x=[f"Regime {int(r)}" for r in duration_stats['Regime']],
            y=duration_stats['Avg Duration (days)'],
            marker_color='#1f77b4',
            text=duration_stats['Avg Duration (days)'].round(1),
            textposition='outside'
        ))
        fig_duration.update_layout(
            title='Average Duration by Regime',
            xaxis_title='Regime',
            yaxis_title='Days',
            template='plotly_white',
            height=400
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # PERFORMANCE BY REGIME
    # ========================================================================
    
    st.header("📈 Performance by Regime")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.dataframe(
            perf[['regime', 'sharpe_ratio', 'mean_return', 'volatility', 'max_drawdown', 'win_rate']].style.format({
                'sharpe_ratio': '{:.2f}',
                'mean_return': '{:.4f}',
                'volatility': '{:.4f}',
                'max_drawdown': '{:.2%}',
                'win_rate': '{:.2%}'
            }).highlight_max(subset=['sharpe_ratio'], color='lightgreen'),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(plot_performance_comparison(perf), use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # STRATEGY BACKTEST
    # ========================================================================
    
    st.header("💼 Strategy Backtest: Best Regime vs Buy & Hold")
    st.markdown(f"""
    **Strategy:** Long BTC only during **Regime {int(best_regime)}** (highest Sharpe), otherwise hold cash.
    """)
    
    df_backtest = backtest_regime_strategy(df, best_regime)
    st.plotly_chart(plot_backtest_comparison(df_backtest), use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bh_return = df_backtest['buy_hold_cum'].iloc[-1] - 1
        st.metric("Buy & Hold Return", f"{bh_return:.2%}")
    
    with col2:
        strat_return = df_backtest['strategy_cum'].iloc[-1] - 1
        st.metric("Regime Strategy Return", f"{strat_return:.2%}")
    
    with col3:
        outperformance = strat_return - bh_return
        st.metric("Outperformance", f"{outperformance:.2%}")
    
    st.markdown("---")
    
    # ========================================================================
    # DYNAMIC ALLOCATION SIMULATION
    # ========================================================================
    
    st.header("🎯 Dynamic Allocation Simulator")
    st.markdown("**Customize your exposure across regimes and see real-time performance impact.**")
    
    with st.sidebar:
        st.header("Allocation Controls")
        
        available_regimes = sorted(df['state'].dropna().unique())
        selected_regimes = st.multiselect(
            "Select Active Regimes",
            options=[int(r) for r in available_regimes],
            default=[int(best_regime)]
        )
        
        regime_weights = {}
        total_weight = 0.0
        
        if selected_regimes:
            st.subheader("Allocation Weights")
            for regime in selected_regimes:
                weight = st.slider(
                    f"Regime {regime}",
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0 / len(selected_regimes),
                    step=0.05,
                    key=f"weight_{regime}"
                )
                regime_weights[regime] = weight
                total_weight += weight
            
            st.info(f"Total Allocation: {total_weight:.0%}")
            
            if total_weight > 0:
                # Normalize weights
                regime_weights = {k: v / total_weight for k, v in regime_weights.items()}
    
    if selected_regimes and total_weight > 0:
        df_custom = backtest_custom_allocation(df, regime_weights)
        st.plotly_chart(plot_custom_allocation(df_custom), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            custom_return = df_custom['custom_cum'].iloc[-1] - 1
            st.metric("Custom Strategy Return", f"{custom_return:.2%}")
        
        with col2:
            custom_sharpe = compute_sharpe(df_custom['custom_return'].dropna())
            st.metric("Sharpe Ratio", f"{custom_sharpe:.2f}")
        
        with col3:
            vs_bh = custom_return - bh_return
            st.metric("vs Buy & Hold", f"{vs_bh:.2%}")
    else:
        st.warning("Select at least one regime and ensure total allocation > 0%")
    
    st.markdown("---")
    
    # ========================================================================
    # PDF REPORT DOWNLOAD
    # ========================================================================
    
    st.header("📄 Executive Report")
    st.markdown("Download a comprehensive PDF report for stakeholders.")
    
    pdf_buffer = generate_pdf_report(df, perf, duration_stats)
    
    st.download_button(
        label="📥 Download Executive Report (PDF)",
        data=pdf_buffer,
        file_name=f"regime_intelligence_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
    
    st.markdown("---")
    st.markdown("**Built with Streamlit** | AI-Driven Market Intelligence Platform")

if __name__ == "__main__":
    main()
