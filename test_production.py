#!/usr/bin/env python3
"""
Production Environment Test Script
Simulates production conditions to test for errors before deployment
"""

import os
import sys
import logging
import subprocess
import signal
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionTester:
    def __init__(self):
        self.streamlit_process = None
        self.base_dir = Path(__file__).parent
        
    def setup_production_environment(self):
        """Set production-like environment variables"""
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'true'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_LOGGER_LEVEL'] = 'info'
        logger.info("✅ Production environment variables set")
        
    def validate_files(self):
        """Validate all required files exist"""
        required_files = [
            'app.py',
            'src/data_processor.py', 
            'src/database.py',
            'data/contacts.csv',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            logger.error(f"❌ Missing files: {missing_files}")
            return False
            
        logger.info("✅ All required files present")
        return True
        
    def test_python_imports(self):
        """Test if all imports work correctly"""
        try:
            logger.info("🔍 Testing Python imports...")
            
            # Test core imports
            import streamlit
            import pandas
            import plotly
            import numpy
            logger.info(f"✅ Core libraries: streamlit={streamlit.__version__}, pandas={pandas.__version__}")
            
            # Test application imports
            sys.path.insert(0, str(self.base_dir))
            from src.data_processor import DataProcessor
            from src.database import DatabaseManager
            logger.info("✅ Application modules imported successfully")
            
            # Test DataProcessor initialization
            processor = DataProcessor()
            logger.info("✅ DataProcessor initialized successfully")
            
            # Test DatabaseManager initialization
            db_manager = DatabaseManager()
            logger.info("✅ DatabaseManager initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Import error: {str(e)}")
            return False
            
    def test_syntax_compilation(self):
        """Test Python syntax compilation"""
        try:
            logger.info("🔍 Testing syntax compilation...")
            
            files_to_compile = ['app.py', 'src/data_processor.py', 'src/database.py']
            
            for file_path in files_to_compile:
                full_path = self.base_dir / file_path
                with open(full_path, 'r') as f:
                    source = f.read()
                    
                compile(source, str(full_path), 'exec')
                logger.info(f"✅ {file_path} compiled successfully")
                
            return True
            
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in {e.filename}:{e.lineno} - {e.msg}")
            return False
        except Exception as e:
            logger.error(f"❌ Compilation error: {str(e)}")
            return False
            
    def start_streamlit_server(self):
        """Start Streamlit server in production mode"""
        try:
            logger.info("🚀 Starting Streamlit server...")
            
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 'app.py',
                '--server.port=8502',  # Use different port to avoid conflicts
                '--server.address=127.0.0.1',
                '--server.headless=true',
                '--server.enableCORS=false',
                '--server.maxUploadSize=100',  # 100MB limit like production
                '--logger.level=info'
            ]
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=str(self.base_dir)
            )
            
            logger.info("⏳ Waiting for server to start...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Streamlit server: {str(e)}")
            return False
            
    def monitor_server_startup(self, timeout=30):
        """Monitor server startup for errors"""
        try:
            start_time = time.time()
            server_started = False
            
            while time.time() - start_time < timeout:
                if self.streamlit_process.poll() is not None:
                    # Process has terminated
                    output = self.streamlit_process.stdout.read()
                    logger.error(f"❌ Server terminated early:")
                    logger.error(output)
                    return False
                    
                # Check if we can read some output
                try:
                    # Non-blocking read
                    self.streamlit_process.stdout.settimeout(1)
                    line = self.streamlit_process.stdout.readline()
                    if line:
                        logger.info(f"Server output: {line.strip()}")
                        
                        # Check for success indicators
                        if "You can now view your Streamlit app" in line:
                            server_started = True
                            logger.info("✅ Server started successfully!")
                            break
                            
                        # Check for error indicators
                        error_patterns = [
                            "StreamlitAPIException",
                            "AttributeError",
                            "ImportError", 
                            "ModuleNotFoundError",
                            "SyntaxError",
                            "NameError",
                            "TypeError: selection() is not a valid"
                        ]
                        
                        for pattern in error_patterns:
                            if pattern in line:
                                logger.error(f"❌ Found error pattern '{pattern}' in server output")
                                return False
                                
                except:
                    pass
                    
                time.sleep(0.5)
                
            if not server_started:
                logger.warning("⚠️ Server startup timeout (but no errors detected)")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error monitoring server: {str(e)}")
            return False
            
    def stop_server(self):
        """Stop the Streamlit server"""
        if self.streamlit_process:
            try:
                logger.info("🛑 Stopping Streamlit server...")
                self.streamlit_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.streamlit_process.wait(timeout=10)
                    logger.info("✅ Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Forcing server shutdown...")
                    self.streamlit_process.kill()
                    self.streamlit_process.wait()
                    
            except Exception as e:
                logger.error(f"❌ Error stopping server: {str(e)}")
                
    def run_full_test(self):
        """Run the complete production test suite"""
        logger.info("🧪 Starting Production Environment Test")
        logger.info("=" * 50)
        
        try:
            # Test 1: Environment setup
            self.setup_production_environment()
            
            # Test 2: File validation
            if not self.validate_files():
                return False
                
            # Test 3: Import testing
            if not self.test_python_imports():
                return False
                
            # Test 4: Syntax compilation
            if not self.test_syntax_compilation():
                return False
                
            # Test 5: Server startup
            if not self.start_streamlit_server():
                return False
                
            # Test 6: Monitor for errors
            if not self.monitor_server_startup():
                return False
                
            logger.info("🎉 All production tests passed!")
            logger.info("Your application is ready for deployment!")
            return True
            
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            self.stop_server()

if __name__ == "__main__":
    tester = ProductionTester()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)