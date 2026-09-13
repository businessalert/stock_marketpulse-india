import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Market Cap Flow & Industry Dashboard", layout="wide")

st.title("📊 Market Capitalization Flow & Stock Intelligence Dashboard")
st.markdown("Integrated Dashboard featuring Real Company Names, NSE/BSE Tickers, Industry Groups, and Capital Shifts.")

@st.cache_data
def load_data():
    # Load mapping CSV
    mapping_df = pd.read_csv("query-results_13.09.2026.csv")
    
    # Load Excel Market Cap Flow sheets
    excel_file = "Market Cap Flow.xlsx"
    xls = pd.ExcelFile(excel_file)
    
    sheet7 = pd.read_excel(excel_file, sheet_name="Sheet7")
    industry_df = pd.read_excel(excel_file, sheet_name="Industry")
    industry_group_df = pd.read_excel(excel_file, sheet_name="Industry Group")
    
    return mapping_df, sheet7, industry_df, industry_group_df

try:
    mapping_df, sheet7, industry_df, industry_group_df = load_data()
    
    # Sidebar Navigation
    st.sidebar.header("Navigation")
    dashboard_mode = st.sidebar.radio("Select View:", [
        "Industry Capital Flow Overview",
        "Stock Screener & Entity Mapping",
        "Cigar Butt / Value Opportunities"
    ])
    
    if dashboard_mode == "Industry Capital Flow Overview":
        st.subheader("Industry-wise Market Capitalization & Stock Count")
        
        # Clean Sheet7
        if "Industry" in sheet7.columns:
            st.dataframe(sheet7, use_container_width=True)
            
            # Visualizing Top Industries by Market Cap
            if "SUM of Market Capitalization" in sheet7.columns:
                top_industries = sheet7.sort_values(by="SUM of Market Capitalization", ascending=False).head(15)
                fig = px.bar(
                    top_industries, 
                    x="Industry", 
                    y="SUM of Market Capitalization",
                    color="COUNTA of Name",
                    title="Top 10 Industries by Market Capitalization",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Displaying raw industry summary data.")
            st.dataframe(sheet7.head(50), use_container_width=True)
            
    elif dashboard_mode == "Stock Screener & Entity Mapping":
        st.subheader("Master Stock Mapping & Fundamental Screener")
        
        # Filters
        industries = mapping_df['Industry'].dropna().unique()
        selected_industry = st.selectbox("Filter by Industry:", ["All"] + list(industries))
        
        filtered_df = mapping_df if selected_industry == "All" else mapping_df[mapping_df['Industry'] == selected_industry]
        
        st.write(f"Showing **{len(filtered_df)}** companies")
        
        display_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry Group', 'Industry', 'Current Price', 'Market Capitalization', 'Price to Earning', 'Return on capital employed']
        existing_cols = [col for col in display_cols if col in filtered_df.columns]
        
        st.dataframe(filtered_df[existing_cols], use_container_width=True)
        
    elif dashboard_mode == "Cigar Butt / Value Opportunities":
        st.subheader("Cigar Butt & Deep Value Screener")
        st.markdown("Filtering companies trading below intrinsic value or at attractive P/E ratios with solid ROCE.")
        
        if 'Intrinsic Value' in mapping_df.columns and 'Current Price' in mapping_df.columns:
            value_stocks = mapping_df[mapping_df['Intrinsic Value'] > mapping_df['Current Price']].dropna(subset=['Name', 'Current Price', 'Intrinsic Value'])
            st.write(f"Found **{len(value_stocks)}** potential value opportunities.")
            
            val_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Intrinsic Value', 'Price to Earning', 'Return on capital employed']
            existing_val_cols = [col for col in val_cols if col in value_stocks.columns]
            
            st.dataframe(value_stocks[existing_val_cols].head(50), use_container_width=True)
        else:
            st.info("Fundamental valuation columns not found in the mapping dataset.")
            st.dataframe(mapping_df.head(20), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
