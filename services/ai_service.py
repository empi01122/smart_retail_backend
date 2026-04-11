import os
from google import genai

def generate_dashboard_insights(summary_data: dict, top_products: list) -> str:
    """
    Takes raw dashboard metrics from the database and uses the Gemini AI
    to generate a plain-text/markdown summary for the store owner.
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "":
        return "⚠️ **AI Insights Unavailable:** Please add your `GEMINI_API_KEY` to the `.env` file to enable smart insights."
        
    # Initialize the new Google GenAI client
    client = genai.Client(api_key=api_key)
    
    # Construct the data context payload
    data_context = f"""
    ### Current Store Data
    - Total Sales Count: {summary_data.get('total_sales', 0)}
    - Total Revenue Generated: {summary_data.get('total_revenue', 0)} FCFA
    - Total Unique Products in Store: {summary_data.get('total_products', 0)}
    - Items with Low Stock (<= 5 units): {summary_data.get('low_stock_alerts', 0)}

    ### Top Selling Products
    {chr(10).join([f"- {p['product']}: {p['units_sold']} units sold (Revenue: {p['revenue']} FCFA)" for p in top_products]) if top_products else "- No sales yet."}
    """

    # Tell the AI how to behave and what to output
    system_instruction = """
    You are a smart retail analytics assistant for a store dashboard. 
    Analyze the provided data and write a short, friendly, and highly insightful summary of the store's performance.

    Format your output strictly with these sections (include the emojis):
    📊 Sales Summary: <A fast summary of their overall performance based on sales count and revenue>
    💡 Restock Recommendations: <Alert them if they have low stock items. Suggest what to restock>
    🔮 Demand Predictions: <Predict general retail trends or provide an encouraging tip if data is low>
    
    Keep the whole response under 150 words. Do not make up fake data. Speak directly to the store manager.
    """

    try:
        # Call the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_instruction}\n\nHere is the data:\n{data_context}"
        )
        return response.text
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return "⚠️ **AI Insights Error:** Unfortunately, there was a problem connecting to the AI brain right now."
