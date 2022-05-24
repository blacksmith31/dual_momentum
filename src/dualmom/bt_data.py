import random
import csv
import utils.stock_tools as st

# file paths
# SYMBOLS_PATH = "sp500.csv"
SYMBOLS_PATH = "smcapchunk4.csv"

HISTORY_PATH = "/run/user/1000/gvfs/smb-share:server=nsadata.local,share=jameson/historical_data/stock/"

# cutoff value
TOP_N = 20

# emas = [21, 50, 100, 200]
# rocs = [21, 30, 60, 120]
# cutoffs = [0, 5, 10]
emas = [13, 21]
rocs = [90, 120, 150]
cutoffs = [0, 10]

symbols = st.read_stock_list(SYMBOLS_PATH)
'''
random.shuffle(symbols)
chunks = [symbols[x:x+98] for x in range(0, len(symbols), 98)]
# print(len(chunks))
# chunks = [chunks[0]]
for idx, chunk in enumerate(chunks):
    name = f"smcapchunk{idx}.csv"
    chunk = [[sym] for sym in chunk]
    with open(name, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(chunk)

'''
# for idx, symbols in enumerate(chunks[1]):
#     idx = 1
st.download_symbols_data(symbols, HISTORY_PATH, st.Client.PriceHistory.PeriodType.YEAR, st.Client.PriceHistory.Period.TWENTY_YEARS)
name = SYMBOLS_PATH.split('.')[0]

for ema in emas:
    for roc in rocs:
        st.apply_sroc_indicators(HISTORY_PATH, ema, roc, symbols)
        for  ind_cutoff in cutoffs:
            name_suffix = f"_{name}_{ema}-{roc}_cutoff_{ind_cutoff}.csv"
            print(f"Running for ema, roc, cutoff values: {name_suffix}")
            # rack_n_stack reads all the indicated csv files in the save path
            rack_df = st.rack_n_stack(HISTORY_PATH, "roc", include_symbs=symbols, suffix=name_suffix)

            rack_file = f"backtest_data/rack{name_suffix}"
            top_symbs = st.get_symb_selection_csv(rack_file, st.filter_vals_max_bt, top_n=TOP_N, ind_valuecutoff=ind_cutoff, suffix=name_suffix)

            top_file = f"backtest_data/symb_select_top{TOP_N}{name_suffix}"

            in_top = st.get_backtest_allocations(top_file, 5, ind_cutoff, name_suffix, symbols)


# plt.figure()
# df = pd.read_csv("test_racknstack_02.csv", index_col="Date")
# boxplot = df.boxplot(rot=90, grid=False, showfliers=False)
# plt.show()
