import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# --- Configuration ---
st.set_page_config(page_title="N-Gram Frequency Search", layout="wide")

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads the Excel data and caches it."""
    # Using the existing file in the directory
    file_path = 'ngram_results_dual_stream_final.xlsx'
    try:
        df = pd.read_excel(file_path)
        # Ensure 'phrase' column exists and is string
        if 'phrase' in df.columns:
            df['phrase'] = df['phrase'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

# --- App UI ---
st.title("N-Gram Frequency Search")
st.markdown("""
This application allows you to search for phrases within the dataset, even with typos. 
It displays frequency counts across different sources (Video, MEB, Tübitak, Saha, Yazın) and highlights where each phrase appears.
Type in the box below to search for a phrase!
""")

if df is not None:
    # --- Sidebar Filters (Optional) ---
    with st.sidebar:
        st.header("Settings")
        limit = st.slider("Max Results", min_value=5, max_value=50, value=10)
        score_cutoff = st.slider("Min Match Score", min_value=0, max_value=100, value=50)

    # --- Search Input ---
    query = st.text_input("Search Phrase:", placeholder="Type a phrase here... (e.g., 'eğitim', 'mücadele')")

    # --- Fuzzy Logic ---
    if query:
        # Get list of phrases
        phrases = df['phrase'].tolist()
        
        # Perform fuzzy search
        # process.extract returns list of tuples: (match, score, index)
        results = process.extract(
            query, 
            phrases, 
            scorer=fuzz.WRatio, 
            limit=limit,
            score_cutoff=score_cutoff
        )
        
        # Prepare results for display
        matched_indices = [idx for (match, score, idx) in results]
        matched_scores = [score for (match, score, idx) in results]
        
        if matched_indices:
            # Filter original dataframe
            filtered_df = df.iloc[matched_indices].copy()
            filtered_df['match_score'] = matched_scores
            
            # Reorder columns to show match_score first
            cols = ['match_score'] + [c for c in filtered_df.columns if c != 'match_score']
            filtered_df = filtered_df[cols]

            st.success(f"Found {len(filtered_df)} distinct matches.")
            
            # 1. Dropdown Selection of Results
            selected_phrase = st.selectbox(
                "Select a matching phrase to view details:",
                options=filtered_df['phrase'].tolist()
            )
            
            # 2. Detailed View of Selected
            if selected_phrase:
                st.subheader("Selected Phrase Details")
                details = filtered_df[filtered_df['phrase'] == selected_phrase].iloc[0]
                st.json(details.to_dict())

            # 3. Table View of All Matches
            st.subheader("All Matches Table")
            st.dataframe(filtered_df.style.background_gradient(subset=['match_score'], cmap="Greens"), use_container_width=True)
            
        else:
            st.warning("No matches found. Try adjusting the score cutoff or search term.")
            
    else:
        st.info("Enter a search term to begin.")
        st.subheader("Dataset Preview (Top 40 sorted by Total Count)")
        # Sort by total_count if available, else just head
        if 'total_count' in df.columns:
            st.dataframe(df.sort_values(by='total_count', ascending=False).head(40), use_container_width=True)
        else:
            st.dataframe(df.head(40), use_container_width=True)

else:
    st.warning("Data could not be loaded. Please ensure 'ngram_results_dual_stream.xlsx' is in the same directory.")
