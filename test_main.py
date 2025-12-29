import asyncio
import httpx

BASE_URL = "http://localhost:8000" 

async def send_request(client, url, i):
    payload = {"url": url}
    response = await client.post(f"{BASE_URL}/analyze_img", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Zlecono"
    assert data["url"] == url
    
    print(f"Request {i+1}/100: OK - {url}")

async def test_100_requests_burst():
    """Test wysyłający 100 requestów równocześnie do /analyze_img (POST) z przykładowymi URL."""
    test_urls = [
        "https://static1.squarespace.com/static/656f4e4dababbd7c042c4946/657236350931ee4538eea52c/65baf15103d8ad2826032a8a/1743469050421/how-to-stop-being-a-people-pleaser-1_1.jpg?format=1500w",
        "https://img.freepik.com/free-photo/people-posing-together-registration-day_23-2149096793.jpg?semt=ais_hybrid&w=740&q=80",
        "https://elements-resized.envatousercontent.com/envato-dam-assets-production/EVA/TRX/01/1f/e6/44/b1/v1_E10/E102BHYV.jpg?w=500&cf_fit=scale-down&mark-alpha=18&mark=https%3A%2F%2Felements-assets.envato.com%2Fstatic%2Fwatermark4.png&q=85&format=auto&s=315bef5dfe9efe9bc22b1aeab148440c3b845f358d307881392adb7582596130",
        "https://images.rawpixel.com/image_png_800/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvczIxLXMyOS1zMzItczM0LXM1Mi10b25nLWt6OWozeWRwLnBuZw.png",
    ]
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(100):
            url = test_urls[i % len(test_urls)] 
            tasks.append(send_request(client, url, i))
        

        await asyncio.gather(*tasks)
    
    print("Wszystkie 100 requestów wysłane równocześnie i pomyślnie!")

if __name__ == "__main__":
    asyncio.run(test_100_requests_burst())