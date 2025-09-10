"""
Simple script to start the VacayMate backend server
"""
import uvicorn
import sys
import os

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting VacayMate Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📍 API Documentation at: http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop the server")
    
    try:
        # Change to backend directory
        os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✅ Server stopped successfully!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure you have installed the requirements:")
        print("   pip install fastapi uvicorn pydantic python-multipart")
