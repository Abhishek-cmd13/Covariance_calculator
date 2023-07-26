from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()

class TickerSymbols(BaseModel):
    symbols: list

class PortfolioInput(BaseModel):
    stocks: list
    new_stock: str

def calculate_mean_correlation_excluding(correlation_matrix, new_stock):
    correlation_matrix_excluding = correlation_matrix.drop(columns=new_stock, index=new_stock)
    return np.mean(correlation_matrix_excluding.values)

def calculate_mean_correlation_including(correlation_matrix, new_stock):
    correlation_matrix_including = correlation_matrix.drop(columns=new_stock, index=new_stock)
    new_stock_correlation = correlation_matrix[new_stock].drop(index=new_stock)
    correlation_matrix_including[new_stock] = new_stock_correlation
    correlation_matrix_including[new_stock][new_stock] = 1.0  # Set correlation with itself to 1.0
    return np.mean(correlation_matrix_including.values)

@app.post("/diversification")
def assess_diversification(portfolio_input: PortfolioInput):
    try:
        data = {}
        stocks = portfolio_input.stocks
        new_stock = portfolio_input.new_stock
        
        # Download historical price data for existing stocks in the portfolio
        for stock in stocks:
            stock_data = yf.download(stock)
            
            if stock_data.empty:
                raise HTTPException(status_code=404, detail=f"No data available for stock: {stock}")
            
            data[stock] = stock_data['Close']
        
        # Download historical price data for the new stock
        stock_data_new = yf.download(new_stock)
        if stock_data_new.empty:
            raise HTTPException(status_code=404, detail=f"No data available for stock: {new_stock}")
        data[new_stock] = stock_data_new['Close']
        
        df = pd.DataFrame(data)
        correlation_matrix = df.corr()
        
        mean_correlation_excluding_new_stock = calculate_mean_correlation_excluding(correlation_matrix, new_stock)
        mean_correlation_including_new_stock = calculate_mean_correlation_including(correlation_matrix, new_stock)
        
        if mean_correlation_including_new_stock < mean_correlation_excluding_new_stock:
            diversification_result = "Adding the new stock is diversifying the portfolio."
        else:
            diversification_result = "Adding the new stock is not diversifying the portfolio."
        
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "mean_correlation_excluding_new_stock": round(mean_correlation_excluding_new_stock, 2),
            "mean_correlation_including_new_stock": round(mean_correlation_including_new_stock, 2),
            "diversification_result": diversification_result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
