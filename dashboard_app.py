    elif view == "⚡ 8. Full Zerodha Confluence Breakout Hunter (RSI 69-80+ Zone)":
        st.subheader("⚡ Breakout Hunter: Active Weekly RSI (69 - 80+) Leaders")
        st.markdown("""
        ### 🎯 Active Filtering & Ranking:
        * **RSI Band**: Strictly isolates stocks with Weekly RSI between **69 and 80+** (the explosive momentum zone).
        * **Custom Ranking Weights**: **RSI (40%)**, **Price ROC (30%)**, **Short-Term Return (20%)**, **MFI (10%)**.
        """)
        
        if not scanned_df.empty:
            # Strictly filter for RSI between 69 and 95 (capturing 69-80+)
            zone_filtered = scanned_df[(scanned_df['RSI (14)'] >= 69.0) & (scanned_df['RSI (14)'] <= 95.0)].copy()
            
            if not zone_filtered.empty:
                final_ranked_zone = rank_and_select_top_25(zone_filtered)
                st.success(f"Successfully isolated **{len(zone_filtered)}** stocks in the RSI 69–80+ zone. Displaying top-ranked leaders:")
                
                display_cols = ['Ticker', 'Current Price', 'RSI (14)', 'Price ROC (18)', 'MFI (14)', '1M Return (%)', 'Composite_Score']
                st.dataframe(final_ranked_zone[[c for c in display_cols if c in final_ranked_zone.columns]], use_container_width=True)
            else:
                st.warning("No stocks currently match the 69-80+ RSI window in the active scan batch. Adjust the range or expand the watchlist.")
