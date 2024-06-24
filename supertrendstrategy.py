from _datetime import datetime as dt, timedelta
import time as t
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

#############################################################################################################################################################################


# Supertrend Calculator Function
def supertrend(df, atr_period, atr_multiplier):

    high = df['High']
    low = df['Low']
    close = df['Close']

    # calculate ATR
    price_diffs = [high - low,
                   high - close.shift(),
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (atr_multiplier * atr)
    final_lowerband = lowerband = hl2 - (atr_multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i-1

        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]

            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan


    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)

#####################################################################################################################################################################################################################333

#stremlit app necessary parameters
st.title('Stock Market Analysis')
with st.sidebar.popover("Ticker"):
    tick = st.text_input("Ticker Symbol")
    ticker = st.radio("", ["^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "NIFTY_MID_SELECT.NS", "btc-usd", "eth-usd"])
Fr = st.sidebar.date_input('From')
To = st.sidebar.date_input('To')
t1 = st.sidebar.time_input('Start time', value=None)
t2 = st.sidebar.time_input('End time', value=None)
atr_multiplier = 1
atr_multiplier2 = 2
timeframe = st.sidebar.text_input('Timeframe(5m)', '5m')

################################################################################################################################################

#ticker Stock data
From = dt(Fr.year, Fr.month, Fr.day, t1.hour, t1.minute)
From -= timedelta(hours=19,minutes=30)
End = dt(To.year, To.month, To.day, t2.hour, t2.minute)
if tick == '':
    tickname = yf.Ticker(ticker)
else:
    tickname = yf.Ticker(tick)
df = tickname.history(start=From, end=End, interval=timeframe)

################################################################################################################################################################################################################################
start = t.time()
del df["Dividends"]
del df["Stock Splits"]
df2 = df.copy()
atr_period = 10

#supertrend calculator
supertrend = supertrend(df, atr_period, 1)
df = df.join(supertrend)
df.to_csv("first Supertrend.csv")
selected = st.checkbox("View Data")
if selected:
    st.table(df)

#ploting the candles
checkboxs = st.checkbox("Show Chart")
if checkboxs:
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                close=df['Close'],
                high=df['High'],
                low=df['Low']),
            go.Line(x=df.index, y=df['Final Upperband']),
            go.Line(x=df.index, y=df['Final Lowerband'])])
    st.plotly_chart(fig)

#############################################################################################################################################################################

# signal generation
d = pd.read_csv("first Supertrend.csv")
df = pd.DataFrame(d)
pnl = 0
df['Final Lowerband'] = df['Final Lowerband'].fillna(0)
df['Final Upperband'] = df['Final Upperband'].fillna(0)
df['super'] = df['Final Upperband'] + df['Final Lowerband']
df['super'].astype(float)
del df['Supertrend']
df['Supertrend'] = df['Close'] - df['super']
df['Signal'] = ''
trade = 0
s = 0

# logic of signal generation
for i in range(9,len(df)):
    if df.iloc[i,9] > 0:
        if s == 0:
            df.iloc[i-1,10] = 1
            s = 1
        else:
            continue
    if df.iloc[i,9] < 0:
        if s == 1:
            df.iloc[i-1,10] = -1
            s = 0
        else:
            continue

# separating signal generated dataframe
sd = []
dx = pd.DataFrame(sd)
k=0
copyrow = 1
for i in range(1, len(df)):
    if df['Signal'][i] == 1 or df['Signal'][i] == -1:
        copyrow = df.loc[i]
        dx = pd.concat([dx, copyrow.to_frame().T], ignore_index=True)

######################################################################################################################################################################################

# Calculating gain and loss for each pair of signal
a=0
prof = []
for i in range(0,len(dx)-1):
    if a == 0:
        gain = dx['Close'][i+1] - dx['Close'][i]
        prof.append(gain)
        a += 1
        trade+=1
        continue
    if a == 1:
        los = dx['Close'][i] - dx['Close'][i+1]
        prof.append(los)
        a -= 1
        trade+=1
    if i == len(dx)-2:
        break

# Calculating the P&L for each pair of signal
profit, win = 0, 0
loss, lose = 0, 0
for i in range(len(prof)):
    pnl += prof[i]
    if prof[i] > 0:
        profit += prof[i]
        win += 1
    else:
        loss += prof[i]
        lose += 1
dx.to_csv("signal.csv")

###################################################################################################################################################################

# Displaying the Results in the APP
win_percent = (win/trade)*100
st.write(prof)
box = st.checkbox("Trades List")
if box :
    st.table(dx)
st.write("PnL : ", pnl)
st.write("profit : ", profit)
st.write("loss : ", loss)
st.write("trade Executed : ", trade)
st.write("win : ", win, ",    Winning Percentage : ", win_percent)
st.write("lose : ", lose)
df.to_csv("buy and sell.csv")
end = t.time()
st.write("Time to Execute" , end-start)
st.stop()