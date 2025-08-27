#!/usr/bin/env python3
"""
Quick Production Test - Start server and check for immediate errors
"""
import subprocess
import sys
import time
import os

def test_streamlit_startup():
    """Test Streamlit server startup for immediate errors"""
    print("🚀 Testing Streamlit server startup...")
    
    # Set production-like environment
    env = os.environ.copy()
    env.update({
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_ENABLE_CORS': 'false',
        'STREAMLIT_LOGGER_LEVEL': 'info'
    })
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port=8503',
        '--server.address=127.0.0.1', 
        '--server.headless=true',
        '--server.enableCORS=false'
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env
        )
        
        print("⏳ Monitoring server startup (15 seconds)...")
        
        # Monitor output for 15 seconds
        start_time = time.time()
        output_lines = []
        
        while time.time() - start_time < 15:
            # Check if process terminated
            if process.poll() is not None:
                remaining_output = process.stdout.read()
                if remaining_output:
                    output_lines.extend(remaining_output.split('\n'))
                break
                
            # Read available output
            try:
                import select
                if select.select([process.stdout], [], [], 0.1)[0]:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(line.strip())
                        print(f"📝 {line.strip()}")
                        
                        # Check for success
                        if "You can now view your Streamlit app" in line:
                            print("✅ Server started successfully!")
                            break
                            
            except ImportError:
                # Windows compatibility
                time.sleep(0.1)
                
        # Analyze output for errors
        error_found = False
        critical_errors = [
            "StreamlitAPIException", 
            "selection() is not a valid",
            "AttributeError",
            "ImportError",
            "ModuleNotFoundError",
            "SyntaxError",
            "NameError",
            "TypeError",
            "ValueError", 
            "KeyError",
            "Exception"
        ]
        
        for line in output_lines:
            for error_pattern in critical_errors:
                if error_pattern in line and "Traceback" not in line:
                    print(f"❌ Found potential error: {line}")
                    error_found = True
                    
        if not error_found:
            print("✅ No critical errors detected in server startup!")
        else:
            print("⚠️ Potential errors found - check output above")
            
        # Stop server
        try:
            process.terminate()
            process.wait(timeout=5)
            print("🛑 Server stopped")
        except:
            process.kill()
            
        return not error_found
        
    except Exception as e:
        print(f"❌ Failed to test server: {e}")
        return False

if __name__ == "__main__":
    success = test_streamlit_startup()
    print("=" * 50)
    if success:
        print("🎉 Production test PASSED! Application is ready for deployment.")
    else:
        print("❌ Production test FAILED! Check errors above.")
    sys.exit(0 if success else 1)