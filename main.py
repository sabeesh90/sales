import streamlit as st
import pandas as pd
import plotly.express as px
import utils

# --- Page Config ---
st.set_page_config(page_title="KPI 3 - Trixeo Santis Dashboard", layout="wide")

# --- Top Centered Title and Subtitle ---
st.markdown(
    """
    <div style="text-align: center;">
        <h1 style="font-size: 50px;">KPI 3 : 📊 Trixeo Santis Dashboard</h1>
        <h4 style="color: gray; margin-top: -10px;">Sales and Usage Analysis Dashboard</h4>
    </div>
    """,
    unsafe_allow_html=True
)

# --- -------------------------------------------------------------------------------------------Sidebar Settings--------------------------------------------------------------------------------------------------------------- ---

# --- Sidebar Settings ---


with st.sidebar.expander("Brand Settings", expanded=True):

    # Selction of brands
    brand = st.selectbox("Brand Type", options=['trixeo', 'forxiga'])

    # Selection of levels
    level = st.selectbox("Brand Type", options=['mini_brick','brick'])
    
    # Selection of business unit
    sales_line = st.selectbox("Brand Type", options=['AZ', 'Santis'])
    
    # seocnd level degfinitions for sales and suggestions repsectively
    if level == 'mini_brick':
        usage_level = 'mini_brick_code'
        sales_level = 'mini_brick'
    elif level == 'brick':
        usage_level = 'brick'
        sales_level = 'brick'

    if sales_line == 'AZ':
        business_unit = 'AZ_RESPI_INH'
        sales_business_unit = 'AZ_RESPI_INH'

    elif sales_line == 'Santis':
        business_unit = 'SAN_MIX'
        sales_business_unit = 'SAN_MIX'
    
    if brand == 'trixeo':
        product_name = 'TRIXEO + IMP.'
    elif brand == 'forxiga':
        product_name = 'FORXIGA + IMP.'



    
# General Settings
with st.sidebar.expander("⚙️ Usage Settings", expanded=False):
    # Quantiles
    quantile_low = st.slider("Low quantile", 0.0, 1.0, 0.20, 0.05)
    quantile_high = st.slider("High quantile", 0.0, 1.0, 0.80, 0.05)
    quantiles = [quantile_low, quantile_high]

    # Usage Threshold
    usage_threshold = st.number_input("Usage Threshold", min_value=0, max_value=100, value=0)

     # Usage Threshold
    reg_threshold = st.number_input("reg Threshold", min_value=0, max_value=100, value=3)

    # Content Type
    content_type = st.selectbox("Content Type", options=[None, 'VAE', 'iDetail'])

    n = st.number_input("Top N", min_value=0, max_value=100, value=10)

# ---------------------------------------------
# --- NEW Sales Analysis Settings Section ---
# ---------------------------------------------
with st.sidebar.expander("📈 Sales Analysis Settings", expanded=False):

    # Recommendation Date
    rec_date = st.date_input("Recommendation Date", value=pd.to_datetime('2024-06-01')).strftime('%d-%b-%Y')

    # Moving Average Window
    window = st.slider("Moving Average Window (months)", min_value=1, max_value=12, value=3)


# --- -------------------------------------------------------------------------------------------Data loading section --------------------------------------------------------------------------------------------------------------- ---
# --- Load usage Data ---

@st.cache_data(ttl=60*60, show_spinner=False)
def load_data(loc):
    return pd.read_parquet(loc,use_threads=True)


print('before loading')

with st.spinner(f"Loading {brand} Sales data, please wait…",show_time=True):
    sales = load_data(f'https://storage.googleapis.com/sales_az/{brand}_sales.parquet')
    print('Sales loaded')
    print(sales.shape)

with st.spinner(f"Loading {brand} Suggestions data, please wait…", show_time=True):
    suggestions = load_data(f'https://storage.googleapis.com/sales_az/{brand}_suggestions.parquet')
    print('suggestions loaded')
    print(suggestions.shape)

r,top_group_month_wise, bottom_group_month_wise, fig_usage= utils.generate_usage(suggestions,sales_business_unit,quantiles=quantiles,usage_threshold=usage_threshold,content_type=content_type,usage_level=usage_level)

# --- Load Sales Data ---
sales_grouped_average_low, sales_grouped_average_high, \
sales_grouped_average_low_graph,sales_grouped_average_high_graph, \
sales_grouped_average,sales_grouped = utils.generate_sales(r, usage_level, sales, business_unit, product_name, 
                                             rec_date, sales_level = sales_level, window = window)


fig_avg, fig_roll = utils.generate_sales_graphs(sales_grouped_average_low, sales_grouped_average_high, sales_grouped_average_low_graph, sales_grouped_average_high_graph, window = window,rec_date=rec_date,)

# 1) Compute the true mins & maxes
true_min_avg = min(
    sales_grouped_average_low['average_sales_across_levels'].min(),
    sales_grouped_average_high['average_sales_across_levels'].min()
)
true_max_avg = max(
    sales_grouped_average_low['average_sales_across_levels'].max(),
    sales_grouped_average_high['average_sales_across_levels'].max()
)

true_min_roll = min(
    sales_grouped_average_low_graph['rolling_mean'].min(),
    sales_grouped_average_high_graph['rolling_mean'].min()
)
true_max_roll = max(
    sales_grouped_average_low_graph['rolling_mean'].max(),
    sales_grouped_average_high_graph['rolling_mean'].max()
)

# 2) Define a buffer: e.g. 10% of the span
buffer_pct = 0.25
buffer_pct_normal = 0.10
avg_span = true_max_avg - true_min_avg
roll_span = true_max_roll - true_min_roll

avg_buffer = avg_span * buffer_pct
roll_buffer = roll_span * buffer_pct


avg_buffer_normal = avg_span * buffer_pct_normal
roll_buffer_normal = roll_span * buffer_pct_normal


# 3) Build your sliders with padded bounds
min_avg, max_avg = st.sidebar.slider(
    "Average Sales Y-axis range",
    float(true_min_avg - avg_buffer),        # pad below
    float(true_max_avg + avg_buffer),        # pad above
    (float(true_min_avg - avg_buffer_normal), float(true_max_avg + avg_buffer_normal)),  # defaults sit exactly on data
    step=1.0
)
min_roll, max_roll = st.sidebar.slider(
    "Rolling Mean Y-axis range",
    float(true_min_roll - roll_buffer),
    float(true_max_roll + roll_buffer),
    (float(true_min_roll-roll_buffer_normal), float(true_max_roll+roll_buffer_normal)),
    step=1.0
)

# 4) Apply to your figures
fig_avg.update_yaxes(range=[min_avg, max_avg])
fig_roll.update_yaxes(range=[min_roll, max_roll])


diff, history, forecast, viz, diff_fig = utils.project_difference_in_rolling_mean(
    sales_grouped_average_low_graph,
    sales_grouped_average_high_graph,
    reg_threshold=reg_threshold
)

# --------------------------------------------------------------------------------------------- Dashboard Layout -------------------------------------------------------------------------------------------------------------------------------

utils.card_container("Gross Statistics")
# st.title("📊 Trixeo Santis Dashboard")
with st.container():
    cola,_, colb = st.columns([1, 0.05, 1])  # Space between columns
    
    with cola:
        st.metric(label=f"Total Number of {usage_level}",value=r[usage_level].nunique())
        st.metric(label=f"Number of {usage_level} Above {quantile_high*100}% Quantile",value=r[r['quantile']==f'Above {quantile_high}'].shape[0])
        st.metric(label=f"Number of {usage_level} Below {quantile_low*100}% Quantile",value=r[r['quantile']==f'Below {quantile_low}'].shape[0])
        st.metric(label=f"Number of {usage_level} with zero usage",value=r[r.usage_rate==0][usage_level].nunique())
    
    with colb:
        st.metric(label=f"Sales Duration",value=f"{sales_grouped_average['sales_month'].min().strftime('%d %b %Y')} to {sales_grouped_average['sales_month'].max().strftime('%d %b %Y')} ")
        st.metric(label=f"Recommendation date",value=f"{rec_date}")
        st.metric(label=f"Highest Usage Rate",value=r.usage_rate.max())
        st.metric(label=f"Lowest Usage Rate",value=r.usage_rate.min())


        # st.metric(label=f"Number of {usage_level} Above {quantile_high*100}% Quantile",value=r[r['quantile']==f'Above {quantile_high}'].shape[0])
        # st.metric(label=f"Number of {usage_level} Below {quantile_low*100}% Quantile",value=r[r['quantile']==f'Below {quantile_low}'].shape[0])
        # st.metric(label=f"Number of {usage_level} with zero usage",value=r[r.usage_rate==0][usage_level].nunique())

        
utils.blue_full_width_card("Usage Section", height_px = 50)

# Row 1
with st.container():
    col2, _, col3 = st.columns([2, 0.05, 1])  # Space between columns

    with col2:
        utils.card_container("📦 Usage Rate Analysis")
        st.dataframe(r, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        utils.card_container("💵 Distribution of Usage Rate")
        st.plotly_chart(fig_usage, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col7, _, col8 = st.columns([1, 0.05, 1])  # Space between columns
    with col7:
        utils.card_container(f"📦 High Usage above {quantile_high*100}th percentile ")
        st.dataframe(top_group_month_wise, use_container_width=True)
        st.write(f"Total Number of {usage_level} in High Usage: {top_group_month_wise[usage_level].nunique()}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col8:
        utils.card_container(f"📦 High Usage Below {quantile_low*100}th percentile ")
        st.dataframe(bottom_group_month_wise, use_container_width=True)
        st.write(f"Total Number of {usage_level} in Low Usage: {bottom_group_month_wise[usage_level].nunique()}")
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    colx, = st.columns([2])

    with colx:
        utils.card_container(f"📦 Top {n} Bricks")
        top_group_filtered, top_group_fig = utils.generate_top_n_usage(n,top_group_month_wise, usage_level)
        st.plotly_chart(top_group_fig, use_container_width=True)
        st.dataframe(top_group_filtered, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)





# Divider
st.divider()
utils.blue_full_width_card("Sales Section", height_px = 50)

# Row 2 (future expansion)
with st.container():
    col4,= st.columns([2])  # Space between columns

    with col4:
        utils.card_container(f"📦 Average Sales Across {sales_level}")
        st.plotly_chart(fig_avg, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col5,= st.columns([2])  # Space between columns

    with col5:
        utils.card_container(f"📦 Rolling Average Sales Across {sales_level} - {window} month window")
        st.plotly_chart(fig_roll, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Divider
st.divider()

# Row 2 (future expansion)
with st.container():
    col6, _, col7 = st.columns([1, 0.05, 1])  # Space between columns
    with col6:
        utils.card_container("📦 Low usage Sales")
        st.dataframe(sales_grouped_average_low, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col7:
        utils.card_container("📦 High Usage Sales")
        st.dataframe(sales_grouped_average_high, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col10,= st.columns([2])  # Space between columns

    with col10:
        utils.card_container("📦 Difference in rolling means between the two groups")
        # st.plotly_chart(diff_fig, use_container_width=True)
        st.dataframe(diff, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col11, _, col12 = st.columns([1, 0.05, 1])  # Space between columns

    with col11:
        utils.card_container("📦 History")
        st.dataframe(history)   # history used to fit
        st.markdown("</div>", unsafe_allow_html=True)
    with col12:
        utils.card_container("📦 Forecast")
        st.dataframe(forecast)   # history used to fit
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col9,= st.columns([2])  # Space between columns

    with col9:
        utils.card_container("📦 Sales per brick month wise")
        st.plotly_chart(diff_fig, use_container_width=True)
        # st.dataframe(sales_grouped, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    col8,= st.columns([2])  # Space between columns

    with col8:
        utils.card_container("📦 Sales per brick month wise")
        st.dataframe(sales_grouped, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)





# Footer
st.caption("Built with ❤️ by Sabeesh | Powered by Streamlit")
