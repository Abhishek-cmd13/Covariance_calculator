from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd

app = FastAPI()

class TickerSymbols(BaseModel):
    symbols: list

@app.post("/correlation")
def calculate_correlation(ticker_symbols: TickerSymbols):
    try:
        data = {}
        
        for symbol in ticker_symbols.symbols:
            stock_data = yf.download(symbol)
            
            if stock_data.empty:
                raise HTTPException(status_code=404, detail=f"No data available for symbol: {symbol}")
            
            data[symbol] = stock_data['Close']
        
        df = pd.DataFrame(data)
        correlation_matrix = df.corr()
        
        return {"correlation_matrix": correlation_matrix.to_dict()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
