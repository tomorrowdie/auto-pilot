# import streamlit as st
#
# st.set_page_config(
#     page_title="My Portfolio",
#     page_icon="👨‍💻",
#     layout="wide"
# )
#
# # Update navigation dictionary to include the new pages
# navigation = {
#     "Info": ["About Me"],
#     "Projects": ["Doc Compare", "SEO Topic Cluster"],
#     "Tools": ["QR Generator", "Minesweeper"],
#     "Data Studio": ["Amazon Data Process H10", "Amazon Catalog Insight"]
# }
#
# # Create navigation in sidebar with sections
# st.sidebar.title("Navigation")
#
# # Initialize selected_page if not in session state
# if 'selected_page' not in st.session_state:
#     st.session_state.selected_page = "About Me"
#
# # Create sections in sidebar
# for section, pages in navigation.items():
#     st.sidebar.subheader(section)
#     for page in pages:
#         # All buttons will have the same style - a clean, consistent look
#         if st.sidebar.button(
#             page,
#             key=page,
#             use_container_width=True,
#             # Add 'primary' type to the selected button for highlighting
#             type="primary" if st.session_state.selected_page == page else "secondary"
#         ):
#             st.session_state.selected_page = page
#             st.rerun()  # Force rerun to update UI immediately
#
# # Page routing based on selection
# if st.session_state.selected_page == "About Me":
#     from views.about_me import show_page
#     show_page()
# elif st.session_state.selected_page == "Doc Compare":
#     from views.doc_compare import show_page
#     show_page()
# elif st.session_state.selected_page == "SEO Topic Cluster":
#     from views.seo_topic_cluster import show_page
#     show_page()
# elif st.session_state.selected_page == "QR Generator":
#     from views.qr_generator import show_page
#     show_page()
# elif st.session_state.selected_page == "Minesweeper":
#     from views.minesweeper import show_page
#     show_page()
# elif st.session_state.selected_page == "Amazon Data Process H10":
#     from views.amazon_data_process_h10 import show_page
#     show_page()
# elif st.session_state.selected_page == "Amazon Catalog Insight":
#     # Updated import to use the new filename
#     from views.amazon_catalog_insight_h10 import show_page
#     show_page()


# The navigation and import section remains the same
# Just make sure the SEO Topic Cluster option is in the navigation dictionary
# and the routing is properly set up

##################
#################VERSION 2#######################
#####################
# import streamlit as st
#
# st.set_page_config(
#     page_title="My Portfolio",
#     page_icon="👨‍💻",
#     layout="wide"
# )
#
# # Update navigation dictionary to include the new pages
# navigation = {
#     "Info": ["About Me"],
#     "Projects": ["Doc Compare", "SEO Topic Cluster"],  # SEO Topic Cluster is added here
#     "Tools": ["QR Generator", "Minesweeper"],
#     "Data Studio": ["Amazon Data Process H10", "Amazon Catalog Insight"]
# }
#
# # Create navigation in sidebar with sections
# st.sidebar.title("Navigation")
#
# # Initialize selected_page if not in session state
# if 'selected_page' not in st.session_state:
#     st.session_state.selected_page = "About Me"
#
# # Create sections in sidebar
# for section, pages in navigation.items():
#     st.sidebar.subheader(section)
#     for page in pages:
#         # All buttons will have the same style - a clean, consistent look
#         if st.sidebar.button(
#             page,
#             key=page,
#             use_container_width=True,
#             # Add 'primary' type to the selected button for highlighting
#             type="primary" if st.session_state.selected_page == page else "secondary"
#         ):
#             st.session_state.selected_page = page
#             st.rerun()  # Force rerun to update UI immediately
#
# # Page routing based on selection
# if st.session_state.selected_page == "About Me":
#     from views.about_me import show_page
#     show_page()
# elif st.session_state.selected_page == "Doc Compare":
#     from views.doc_compare import show_page
#     show_page()
# elif st.session_state.selected_page == "SEO Topic Cluster":
#     from views.seo_topic_cluster import show_page  # Import the new view
#     show_page()
# elif st.session_state.selected_page == "QR Generator":
#     from views.qr_generator import show_page
#     show_page()
# elif st.session_state.selected_page == "Minesweeper":
#     from views.minesweeper import show_page
#     show_page()
# elif st.session_state.selected_page == "Amazon Data Process H10":
#     from views.amazon_data_process_h10 import show_page
#     show_page()
# elif st.session_state.selected_page == "Amazon Catalog Insight":
#     # Updated import to use the new filename
#     from views.amazon_catalog_insight_h10 import show_page
#     show_page()



import streamlit as st

st.set_page_config(
    page_title="My Portfolio",
    page_icon="👨‍💻",
    layout="wide"
)

# Updated navigation dictionary - removed problematic pages
navigation = {
    "Info": ["About Me"],
    "Projects": [],  # Removed Doc Compare, SEO Topic Cluster, RAG Chatbot
    "Tools": ["QR Generator", "AI Oracle"],  # Removed Minesweeper
    "Data Studio": ["Amazon Data Process H10", "Amazon Catalog Insight"]
}

# Global API Key setup - Load from secrets only
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY", None)
    if api_key:
        st.session_state['global_deepseek_key'] = api_key
except Exception:
    # If secrets are not available, set to None
    st.session_state['global_deepseek_key'] = None

# Create navigation in sidebar with sections
st.sidebar.title("Navigation")

# Initialize selected_page if not in session state
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "About Me"

# Create sections in sidebar
for section, pages in navigation.items():
    st.sidebar.subheader(section)
    for page in pages:
        # All buttons will have the same style - a clean, consistent look
        if st.sidebar.button(
            page,
            key=page,
            use_container_width=True,
            # Add 'primary' type to the selected button for highlighting
            type="primary" if st.session_state.selected_page == page else "secondary"
        ):
            st.session_state.selected_page = page
            st.rerun()  # Force rerun to update UI immediately

# Page routing based on selection
if st.session_state.selected_page == "About Me":
    from views.about_me import show_page
    show_page()
# elif st.session_state.selected_page == "Doc Compare":
#     from views.doc_compare import show_page
#     show_page()
# elif st.session_state.selected_page == "SEO Topic Cluster":
#     from views.seo_topic_cluster import show_page
#     show_page()
# elif st.session_state.selected_page == "RAG Chatbot":  # New routing for RAG Chatbot
#     from views.rag_chatbot import show_page
#     show_page()
elif st.session_state.selected_page == "QR Generator":
    from views.qr_generator import show_page
    show_page()
# elif st.session_state.selected_page == "Minesweeper":
#     from views.minesweeper import show_page
#     show_page()
elif st.session_state.selected_page == "Amazon Data Process H10":
    from views.amazon_data_process_h10 import show_page
    show_page()
elif st.session_state.selected_page == "Amazon Catalog Insight":
    from views.amazon_catalog_insight_h10 import show_page
    show_page()
elif st.session_state.selected_page == "AI Oracle":
    from views.ai_oracle import show_page
    show_page()